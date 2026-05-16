from kubernetes import client, config
import sys
import json
import time
import argparse
import logging
from pathlib import Path

# ANSI color codes for terminal output
class ColoredFormatter(logging.Formatter):
    """Custom formatter with colored output"""
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[92m',       # Green
        'WARNING': '\033[93m',    # Yellow
        'ERROR': '\033[91m',      # Red
        'CRITICAL': '\033[95m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.COLORS['INFO'])
        record.levelname = f"{log_color}{record.levelname}{self.COLORS['RESET']}"
        record.msg = f"{log_color}{record.msg}{self.COLORS['RESET']}"
        return super().format(record)

# Setup logging with colors
handler = logging.StreamHandler()
formatter = ColoredFormatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(handler)

# Default configuration (used if config.json not found)
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
            logger.warning(f"Config file not found at {config_path}. Using default configuration.")
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
                logger.error(f"Error getting node metrics after {retries} attempts: {e}. Ensure metrics-server is installed and running.")
                return None
    return None

def check_cluster_balance(config_data):
    """Check cluster balance and return analysis. Can be called repeatedly."""
    thresholds = config_data["thresholds"]
    cpu_overload = thresholds["cpu_overloaded_percent"]
    cpu_underutil = thresholds["cpu_underutilized_percent"]
    
    try:
        config.load_kube_config()
    except Exception as e:
        logger.error(f"Error loading Kubernetes config: {e}")
        return None

    v1 = client.CoreV1Api()

    try:
        nodes = v1.list_node()
    except Exception as e:
        logger.error(f"Error listing nodes: {e}")
        return None

    metrics = get_node_metrics()
    if not metrics:
        logger.warning("Could not retrieve metrics. Skipping this check.")
        return None

    overloaded = []
    underutilized = []

    logger.info("Node Resource Usage:")
    for node in nodes.items:
        name = node.metadata.name
        cpu_capacity = int(node.status.capacity['cpu']) * 1000  # cores to millicores
        mem_capacity_str = node.status.capacity['memory']
        mem_capacity = parse_memory(mem_capacity_str)

        # Find metrics for this node
        node_metric = next((item for item in metrics['items'] if item['metadata']['name'] == name), None)
        if node_metric:
            cpu_used = parse_cpu(node_metric['usage']['cpu'])
            mem_used = parse_memory(node_metric['usage']['memory'])

            cpu_percent = (cpu_used / cpu_capacity) * 100
            mem_percent = (mem_used / mem_capacity) * 100

            logger.info(f"  Node: {name} | CPU: {cpu_percent:.1f}% | Memory: {mem_percent:.1f}%")

            if cpu_percent > cpu_overload:
                overloaded.append(name)
                logger.warning(f"  ⚠️  Node {name} is overloaded (CPU: {cpu_percent:.1f}%, Memory: {mem_percent:.1f}%)")
            elif cpu_percent < cpu_underutil:
                underutilized.append(name)
                logger.info(f"  ✓ Node {name} is underutilized (CPU: {cpu_percent:.1f}%, Memory: {mem_percent:.1f}%)")
        else:
            logger.warning(f"  Node: {name} - Metrics not available")

    logger.info("Decision Engine Analysis:")
    if overloaded:
        logger.warning(f"  Overloaded nodes: {', '.join(overloaded)}")
        if underutilized:
            logger.info(f"  Underutilized nodes: {', '.join(underutilized)}")
            logger.info("  ✓ Recommendation: Migrate workloads from overloaded to underutilized nodes.")
        else:
            logger.warning("  ⚠️  No underutilized nodes available. Consider scaling up or optimizing workloads.")
    else:
        logger.info("  ✓ All nodes are balanced. No action needed.")
    
    return {"overloaded": overloaded, "underutilized": underutilized}

def check_cluster_balance_demo(config_data):
    """Check cluster balance using simulated demo node data. Can be called repeatedly."""
    thresholds = config_data["thresholds"]
    cpu_overload = thresholds["cpu_overloaded_percent"]
    cpu_underutil = thresholds["cpu_underutilized_percent"]

    overloaded = []
    underutilized = []

    logger.info("Node Resource Usage (DEMO MODE):")
    for node_name, cpu_percent, mem_percent in DEMO_NODES:
        logger.info(f"  Node: {node_name} | CPU: {cpu_percent}% | Memory: {mem_percent}%")

        if cpu_percent > cpu_overload:
            overloaded.append(node_name)
            logger.warning(f"  ⚠️  Node {node_name} is overloaded (CPU: {cpu_percent}%, Memory: {mem_percent}%)")
        elif cpu_percent < cpu_underutil:
            underutilized.append(node_name)
            logger.info(f"  ✓ Node {node_name} is underutilized (CPU: {cpu_percent}%, Memory: {mem_percent}%)")

    logger.info("Decision Engine Analysis:")
    if overloaded:
        logger.warning(f"  Overloaded nodes: {', '.join(overloaded)}")
        if underutilized:
            logger.info(f"  Underutilized nodes: {', '.join(underutilized)}")
            logger.info("  ✓ Recommendation: Migrate workloads from overloaded to underutilized nodes.")
        else:
            logger.warning("  ⚠️  No underutilized nodes available. Consider scaling up or optimizing workloads.")
    else:
        logger.info("  ✓ All nodes are balanced. No action needed.")

    return {"overloaded": overloaded, "underutilized": underutilized}

def main():
    """Main entry point with support for continuous monitoring."""
    parser = argparse.ArgumentParser(
        description="ClusterBalancer - Adaptive Workload Distribution System"
    )
    parser.add_argument(
        "--continuous", "-c",
        action="store_true",
        help="Enable continuous monitoring mode"
    )
    parser.add_argument(
        "--interval", "-i",
        type=int,
        default=None,
        help="Monitoring interval in seconds (overrides config)"
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to custom config file"
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Enable demo mode with simulated node data"
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
    
    # Determine monitoring mode
    continuous = args.continuous or config_data["monitoring"]["continuous_mode"]
    interval = args.interval or config_data["monitoring"]["check_interval_seconds"]
    
    logger.info("=" * 60)
    logger.info("ClusterBalancer – Adaptive Workload Distribution System")
    logger.info("=" * 60)
    logger.info(f"Mode: {'Continuous' if continuous else 'Single Check'}")
    if args.demo:
        logger.info("Demo Mode: ON (using simulated node data)")
    if continuous:
        logger.info(f"Check interval: {interval} seconds")
    logger.info("=" * 60)
    
    iteration = 0
    try:
        while True:
            iteration += 1
            if continuous:
                logger.info(f"\n[ITERATION {iteration}] {time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            if args.demo:
                result = check_cluster_balance_demo(config_data)
            else:
                result = check_cluster_balance(config_data)
            
            if not continuous or result is None:
                break
            
            logger.info(f"Next check in {interval} seconds...")
            time.sleep(interval)
    
    except KeyboardInterrupt:
        logger.info("\nMonitoring stopped by user.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()