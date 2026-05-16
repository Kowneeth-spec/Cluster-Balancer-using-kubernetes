
ClusterBalancer
Adaptive Workload Distribution for Kubernetes Clusters
ClusterBalancer is an intelligent, external controller that overcomes the limitations of static scheduling in Kubernetes. It continuously monitors cluster health and automatically redistributes workloads across nodes to ensure balanced CPU and memory utilization — with zero modifications to the Kubernetes core.

Table of Contents

Overview
Problem Statement
Features
Architecture
System Workflow
Installation
Configuration
Usage
Project Structure
Results
Future Enhancements


Overview
Kubernetes is a powerful container orchestration platform, but scheduling decisions are made only at deployment time — it does not adapt to dynamic workload changes at runtime. In real-world environments, this leads to overloaded nodes, wasted resources on underutilized nodes, and degraded application performance.
ClusterBalancer solves this by introducing a continuous feedback loop: collect metrics → analyze → detect imbalance → migrate pods → repeat.

Problem Statement
Without runtime workload redistribution, Kubernetes clusters suffer from:

Uneven distribution of CPU and memory across nodes
High latency and reduced performance on overloaded nodes
Wasted computational resources on underutilized nodes
Increased application response times
The need for manual intervention to balance workloads


Features

Real-time monitoring via Kubernetes Metrics Server and API
Configurable thresholds to define overloaded, balanced, and underutilized states
Intelligent decision engine that classifies nodes and generates migration plans
Safe pod eviction using Kubernetes-native Pod Disruption Budgets (PDB)
Dry-run mode for testing rebalancing logic without applying changes
Retry mechanism for fault-tolerant workload migration
Structured logging and health reports
Modular and scalable design — works independently without touching Kubernetes internals


Architecture
ClusterBalancer follows a three-layer architecture:
Input Layer

Kubernetes Cluster (nodes and pods)
Metrics Server (CPU & memory data)
config.json (thresholds and settings)

Processing Layer

Monitoring Module — collects and normalizes real-time metrics
Decision Engine — classifies nodes and determines if rebalancing is needed
Scheduler Module — executes pod eviction and migration

Output Layer

Health reports and logs
Rebalancing decisions
Workload migration actions


System Workflow
ClusterBalancer runs in a continuous loop:

Collect CPU and memory metrics from all nodes
Analyze resource utilization against configured thresholds
Detect imbalance (overloaded or underutilized nodes)
Generate a workload migration plan
Execute pod eviction; Kubernetes reschedules automatically
Repeat continuously


Installation
Prerequisites

Python 3.8+
A running Kubernetes cluster (Minikube supported)
Docker
Kubernetes Python Client (kubernetes)
Metrics Server enabled on the cluster

Setup
bashgit clone https://github.com/your-username/ClusterBalancer.git
cd ClusterBalancer
pip install -r requirements.txt
Enable Metrics Server on Minikube:
bashminikube addons enable metrics-server

Configuration
Edit config.json to set your thresholds:
json{
  "cpu_overload_threshold": 80,
  "cpu_underload_threshold": 20,
  "memory_overload_threshold": 80,
  "memory_underload_threshold": 20,
  "monitor_interval_seconds": 30,
  "dry_run": false
}
KeyDescriptioncpu_overload_thresholdCPU % above which a node is considered overloadedcpu_underload_thresholdCPU % below which a node is considered underutilizedmemory_overload_thresholdMemory % above which a node is considered overloadeddry_runIf true, decisions are logged but no pods are evicted

Usage
Run the monitoring and decision engine:
bashpython monitor.py
Run the rebalancer:
bashpython rebalance.py
Dry-run mode (no changes applied):
Set "dry_run": true in config.json, then run normally.

Project Structure
ClusterBalancer/
├── monitor.py        # Monitoring module + decision engine
├── rebalance.py      # Scheduler module (pod eviction & migration)
├── config.json       # Configurable thresholds and settings
├── requirements.txt  # Python dependencies
└── README.md

Results
MetricBefore ClusterBalancerAfter ClusterBalancerLoad distributionUnevenBalanced across nodesNode overloadFrequentEliminatedLatencyHighReducedResource utilizationWastefulEfficientSystem stabilityDegradedImproved

Future Enhancements

Machine learning-based predictive scheduling
Multi-cluster workload balancing
Web-based real-time monitoring dashboard
Cost-aware resource optimization


Built With

Python
Kubernetes Python Client
Docker
Minikube
