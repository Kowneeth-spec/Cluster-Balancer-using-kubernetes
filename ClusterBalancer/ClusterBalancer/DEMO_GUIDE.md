# 🎯 ClusterBalancer - Overload Demo Guide

This guide shows you how to create an **overload scenario** and watch ClusterBalancer detect and fix it.

---

## 📋 What This Demo Shows

1. **Normal State** - Balanced cluster with light load
2. **Overload Creation** - Deploy high-CPU workload to trigger imbalance
3. **Detection** - ClusterBalancer detects overloaded nodes (>70% CPU)
4. **Decision** - System identifies pods for migration
5. **Rebalancing** - Pods are moved to underutilized nodes
6. **Recovery** - Cluster returns to balanced state

---

## 🚀 Quick Start (10 minutes)

### Option 1: Use PowerShell Demo Script (Recommended for Windows)

```powershell
cd "c:\Users\kowne\Downloads\Drive\CPP Mini Project\ClusterBalancer\ClusterBalancer"
.\demo_overload.ps1
```

This automatically:
- ✅ Shows current cluster state
- ✅ Deploys 4 heavy CPU pods
- ✅ Waits for pods to consume resources
- ✅ Runs monitoring to detect overload
- ✅ Shows rebalancing options
- ✅ Provides cleanup instructions

### Option 2: Manual Step-by-Step (More Control)

Follow the manual steps below ⬇️

---

## 📝 Manual Step-by-Step Demo

### STEP 1: Check Current Cluster State

```bash
# See your nodes
kubectl get nodes

# Check initial resource usage
kubectl top nodes

# List current pods
kubectl get pods -o wide
```

**Expected Output:**
```
NAME           STATUS   ROLES                VERSION
minikube       Ready    control-plane   v1.35.1
minikube-m02   Ready    <none>         v1.35.1
minikube-m03   Ready    <none>         v1.35.1
```

---

### STEP 2: Create Heavy CPU Workload

Create a file `heavy-workload.yaml`:

```yaml
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
          - "2"           # Use 2 CPUs
          - "--io"
          - "1"
          - "--vm"
          - "1"
          - "--verbose"
        resources:
          limits:
            cpu: "1500m"             # 1.5 CPU max
            memory: "512Mi"
          requests:
            cpu: "1000m"             # 1 CPU requested
            memory: "256Mi"
```

Deploy it:

```bash
kubectl apply -f heavy-workload.yaml
```

**Expected Output:**
```
deployment.apps/cpu-heavy created
```

---

### STEP 3: Wait for Pods to Start and Consume CPU

```bash
# Watch pods starting
kubectl get pods -l app=cpu-heavy -w

# Check pod distribution across nodes
kubectl get pods -l app=cpu-heavy -o wide
```

**Wait 1-2 minutes** for pods to consume CPU and trigger overload.

---

### STEP 4: See Overloaded State (Optional)

```bash
# Check resource usage by node
kubectl top nodes

# Or the detailed output:
kubectl top nodes --no-headers
```

**Expected Output (when overloaded):**
```
NAME           CPU(cores)   CPU%    MEMORY(bytes)   MEMORY%
minikube       1800m        90%     800Mi           50%      ← OVERLOADED!
minikube-m02   200m         10%     150Mi           10%      ← UNDERUTILIZED
minikube-m03   150m         7%      140Mi           9%       ← UNDERUTILIZED
```

---

### STEP 5: Run ClusterBalancer Monitoring

```bash
cd "c:\Users\kowne\Downloads\Drive\CPP Mini Project\ClusterBalancer\ClusterBalancer"
python monitoring/monitor.py
```

**Expected Output (shows overload):**
```
2026-04-16 22:50:00 - INFO - Node Resource Usage:
2026-04-16 22:50:00 - INFO - Node: minikube | CPU: 90.0% | Memory: 50.0%
2026-04-16 22:50:00 - INFO - ⚠️ Node minikube is overloaded (CPU: 90.0%)

2026-04-16 22:50:00 - INFO - Node: minikube-m02 | CPU: 10.0% | Memory: 10.0%
2026-04-16 22:50:00 - INFO - ✓ Node minikube-m02 is underutilized (CPU: 10.0%)

2026-04-16 22:50:00 - INFO - Node: minikube-m03 | CPU: 7.0% | Memory: 9.0%
2026-04-16 22:50:00 - INFO - ✓ Node minikube-m03 is underutilized (CPU: 7.0%)

2026-04-16 22:50:00 - INFO - Decision Engine:
2026-04-16 22:50:00 - INFO - Overloaded nodes: minikube
2026-04-16 22:50:00 - INFO - Underutilized nodes: minikube-m02, minikube-m03
2026-04-16 22:50:00 - INFO - ✓ Recommendation: Migrate workloads from minikube to healthier nodes
```

---

### STEP 6: Preview Rebalancing (Optional - No Changes)

```bash
python scheduler/rebalance.py --dry-run
```

**Expected Output:**
```
2026-04-16 22:51:00 - INFO - DRY-RUN MODE: No changes will be applied
2026-04-16 22:51:00 - INFO - Found overloaded nodes: minikube
2026-04-16 22:51:00 - INFO - Found 2 candidate pods for migration
2026-04-16 22:51:00 - INFO - [DRY-RUN] Would migrate pod 'cpu-heavy-xyz' from node 'minikube'
```

---

### STEP 7: Actually Rebalance (OPTIONAL - Makes Changes)

```bash
python scheduler/rebalance.py
```

**Expected Output:**
```
2026-04-16 22:52:00 - INFO - Found overloaded nodes: minikube
2026-04-16 22:52:00 - INFO - Found 2 candidate pods for migration
2026-04-16 22:52:00 - INFO - Creating Pod Disruption Budget for pod safety...
2026-04-16 22:52:00 - INFO - Pod Disruption Budget created
2026-04-16 22:52:00 - INFO - Initiating migration of pod 'cpu-heavy-xyz'...
2026-04-16 22:52:00 - INFO - Pod deleted successfully. Kubernetes will reschedule it.
2026-04-16 22:52:05 - INFO - ✓ Rebalancing complete!
```

**What's happening:**
- Pod is deleted from overloaded node
- Kubernetes scheduler places it on a healthier node
- Cluster gradually rebalances

---

### STEP 8: Watch Recovery (Optional)

```bash
# Monitor continuously to see rebalancing in action
python monitoring/monitor.py --continuous --interval 5
```

**You'll see:**
- CPU on overloaded node drops as pods move
- CPU on underutilized nodes increases
- Eventually all nodes become balanced

Press **Ctrl+C** to stop.

---

### STEP 9: Verify Rebalancing Worked

```bash
# Check new pod distribution
kubectl get pods -l app=cpu-heavy -o wide

# Check resource usage is now balanced
kubectl top nodes
```

**Expected After Rebalancing:**
```
NAME           CPU(cores)   CPU%    MEMORY(bytes)   MEMORY%
minikube       600m         30%     300Mi           20%      ← BALANCED ✓
minikube-m02   700m         35%     400Mi           25%      ← BALANCED ✓
minikube-m03   650m         32%     380Mi           24%      ← BALANCED ✓
```

---

### STEP 10: Cleanup

Remove the heavy workload:

```bash
kubectl delete deployment cpu-heavy
```

**Expected Output:**
```
deployment.apps "cpu-heavy" deleted
```

Verify cleanup:

```bash
kubectl get pods -l app=cpu-heavy
# Should show: No resources found in default namespace
```

Run monitoring again to see normal state:

```bash
python monitoring/monitor.py
```

---

## 📊 Demo Configuration Details

### Heavy Workload Specs
| Setting | Value | Purpose |
|---------|-------|---------|
| Replicas | 4 | Creates multiple pods across nodes |
| CPU Limit | 1500m | 1.5 CPU max per pod |
| CPU Request | 1000m | 1 CPU requested per pod |
| Total Load | 4 CPU | Forces overload on 3-CPU cluster |
| Stress Tool | polinux/stress | Generates real CPU load |

### Monitoring Thresholds
| Metric | Threshold | Action |
|--------|-----------|--------|
| CPU > 70% | Overloaded | Flag node, recommend migration |
| CPU < 30% | Underutilized | Candidate for receiving pods |
| Check Interval | 30 sec (default) | Frequency of monitoring |

---

## 🎯 What You Should See

### Timeline

| Time | What Happens |
|------|--------------|
| T+0s | Deploy 4 heavy pods |
| T+10s | Pods start consuming CPU |
| T+30s | Cluster becomes overloaded |
| T+60s | Monitor detects overload |
| T+90s | Rebalancer moves pods |
| T+120s | Cluster rebalances |
| T+180s | All nodes balanced again |

### Expected Output Sequence

```
1️⃣ NORMAL STATE
   Node: minikube | CPU: 5% | Memory: 10%
   ✓ All nodes balanced

2️⃣ AFTER DEPLOYMENT
   Node: minikube | CPU: 85% | Memory: 35%
   ⚠️ Node is overloaded!

3️⃣ AFTER REBALANCING
   Node: minikube | CPU: 40% | Memory: 20%
   ✓ All nodes balanced again
```

---

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| Pods not starting | Wait longer (5 minutes), check image downloads |
| No overload detected | Increase stress workload, check thresholds |
| Metrics not available | Wait for metrics-server to initialize |
| Rebalancing fails | Check RBAC permissions, increase grace period |
| Pod won't rebalance | Manually delete: `kubectl delete pod <name>` |

---

## 📚 Related Commands

```bash
# View all pods across all namespaces
kubectl get pods -A

# Watch pod creation in real-time
kubectl get pods -l app=cpu-heavy -w

# See pod details
kubectl describe pod <pod-name>

# Check pod logs
kubectl logs <pod-name>

# See events
kubectl get events

# View resource requests/limits
kubectl describe node <node-name>
```

---

## 🎓 What You'll Learn

By running this demo, you'll understand:

✅ How ClusterBalancer detects overloaded nodes
✅ How it identifies pods for migration
✅ How it safely moves workloads
✅ How Kubernetes reschedules pods
✅ How the cluster rebalances automatically
✅ How to use each script (monitor, rebalance, demo)

---

## 💡 Tips

- **For production**: Use `--dry-run` before actual migration
- **For learning**: Run each step individually to understand
- **For continuous**: Use `--continuous` mode to watch in real-time
- **For troubleshooting**: Check `kubectl describe pod <name>` for details

---

## ✨ Summary

This demo shows ClusterBalancer's core functionality:

1. **Detection** - Finds overloaded nodes
2. **Decision** - Recommends migrations
3. **Action** - Safely moves workloads
4. **Recovery** - Cluster rebalances automatically

**Everything works together to keep your Kubernetes cluster healthy!** 🚀

---

**Next Steps:**
1. Run the demo to see it work
2. Try `--dry-run` to preview changes safely
3. Customize thresholds in `config.json`
4. Run `--continuous` for production monitoring
