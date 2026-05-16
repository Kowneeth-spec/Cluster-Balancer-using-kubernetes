from kubernetes import client, config
import sys
import time
import json
import argparse
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_CONFIG = {
    "thresholds": {
        "cpu_overloaded_percent": 70,
        "cpu_underutilized_percent": 30,
        "memory_overloaded_percent": 80,
        "memory_underutilized_percent": 20
    },
    "monitoring": {
        "check_interval_seconds": 30,
        "continuous_mode": False
    },
    "migration": {
        "max_retries": 3,
        "retry_delay_seconds": 5,
        "enable_pod_disruption_budget": True,
        "graceful_termination_seconds": 30
    }
}

# Demo mode node data: (node_name, cpu_percent, mem_percent)
DEMO_NODES = [
    ("overloaded-node-1", 91, 75),
    ("overloaded-node-2", 88, 72),
    ("overloaded-node-3", 76, 65),
    ("overloaded-node-4", 81, 70),
    ("overloaded-node-5", 85, 71),
    ("overloaded-node-6", 66, 60),
    ("underutilized-node-1", 12, 15),
    ("underutilized-node-2", 8, 10),
    ("underutilized-node-3", 5, 8),
    ("underutilized-node-4", 3, 5),
]

def load_config():
    """Load configuration from config.json or use defaults."""
    config_path = Path(__file__).parent.parent / "config.json"
    try:
        if config_path.exists():
            with open(config_path, 'r') as f:
                config_data = json.load(f)
                logger.info(f"Configuration loaded from {config_path}")
                return config_data
        else:
            logger.warning(f"Config file not found. Using default configuration.")
            return DEFAULT_CONFIG
    except Exception as e:
        logger.error(f"Error loading config file: {e}. Using default configuration.")
        return DEFAULT_CONFIG

def parse_cpu(cpu_str):
    """Parse CPU usage string to millicores."""
    if cpu_str.endswith('m'):
        return int(cpu_str[:-1])
    elif cpu_str.endswith('n'):
        return int(cpu_str[:-1]) // 1000000  # nano to milli
    elif '.' in cpu_str:
        return int(float(cpu_str) * 1000)
    else:
        return int(cpu_str) * 1000

def parse_memory(mem_str):
    """Parse memory usage string to bytes."""
    if mem_str.endswith('Ki'):
        return int(mem_str[:-2]) * 1024
    elif mem_str.endswith('Mi'):
        return int(mem_str[:-2]) * 1024 * 1024
    elif mem_str.endswith('Gi'):
        return int(mem_str[:-2]) * 1024 * 1024 * 1024
    else:
        return int(mem_str)

def get_node_metrics(retries=3):
    """Retrieve node metrics from metrics-server with retry logic."""
    for attempt in range(retries):
        try:
            custom_api = client.CustomObjectsApi()
            return custom_api.list_cluster_custom_object("metrics.k8s.io", "v1beta1", "nodes")
        except Exception as e:
            if attempt < retries - 1:
                logger.warning(f"Attempt {attempt + 1}/{retries}: Error getting node metrics: {e}. Retrying...")
                time.sleep(2)
            else:
                logger.error(f"Error getting node metrics after {retries} attempts: {e}.")
                return None
    return None

def create_pod_disruption_budget(v1, namespace, pod_name):
    """Create a Pod Disruption Budget to protect the pod during migration."""
    try:
        from kubernetes.client.models import (
            V1PodDisruptionBudget,
            V1PodDisruptionBudgetSpec,
            V1LabelSelector,
            V1ObjectMeta
        )
        
        pdb_name = f"{pod_name}-pdb"
        pdb_namespace = namespace
        
        # Check if PDB already exists
        api_instance = client.CustomObjectsApi()
        try:
            api_instance.get_namespaced_custom_object(
                group="policy",
                version="v1",
                namespace=pdb_namespace,
                plural="poddisruptionbudgets",
                name=pdb_name
            )
            logger.info(f"PDB {pdb_name} already exists.")
            return True
        except:
            pass
        
        # Create new PDB
        pdb_body = {
            "apiVersion": "policy/v1",
            "kind": "PodDisruptionBudget",
            "metadata": {
                "name": pdb_name,
                "namespace": pdb_namespace
            },
            "spec": {
                "maxUnavailable": 0,
                "selector": {
                    "matchLabels": {
                        "app": pod_name.split('-')[0]  # Use first part of pod name as label
                    }
                }
            }
        }
        
        api_instance.create_namespaced_custom_object(
            group="policy",
            version="v1",
            namespace=pdb_namespace,
            plural="poddisruptionbudgets",
            body=pdb_body
        )
        logger.info(f"Pod Disruption Budget created for {pod_name} in {namespace}")
        return True
    except Exception as e:
        logger.warning(f"Could not create PDB for {pod_name}: {e}. Proceeding without PDB.")
        return False

def migrate_pod(v1, pod_name, namespace, config_data):
    """Safely migrate a pod with retries and graceful termination."""
    migration_config = config_data["migration"]
    max_retries = migration_config["max_retries"]
    retry_delay = migration_config["retry_delay_seconds"]
    grace_period = migration_config["graceful_termination_seconds"]
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Migration attempt {attempt + 1}/{max_retries} for pod {pod_name}")
            
            # Delete pod with graceful termination
            v1.delete_namespaced_pod(
                pod_name,
                namespace,
                grace_period_seconds=grace_period
            )
            logger.info(f"Pod {pod_name} deleted successfully. Kubernetes will reschedule it.")
            return True
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"Migration attempt failed: {e}. Retrying in {retry_delay}s...")
                time.sleep(retry_delay)
            else:
                logger.error(f"Migration failed after {max_retries} attempts: {e}")
                return False
    return False

def get_overloaded_nodes(config_data):
    """Identify overloaded nodes based on CPU threshold."""
    thresholds = config_data["thresholds"]
    cpu_threshold = thresholds["cpu_overloaded_percent"]
    
    try:
        config.load_kube_config()
    except Exception as e:
        logger.error(f"Error loading Kubernetes config: {e}")
        return []

    v1 = client.CoreV1Api()
    try:
        nodes = v1.list_node()
    except Exception as e:
        logger.error(f"Error listing nodes: {e}")
        return []
    
    metrics = get_node_metrics()
    if not metrics:
        logger.warning("Could not retrieve metrics.")
        return []

    overloaded = []
    for node in nodes.items:
        name = node.metadata.name
        try:
            cpu_capacity = int(node.status.capacity['cpu']) * 1000
            node_metric = next((item for item in metrics['items'] if item['metadata']['name'] == name), None)
            if node_metric:
                cpu_used = parse_cpu(node_metric['usage']['cpu'])
                cpu_percent = (cpu_used / cpu_capacity) * 100
                if cpu_percent > cpu_threshold:
                    overloaded.append(name)
                    logger.warning(f"Node {name} is overloaded: {cpu_percent:.1f}%")
        except Exception as e:
            logger.warning(f"Error processing node {name}: {e}")
            continue
    
    return overloaded

def main():
    """Main entry point for workload rebalancing."""
    parser = argparse.ArgumentParser(
        description="ClusterBalancer Scheduler - Rebalance workloads dynamically"
    )
    parser.add_argument(
        "--dry-run", "-d",
        action="store_true",
        help="Preview changes without applying them"
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to custom config file"
    )
    parser.add_argument(
        "--skip-pdb", "-s",
        action="store_true",
        help="Skip Pod Disruption Budget creation"
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Use demo mode with simulated node data"
    )
    
    args = parser.parse_args()
    
    # Load configuration
    config_data = load_config()
    
    if args.config:
        try:
            with open(args.config, 'r') as f:
                config_data = json.load(f)
                logger.info(f"Custom configuration loaded from {args.config}")
        except Exception as e:
            logger.error(f"Error loading custom config: {e}. Using default config.")
    
    logger.info("=" * 60)
    logger.info("ClusterBalancer – Adaptive Workload Distribution System")
    logger.info("Scheduler: Rebalancing workload...")
    logger.info("=" * 60)
    
    if args.dry_run:
        logger.info("DRY-RUN MODE: No changes will be applied")
    
    overloaded = get_overloaded_nodes(config_data)
    if not overloaded:
        logger.info("No overloaded nodes detected. No rebalancing needed.")
        return

    logger.warning(f"Found overloaded nodes: {', '.join(overloaded)}")

    try:
        config.load_kube_config()
    except Exception as e:
        logger.error(f"Error loading Kubernetes config: {e}")
        sys.exit(1)

    v1 = client.CoreV1Api()

    try:
        pods = v1.list_pod_for_all_namespaces()
    except Exception as e:
        logger.error(f"Error listing pods: {e}")
        sys.exit(1)

    # Find pods on overloaded nodes
    candidate_pods = []
    for pod in pods.items:
        if pod.spec.node_name in overloaded and pod.status.phase == 'Running':
            candidate_pods.append((pod.metadata.name, pod.metadata.namespace, pod.spec.node_name))

    if not candidate_pods:
        logger.info("No running pods found on overloaded nodes.")
        return

    logger.info(f"Found {len(candidate_pods)} candidate pods for migration.")
    
    # Select the first candidate pod for migration
    pod_name, namespace, node_name = candidate_pods[0]
    logger.info(f"Selected pod for migration: '{pod_name}' (namespace: {namespace}, node: {node_name})")
    
    if args.dry_run:
        logger.info(f"[DRY-RUN] Would migrate pod '{pod_name}' from node '{node_name}'")
        return
    
    # Create PDB if enabled
    pdb_enabled = config_data["migration"]["enable_pod_disruption_budget"] and not args.skip_pdb
    if pdb_enabled:
        logger.info("Creating Pod Disruption Budget for pod safety...")
        create_pod_disruption_budget(v1, namespace, pod_name)
    
    # Migrate the pod
    logger.info(f"Initiating migration of pod '{pod_name}' from overloaded node '{node_name}'...")
    success = migrate_pod(v1, pod_name, namespace, config_data)
    
    if success:
        logger.info("Waiting for pod to be rescheduled...")
        time.sleep(5)
        logger.info("✓ Rebalancing complete!")
    else:
        logger.error("✗ Rebalancing failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()