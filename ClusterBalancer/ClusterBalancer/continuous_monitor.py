#!/usr/bin/env python3
"""
ClusterBalancer - Continuous Monitoring Daemon
Runs monitoring continuously with configurable interval and logging
"""

import subprocess
import sys
import argparse
import time
from pathlib import Path
from datetime import datetime

def run_monitoring(interval=30, log_file="monitor_log.txt", verbose=True):
    """Run continuous monitoring with logging"""
    
    project_path = Path(__file__).parent
    
    if verbose:
        print("=" * 50)
        print("ClusterBalancer - Continuous Monitoring Daemon")
        print("=" * 50)
        print(f"\n[Configuration]")
        print(f"  Project: {project_path}")
        print(f"  Interval: {interval} seconds")
        print(f"  Log file: {log_file}")
        print(f"  Verbose: {verbose}")
        print(f"\n[Status] Press Ctrl+C to stop monitoring\n")
    
    # Create log file and add startup message
    log_path = project_path / log_file
    with open(log_path, 'a') as f:
        f.write(f"\n{'='*60}\n")
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Monitoring started\n")
        f.write(f"{'='*60}\n")
    
    try:
        # Run monitoring script
        cmd = [
            sys.executable,
            str(project_path / "monitoring" / "monitor.py"),
            "--continuous",
            "--interval", str(interval)
        ]
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        # Read output line by line
        for line in process.stdout:
            # Print to console if verbose
            if verbose:
                print(line, end='')
            
            # Write to log file
            with open(log_path, 'a') as f:
                f.write(line)
        
        # Wait for process to complete
        process.wait()
        
    except KeyboardInterrupt:
        if verbose:
            print("\n\n⏸️  Monitoring stopped by user")
        process.terminate()
        process.wait()
    except Exception as e:
        if verbose:
            print(f"\n❌ Error: {e}")
        with open(log_path, 'a') as f:
            f.write(f"\n[ERROR] {e}\n")
    finally:
        # Log stop time
        with open(log_path, 'a') as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Monitoring stopped\n")
        
        if verbose:
            print(f"\n✅ Logs saved to: {log_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="ClusterBalancer - Continuous Monitoring Daemon"
    )
    parser.add_argument(
        "--interval", "-i",
        type=int,
        default=30,
        help="Check interval in seconds (default: 30)"
    )
    parser.add_argument(
        "--log", "-l",
        default="monitor_log.txt",
        help="Log file path (default: monitor_log.txt)"
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress console output (log only)"
    )
    
    args = parser.parse_args()
    
    run_monitoring(
        interval=args.interval,
        log_file=args.log,
        verbose=not args.quiet
    )
