# 🚀 ClusterBalancer - Execution Guide

Quick reference for running the ClusterBalancer project.

**New:** Added stress-test scenarios to simulate CPU overutilization for testing the monitor!

---

## ✅ Prerequisites

- Kubernetes cluster (Minikube, EKS, GKE, etc.)
- `kubectl` configured and working
- Python 3.7+ installed
- `kubernetes` Python package

---

## 📋 Step-by-Step Execution

### Step 0: Pre-Execution Checklist (NEW!)
Before starting, verify minikube is installed and working:
```powershell
# Check if minikube is installed
minikube version

# Check current cluster status
minikube status
```

**If you see an error like "command not found" or "not recognized":**
- Minikube is not installed or not in your PATH
- See **Troubleshooting → Minikube Not Installed** below

**If status shows stopped or error:**
- Proceed to Step 1 and run `minikube start --nodes=3`

### Step 1: Navigate to Project Directory
```powershell
cd "c:\Users\kowne\Downloads\Drive\CPP Mini Project\ClusterBalancer\ClusterBalancer"
```

### Step 2: Install Dependencies
```powershell
pip install kubernetes
```

### Step 3: Ensure Kubernetes Cluster is Running
```powershell
# Start minikube with 3 nodes (if not already running)
minikube start --nodes=3

# Wait 10 seconds for cluster to fully initialize
Start-Sleep -Seconds 10

# Update kubectl context to point to minikube
minikube update-context

# Verify nodes are ready
kubectl get nodes
```

**Expected Output:**
```
NAME           STATUS   ROLES           AGE    VERSION
minikube       Ready    control-plane   7d2h   v1.35.1
minikube-m02   Ready    <none>          7d2h   v1.35.1
minikube-m03   Ready    <none>          7d2h   v1.35.1
```

**Error: "No connection could be made" or "connection refused"?**
- See **Troubleshooting → Connection Refused Error** below

### Step 4: Enable Metrics Server (For Resource Monitoring)
```powershell
minikube addons enable metrics-server

# Wait 15 seconds for metrics server to be ready
Start-Sleep -Seconds 15

# Verify metrics are working
kubectl top nodes
```

**If you see "error: metrics not available yet":**
- Wait another 10-15 seconds and try again
- Metrics can take 30+ seconds to appear on first startup

### Step 5: Deploy Test Workload (Optional)
```powershell
kubectl apply -f deployment/workload.yaml
```

### Step 6: Run Single Cluster Health Check
```powershell
python monitoring/monitor.py
```

**Expected Output:**
```
2026-05-04 12:56:09 - INFO - ============================================================
2026-05-04 12:56:09 - INFO - ClusterBalancer – Adaptive Workload Distribution System
2026-05-04 12:56:09 - INFO - ============================================================
2026-05-04 12:56:09 - INFO - Mode: Single Check
2026-05-04 12:56:09 - INFO - Node Resource Usage:
2026-05-04 12:56:09 - INFO -   Node: minikube | CPU: 4.3% | Memory: 9.9%
2026-05-04 12:56:09 - INFO -   ✓ All nodes are balanced. No action needed.
```

### Step 7: Deploy Stress Test Workload (Optional - To Test Overutilized Detection)
```powershell
# Deploy the stress test scenarios
kubectl apply -f deployment/stress-test.yaml

# Verify stress pods are running across nodes
kubectl get pods -n stress-test -o wide

# View resource usage on nodes
kubectl top nodes
```

### Step 8: Run Continuous Monitoring (Now With Stress Test Active)
```powershell
python monitoring/monitor.py --continuous --interval 5
```

**Press Ctrl+C to stop**

You should now see overutilized nodes detected by your monitor!

### Step 9: Stop Stress Test When Done
```powershell
# Delete the stress test namespace and all resources
kubectl delete namespace stress-test
```

---

## 🧪 Stress Test Scenarios

### Scenario 1: Balanced Cluster Stress (Minikube Optimized)
Test ClusterBalancer's ability to detect when all nodes are equally overutilized.

**What it does:**
- Deploys **12 stress pods** (4 per node) - **Increased for minikube**
- Each pod runs `stress --cpu 4` for 10 minutes - **More aggressive**
- Spreads pods evenly using `topologySpreadConstraints`
- Uses **100m CPU requests** to fit on minikube's limited resources
- All nodes should reach 5-8% CPU (detected as **overutilized** with new 5% threshold)

**Deploy:**
```powershell
kubectl apply -f deployment/stress-test.yaml
```

**Monitor in real-time:**
```powershell
# In one terminal
python monitoring/monitor.py --continuous --interval 5

# In another terminal, watch pod distribution
kubectl get pods -n stress-test -o wide -w
```

**Expected Monitor Output:**
```
2026-05-04 13:15:30 - INFO - Node Resource Usage:
2026-05-04 13:15:30 - INFO -   Node: minikube | CPU: 7.1% | Memory: 13.4%
2026-05-04 13:15:30 - INFO -   ✓ Node minikube is overutilized (CPU: 7.1% > threshold 5%)

2026-05-04 13:15:30 - INFO -   Node: minikube-m02 | CPU: 6.8% | Memory: 8.2%
2026-05-04 13:15:30 - INFO -   ✓ Node minikube-m02 is overutilized (CPU: 6.8% > threshold 5%)

2026-05-04 13:15:30 - INFO -   Node: minikube-m03 | CPU: 7.2% | Memory: 9.5%
2026-05-04 13:15:30 - INFO -   ✓ Node minikube-m03 is overutilized (CPU: 7.2% > threshold 5%)

2026-05-04 13:15:30 - INFO - ⚠ All nodes are overutilized. System needs scaling or optimization.
```

### Scenario 2: Imbalanced Cluster Stress (Minikube Optimized)
Test ClusterBalancer's ability to detect workload imbalance.

**What it does:**
- Deploys **15 stress pods** all pinned to control-plane (minikube) - **Increased for minikube**
- Each pod runs `stress --cpu 4` - **More aggressive**
- Worker nodes remain underutilized
- Creates a clear imbalance scenario
- Control-plane should reach 7-8% CPU (detected as **overutilized** with 5% threshold)
- Worker nodes at 1-2% CPU (detected as **underutilized** with 2% threshold)

**Deploy (same command):**
```powershell
kubectl apply -f deployment/stress-test.yaml
```

**Monitor Output Expectations:**
```
2026-05-04 13:15:30 - INFO - Node Resource Usage:
2026-05-04 13:15:30 - INFO -   Node: minikube | CPU: 8.2% | Memory: 15.5%
2026-05-04 13:15:30 - INFO -   ✓ Node minikube is overutilized (CPU: 8.2% > threshold 5%)

2026-05-04 13:15:30 - INFO -   Node: minikube-m02 | CPU: 1.1% | Memory: 2.1%
2026-05-04 13:15:30 - INFO -   ✓ Node minikube-m02 is underutilized (CPU: 1.1% < threshold 2%)

2026-05-04 13:15:30 - INFO -   Node: minikube-m03 | CPU: 0.9% | Memory: 1.8%
2026-05-04 13:15:30 - INFO -   ✓ Node minikube-m03 is underutilized (CPU: 0.9% < threshold 2%)

2026-05-04 13:15:30 - INFO - ⚠ Cluster is imbalanced! Some nodes overutilized, others underutilized.
2026-05-04 13:15:30 - INFO - ⚠ Imbalance: 7.3% difference between highest and lowest CPU
2026-05-04 13:15:30 - INFO - ⚠ Recommend: Migrate workloads from minikube to minikube-m02, minikube-m03
```

### Cleanup Stress Test
```powershell
# Delete the entire stress-test namespace and all resources
kubectl delete namespace stress-test

# Verify it's deleted
kubectl get namespaces | findstr stress-test
```

---

### Monitor Script Options

```bash
# Single health check (default)
python monitoring/monitor.py

# Continuous monitoring every 5 seconds
python monitoring/monitor.py --continuous --interval 5

# Continuous monitoring every 30 seconds
python monitoring/monitor.py --continuous --interval 30

# Continuous monitoring every 60 seconds
python monitoring/monitor.py --continuous --interval 60
```

### Real-Time Resource Monitoring

```bash
# Watch node resource usage in real-time
kubectl top nodes -w

# Watch pod resource usage in real-time
kubectl top pods -n stress-test -w

# View detailed node metrics
kubectl describe node minikube
kubectl describe node minikube-m02
kubectl describe node minikube-m03

# Get metrics for all pods
kubectl top pods --all-namespaces

# Watch stress test pods continuously
kubectl get pods -n stress-test -o wide -w
```

### Kubernetes Commands

```bash
# View all nodes in cluster
kubectl get nodes

# View detailed node information
kubectl get nodes -o wide

# View all pods in default namespace
kubectl get pods

# View pods with resource usage
kubectl top nodes
kubectl top pods

# View the deployed workload
kubectl get deployment -n stress-test

# View all resources in stress-test namespace
kubectl get all -n stress-test

# View events in stress-test namespace
kubectl get events -n stress-test

# Delete the stress test workload
kubectl delete namespace stress-test

# View cluster status
minikube status

# Stop the cluster
minikube stop

# Start the cluster
minikube start

# Delete the cluster
minikube delete
```

---

## 📊 Understanding the Output

### Node Status Indicators (Updated for Minikube Thresholds):

- **Overloaded Node** (CPU > 5%): Detected as overutilized - will trigger rebalancing alerts
- **Underutilized Node** (CPU < 2%): Detected as underutilized - can receive more workloads
- **Balanced Node** (CPU 2-5%): Optimal range for minikube environments
- **Imbalance Threshold**: >5% difference between highest and lowest CPU usage

### Example Output (Minikube Environment):

```
Node: minikube | CPU: 7.1% | Memory: 13.4%
✓ Node minikube is overutilized (CPU: 7.1% > threshold 5%)

Node: minikube-m02 | CPU: 1.5% | Memory: 2.1%
✓ Node minikube-m02 is underutilized (CPU: 1.5% < threshold 2%)
```

---

## 🛠️ Troubleshooting

### Connection Refused Error ("dial tcp 127.0.0.1:56544: connectex")
This error means kubectl cannot connect to the minikube API server.

**Solution:**
```powershell
# Step 1: Check if cluster is actually running
minikube status

# Step 2: If status shows "Stopped", start it
minikube start --nodes=3
Start-Sleep -Seconds 15

# Step 3: Update the kubectl context
minikube update-context

# Step 4: Verify connection works
kubectl get nodes
```

**If still not working after Step 4:**
```powershell
# Hard reset kubectl context
minikube delete
Start-Sleep -Seconds 5
minikube start --nodes=3
Start-Sleep -Seconds 20
minikube update-context
kubectl get nodes
```

### Minikube Not Installed
If you get "minikube: command not found" or "'minikube' is not recognized":

**For Windows:**
1. Download minikube from: https://github.com/kubernetes/minikube/releases
2. Place the `.exe` file in a folder (e.g., `C:\Program Files\minikube\`)
3. Add that folder to your Windows PATH:
   - Right-click "This PC" → Properties → Advanced system settings
   - Click "Environment Variables"
   - Under "System variables", find "Path" and click Edit
   - Click "New" and add `C:\Program Files\minikube\`
   - Click OK and restart PowerShell
4. Verify installation:
   ```powershell
   minikube version
   ```

### Minikube Fails to Start
If `minikube start` hangs or fails:

```powershell
# Check what driver is being used
minikube config get driver

# Try starting with explicit driver (Docker is most common on Windows)
minikube start --driver=docker --nodes=3

# If Docker fails, try Hyper-V
minikube start --driver=hyperv --nodes=3

# If both fail, completely reset minikube
minikube delete --all
minkube cache prune
minikube start --driver=docker --nodes=3
```

**Ensure Docker Desktop is running** (if using Docker driver) - Check system tray for Docker icon

### Metrics Not Available
```powershell
# Enable metrics-server
minikube addons enable metrics-server

# Wait 20 seconds (can take longer on first startup)
Start-Sleep -Seconds 20

# Check metrics
kubectl top nodes

# If still showing "metrics not available yet", wait another 30 seconds
```

### Python Dependencies Missing
```powershell
# Reinstall kubernetes package
pip install --upgrade kubernetes

# Verify installation
pip list | findstr kubernetes

# Should show: kubernetes  X.X.X
```

### kubectl Context Issues
```powershell
# List all contexts
kubectl config get-contexts

# Set context to minikube
kubectl config use-context minikube

# Verify context is set
kubectl config current-context
```

---

## 🧪 Complete Testing Workflow

### Full End-to-End Test
This workflow demonstrates ClusterBalancer detecting overutilized and imbalanced nodes.

```powershell
# Step 1: Clean up any previous stress tests
kubectl delete namespace stress-test --ignore-not-found=true
Start-Sleep -Seconds 5

# Step 2: Deploy stress test scenarios
kubectl apply -f deployment/stress-test.yaml
Start-Sleep -Seconds 10

# Step 3: Verify pods are running
kubectl get pods -n stress-test -o wide

# Step 4: Check node resource usage
kubectl top nodes

# Step 5: Run ClusterBalancer monitor in continuous mode
python monitoring/monitor.py --continuous --interval 5

# (Monitor will show overutilized/underutilized nodes)
# (Press Ctrl+C to stop monitoring)

# Step 6: Cleanup
kubectl delete namespace stress-test
```

### What to Expect
1. **First 10 seconds:** Pods are starting, stress processes initializing
2. **After 15 seconds:** Pods running at full stress level (CPU shows in metrics)
3. **Monitor output:** 
   - Balanced: All nodes should show 5-8% CPU (all **overutilized**)
   - Imbalanced: Control-plane 7-8% (overutilized), workers 0.5-1% (underutilized)
4. **After 600s (10 min):** Stress pods exit automatically, CPU returns to baseline

---

## 🔧 Configuration Changes Made for Minikube

### config.json - Updated Thresholds
Due to minikube's limited CPU resources on Docker driver, thresholds have been optimized:

```json
{
  "thresholds": {
    "cpu_overloaded_percent": 5,      // ← Lowered from 70% to 5%
    "cpu_underutilized_percent": 2,   // ← Lowered from 30% to 2%
    "memory_overloaded_percent": 80,
    "memory_underutilized_percent": 20
  }
}
```

**Why these changes:**
- Minikube on Docker has very limited CPU cores (typically 2-4 cores shared)
- Stress pods can only push usage to 5-8% due to resource constraints
- Lower thresholds allow testing of overutilized/imbalanced detection
- File location: `c:\Users\kowne\Downloads\Drive\CPP Mini Project\ClusterBalancer\ClusterBalancer\config.json`

### stress-test.yaml - Optimized for Minikube

| Setting | Before | After | Reason |
|---------|--------|-------|--------|
| Balanced replicas | 6 | **12** | More pods = more CPU stress |
| Imbalanced replicas | 9 | **15** | Heavier load on control-plane |
| CPU stress cores | `--cpu 2` | **`--cpu 4`** | More aggressive stress |
| CPU requests | 1000m | **100m** | Fit more pods on limited minikube |
| CPU limits | 2000m | **500m** | Allow stress to show in metrics |
| Memory requests | 256Mi | **64Mi** | Reduce memory pressure |

---

## 🎯 Quick Reference

| Command | Purpose |
|---------|---------|
| `python monitoring/monitor.py` | Single health check |
| `python monitoring/monitor.py --continuous --interval 5` | Real-time monitoring |
| `kubectl apply -f deployment/stress-test.yaml` | Deploy CPU stress test (balanced + imbalanced) |
| `kubectl get pods -n stress-test -o wide` | View stress pod distribution across nodes |
| `kubectl delete namespace stress-test` | Clean up stress test |
| `kubectl top nodes` | View live node resource usage |
| `kubectl top pods -n stress-test` | View stress pod resource usage |
| `kubectl get nodes` | View cluster nodes |
| `kubectl apply -f deployment/workload.yaml` | Deploy original workload |
| `minikube start --nodes=3` | Start multi-node cluster |
| `minikube addons enable metrics-server` | Enable metrics server |
| `minikube status` | Check cluster status |

---

## 📖 Full Documentation

For complete project documentation, see [README.md](README.md)
