# ClusterBalancer Demo - Overload Scenario Script
# This script creates an overload scenario and monitors cluster rebalancing

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "ClusterBalancer - Overload Demo" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check cluster state
Write-Host "[Step 1] Checking current cluster state..." -ForegroundColor Yellow
Write-Host "Nodes in cluster:" -ForegroundColor White
kubectl get nodes

Write-Host ""
Write-Host "Current node resource usage:" -ForegroundColor White
kubectl top nodes

Write-Host ""
Write-Host "Current pods:" -ForegroundColor White
kubectl get pods -o wide --all-namespaces

# Step 2: Create heavy workload
Write-Host ""
Write-Host "[Step 2] Creating heavy CPU workload..." -ForegroundColor Yellow

$workloadYaml = @"
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cpu-heavy
  namespace: default
spec:
  replicas: 4
  selector:
    matchLabels:
      app: cpu-heavy
  template:
    metadata:
      labels:
        app: cpu-heavy
    spec:
      containers:
      - name: cpu-load
        image: progrium/stress
        resources:
          requests:
            cpu: "500m"
            memory: "256Mi"
          limits:
            cpu: "1000m"
            memory: "512Mi"
        args:
        - "--cpu"
        - "1"
        - "--io"
        - "1"
        - "--vm"
        - "1"
        - "--timeout"
        - "600s"
"@

# Save to temp file and apply
$tempFile = [System.IO.Path]::GetTempFileName()
Set-Content -Path $tempFile -Value $workloadYaml
kubectl apply -f $tempFile
Remove-Item $tempFile

Write-Host "Heavy workload deployed. Waiting for pods to start..." -ForegroundColor Green

# Step 3: Wait for pods and resources to be consumed
Write-Host ""
Write-Host "[Step 3] Waiting for pods to initialize (30 seconds)..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

Write-Host "Pod status:" -ForegroundColor White
kubectl get pods -o wide

# Step 4: Display resource usage after overload
Write-Host ""
Write-Host "[Step 4] Checking resource usage under load..." -ForegroundColor Yellow
Write-Host "Node metrics after workload deployment:" -ForegroundColor White
kubectl top nodes

# Step 5: Run scheduler to detect and recommend rebalancing
Write-Host ""
Write-Host "[Step 5] Running ClusterBalancer scheduler (DRY-RUN mode)..." -ForegroundColor Yellow
python scheduler/rebalance.py --dry-run

# Step 6: Show monitoring  
Write-Host ""
Write-Host "[Step 6] Starting continuous monitoring (up to 20 seconds)..." -ForegroundColor Yellow
Write-Host ""

# Run monitoring continuously with interval of 5 seconds
# This will show multiple iterations of cluster monitoring
python monitoring/monitor.py --continuous --interval 5 2>&1 | Select-Object -First 150

Write-Host ""
Write-Host "[Step 6] Continuous monitoring completed" -ForegroundColor Green

# Step 7: Cleanup
Write-Host ""
Write-Host "[Step 7] Cleanup options:" -ForegroundColor Cyan
Write-Host ""
Write-Host "To remove the heavy workload and restore normal state, run:" -ForegroundColor White
Write-Host "  kubectl delete deployment cpu-heavy -n default" -ForegroundColor Green
Write-Host ""
Write-Host "Demo completed!" -ForegroundColor Cyan