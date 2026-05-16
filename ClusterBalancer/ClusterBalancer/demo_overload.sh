#!/bin/bash
# ClusterBalancer - Overload Demo Script
# This creates CPU-intensive workloads to demonstrate rebalancing

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  ClusterBalancer - Overload & Rebalancing Demo             ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Step 1: Check current cluster state
echo "📊 STEP 1: Checking current cluster state..."
echo ""
kubectl get nodes
echo ""
kubectl top nodes 2>/dev/null || echo "  (metrics-server may not be ready)"
echo ""

# Step 2: Create heavy CPU workload
echo "⚙️  STEP 2: Deploying high-CPU workload to trigger overload..."
echo ""
cat << 'EOF' > /tmp/heavy-workload.yaml
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
      - name: stress
        image: polinux/stress:latest
        args:
          - "--cpu"
          - "4"
          - "--io"
          - "1"
          - "--vm"
          - "1"
          - "--vm-bytes"
          - "128M"
          - "--verbose"
        resources:
          limits:
            cpu: "2"
            memory: "512Mi"
          requests:
            cpu: "1.5"
            memory: "256Mi"
EOF

kubectl apply -f /tmp/heavy-workload.yaml
echo "  ✓ Heavy workload deployed (4 replicas with high CPU demands)"
echo ""

# Step 3: Wait for pods to start
echo "⏳ STEP 3: Waiting for pods to start (30 seconds)..."
sleep 30
echo ""

# Step 4: Show overloaded state
echo "🔴 STEP 4: Current state - Some nodes should be overloaded..."
echo ""
echo "Nodes:"
kubectl get nodes
echo ""
echo "Pods distribution:"
kubectl get pods -o wide | grep -E "cpu|NAME"
echo ""

echo "📈 Node metrics (CPU overloaded > 5%):"
echo ""
python -c "
import subprocess
import time
try:
    result = subprocess.run(['kubectl', 'top', 'nodes'], capture_output=True, text=True, timeout=5)
    print(result.stdout)
except:
    print('Metrics not yet available - wait a moment and try again')
"
echo ""

# Step 5: Run ClusterBalancer monitoring
echo "📊 STEP 5: Running ClusterBalancer monitoring..."
echo ""
echo "Output shows:"
echo "  - Nodes with CPU > 5% = OVERLOADED"
echo "  - Nodes with CPU < 30% = UNDERUTILIZED"
echo ""

cd "c:\Users\kowne\Downloads\Drive\CPP Mini Project\ClusterBalancer\ClusterBalancer"
python monitoring/monitor.py
echo ""

# Step 6: Show rebalancing option
echo "🔄 STEP 6: Proposed rebalancing..."
echo ""
echo "If overloaded nodes detected, you can:"
echo ""
echo "  Preview: python scheduler/rebalance.py --dry-run"
echo "  Rebalance: python scheduler/rebalance.py"
echo ""

# Step 7: Cleanup
echo "🧹 STEP 7: Cleanup instructions..."
echo ""
echo "To remove the heavy workload:"
echo "  kubectl delete deployment cpu-heavy"
echo ""
echo "To check again later:"
echo "  python monitoring/monitor.py --continuous"
echo ""

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  Demo Complete!                                            ║"
echo "╚════════════════════════════════════════════════════════════╝"
