#!/usr/bin/env python3
"""
Local Development Orchestrator for Citizen Services Portal.

Starts all services locally for rapid development:
- MCP Servers (LADBS, LADWP, LASAN, CSP)
- CSP Agent (uses Azure OpenAI, local MCP servers)
- Web Application

Usage:
    python scripts/dev-local.py              # Start all services
    python scripts/dev-local.py --mcp-only   # Start only MCP servers
    python scripts/dev-local.py --web-only   # Start only web app

Requirements:
    - Azure CLI logged in: `az login`
    - azd environment configured: `azd env select <env>`
"""

import argparse
import os
import signal
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# Project root
PROJECT_ROOT = Path(__file__).parent.parent


def get_azd_env_values() -> dict[str, str]:
    """Load environment values from azd."""
    try:
        result = subprocess.run(
            ["azd", "env", "get-values"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print("⚠️  Warning: Could not load azd env values")
            return {}
        
        env = {}
        for line in result.stdout.strip().split("\n"):
            if "=" in line:
                key, value = line.split("=", 1)
                # Remove surrounding quotes
                env[key] = value.strip('"').strip("'")
        return env
    except FileNotFoundError:
        print("⚠️  Warning: azd not found, agent may not work")
        return {}


@dataclass
class ServiceConfig:
    """Configuration for a service."""
    name: str
    path: Path
    command: list[str]
    port: int
    env: dict[str, str] = field(default_factory=dict)
    health_endpoint: Optional[str] = None
    depends_on: list[str] | None = None


# Service configurations
MCP_SERVERS = [
    ServiceConfig(
        name="mcp-ladbs",
        path=PROJECT_ROOT / "src" / "mcp-servers" / "ladbs",
        command=["uv", "run", "python", "mcp_server_ladbs.py"],
        port=8001,
        env={"PORT": "8001"},
        health_endpoint="/health",
    ),
    ServiceConfig(
        name="mcp-ladwp",
        path=PROJECT_ROOT / "src" / "mcp-servers" / "ladwp",
        command=["uv", "run", "python", "mcp_server_ladwp.py"],
        port=8002,
        env={"PORT": "8002"},
        health_endpoint="/health",
    ),
    ServiceConfig(
        name="mcp-lasan",
        path=PROJECT_ROOT / "src" / "mcp-servers" / "lasan",
        command=["uv", "run", "python", "mcp_server_lasan.py"],
        port=8003,
        env={"PORT": "8003"},
        health_endpoint="/health",
    ),
    ServiceConfig(
        name="mcp-csp",
        path=PROJECT_ROOT / "src" / "mcp-servers" / "csp",
        command=["uv", "run", "python", "mcp_server_csp.py"],
        port=8004,
        env={"PORT": "8004"},
        health_endpoint="/health",
    ),
]


def get_csp_agent_config(azd_env: dict[str, str]) -> ServiceConfig:
    """Create CSP Agent config with Azure credentials from azd."""
    return ServiceConfig(
        name="csp-agent",
        path=PROJECT_ROOT / "src" / "agents" / "csp-agent",
        command=["uv", "run", "python", "main.py"],
        port=8088,  # Agent framework default port
        env={
            # Use local MCP servers (streamable-http transport)
            "MCP_LADBS_URL": "http://localhost:8001/mcp",
            "MCP_LADWP_URL": "http://localhost:8002/mcp",
            "MCP_LASAN_URL": "http://localhost:8003/mcp",
            "MCP_CSP_URL": "http://localhost:8004/mcp",
            # Azure OpenAI from azd
            "AZURE_OPENAI_ENDPOINT": azd_env.get("AZURE_OPENAI_ENDPOINT", ""),
            "AZURE_OPENAI_CHAT_DEPLOYMENT_NAME": azd_env.get("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME", "gpt-4.1"),
            # Azure AI Foundry project (required for agent runtime)
            "AZURE_AI_PROJECT_ENDPOINT": azd_env.get("AZURE_AI_PROJECT_ENDPOINT", ""),
            "AGENT_PROJECT_RESOURCE_ID": azd_env.get("AZURE_AI_PROJECT_ID", ""),
            # Application Insights (optional but expected)
            "APPLICATIONINSIGHTS_CONNECTION_STRING": azd_env.get("applicationInsightsConnectionString", ""),
            # OpenTelemetry for local tracing with Aspire Dashboard
            # Start Aspire: make aspire-start (or docker run -d -p 18888:18888 -p 4317:18889 -e DOTNET_DASHBOARD_UNSECURED_ALLOW_ANONYMOUS=true mcr.microsoft.com/dotnet/aspire-dashboard:9.0)
            # View traces: http://localhost:18888
            "ENABLE_INSTRUMENTATION": "true",
            "OTEL_EXPORTER_OTLP_ENDPOINT": os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317"),
            "OTEL_SERVICE_NAME": "csp-agent",
        },
        health_endpoint="/health",
        depends_on=["mcp-ladbs", "mcp-ladwp", "mcp-lasan", "mcp-csp"],
    )


def get_web_app_config(azd_env: dict[str, str]) -> ServiceConfig:
    """Create Web App config with Azure credentials from azd."""
    return ServiceConfig(
        name="web-app",
        path=PROJECT_ROOT / "src" / "web-app",
        command=["uv", "run", "python", "main.py"],
        port=8080,
        env={
            "DEBUG": "true",
            "USE_MOCK_AUTH": "true",
            "CSP_AGENT_URL": "http://localhost:8088",
            # CosmosDB for user/project persistence
            "COSMOS_ENDPOINT": azd_env.get("cosmosDbEndpoint", ""),
            "COSMOS_DATABASE": "csp",
        },
        health_endpoint="/",
    )


class ServiceManager:
    """Manages lifecycle of local development services."""

    def __init__(self):
        self.processes: dict[str, subprocess.Popen] = {}
        self.stopping = False

    def start_service(self, config: ServiceConfig, sync_deps: bool = True) -> subprocess.Popen:
        """Start a single service."""
        print(f"🚀 Starting {config.name} on port {config.port}...")
        
        # Ensure dependencies are installed
        if sync_deps and (config.path / "pyproject.toml").exists():
            print(f"   📦 Syncing dependencies for {config.name}...")
            subprocess.run(
                ["uv", "sync"],
                cwd=config.path,
                capture_output=True,
            )
        
        # Prepare environment - clear VIRTUAL_ENV to avoid uv warnings
        env = os.environ.copy()
        env.pop('VIRTUAL_ENV', None)
        env.update(config.env)
        
        # Start the process
        process = subprocess.Popen(
            config.command,
            cwd=config.path,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        
        self.processes[config.name] = process
        return process

    def wait_for_port(self, port: int, timeout: float = 30.0) -> bool:
        """Wait for a port to become available."""
        import socket
        start = time.time()
        while time.time() - start < timeout:
            try:
                with socket.create_connection(("localhost", port), timeout=1):
                    return True
            except (ConnectionRefusedError, OSError):
                time.sleep(0.5)
        return False

    def start_mcp_servers(self) -> bool:
        """Start all MCP servers in parallel."""
        print("\n" + "=" * 60)
        print("📡 Starting MCP Servers")
        print("=" * 60)
        
        for config in MCP_SERVERS:
            self.start_service(config)
        
        # Wait for all MCP servers to be ready
        print("\n⏳ Waiting for MCP servers to be ready...")
        all_ready = True
        for config in MCP_SERVERS:
            if self.wait_for_port(config.port, timeout=30):
                print(f"   ✅ {config.name} ready on port {config.port}")
            else:
                print(f"   ❌ {config.name} failed to start on port {config.port}")
                all_ready = False
        
        return all_ready

    def start_agent(self, agent_config: ServiceConfig) -> bool:
        """Start the CSP Agent."""
        print("\n" + "=" * 60)
        print("🤖 Starting CSP Agent")
        print("=" * 60)
        
        self.start_service(agent_config, sync_deps=False)
        
        if self.wait_for_port(agent_config.port, timeout=30):
            print(f"   ✅ csp-agent ready on port {agent_config.port}")
            return True
        else:
            print(f"   ❌ csp-agent failed to start on port {agent_config.port}")
            return False

    def start_web_app(self, web_app_config: ServiceConfig) -> bool:
        """Start the web application."""
        print("\n" + "=" * 60)
        print("🌐 Starting Web Application")
        print("=" * 60)
        
        self.start_service(web_app_config)
        
        if self.wait_for_port(web_app_config.port, timeout=30):
            print(f"   ✅ web-app ready on port {web_app_config.port}")
            return True
        else:
            print(f"   ❌ web-app failed to start on port {web_app_config.port}")
            return False

    def stream_logs(self):
        """Stream logs from all running processes."""
        import select
        
        print("\n" + "=" * 60)
        print("📋 Streaming Logs (Ctrl+C to stop)")
        print("=" * 60 + "\n")
        
        # Create a mapping of file descriptors to service names
        fd_to_name = {}
        for name, process in self.processes.items():
            if process.stdout:
                fd_to_name[process.stdout.fileno()] = name
        
        while not self.stopping and self.processes:
            # Check for output from all processes
            readable = []
            for name, process in list(self.processes.items()):
                if process.poll() is not None:
                    print(f"⚠️  {name} exited with code {process.returncode}")
                    del self.processes[name]
                    continue
                if process.stdout:
                    readable.append(process.stdout)
            
            if not readable:
                time.sleep(0.1)
                continue
            
            try:
                ready, _, _ = select.select(readable, [], [], 0.1)
                for stream in ready:
                    line = stream.readline()
                    if line:
                        name = fd_to_name.get(stream.fileno(), "unknown")
                        # Color-code by service type
                        if "mcp-" in name:
                            prefix = f"\033[36m[{name}]\033[0m"  # Cyan
                        elif "agent" in name:
                            prefix = f"\033[33m[{name}]\033[0m"  # Yellow
                        else:
                            prefix = f"\033[32m[{name}]\033[0m"  # Green
                        print(f"{prefix} {line.rstrip()}")
            except (ValueError, OSError):
                # Handle closed file descriptors
                pass

    def stop_all(self):
        """Stop all running services."""
        self.stopping = True
        print("\n\n🛑 Stopping all services...")
        
        for name, process in self.processes.items():
            print(f"   Stopping {name}...")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
        
        self.processes.clear()
        print("✅ All services stopped")


def main():
    parser = argparse.ArgumentParser(
        description="Local development orchestrator for Citizen Services Portal"
    )
    parser.add_argument(
        "--mcp-only",
        action="store_true",
        help="Start only MCP servers",
    )
    parser.add_argument(
        "--web-only",
        action="store_true",
        help="Start only the web application",
    )
    parser.add_argument(
        "--no-logs",
        action="store_true",
        help="Don't stream logs (services run in background)",
    )
    
    args = parser.parse_args()
    
    # Load Azure credentials from azd
    print("\n📦 Loading Azure credentials from azd...")
    azd_env = get_azd_env_values()
    
    if not azd_env.get("AZURE_OPENAI_ENDPOINT"):
        print("⚠️  Warning: AZURE_OPENAI_ENDPOINT not found in azd env")
        print("   Run 'azd env select <env>' and ensure infrastructure is deployed")
    else:
        print(f"   ✅ Found Azure OpenAI: {azd_env['AZURE_OPENAI_ENDPOINT']}")
    
    # Create agent config with Azure credentials
    agent_config = get_csp_agent_config(azd_env)
    
    # Create web app config with Azure credentials
    web_app_config = get_web_app_config(azd_env)
    
    manager = ServiceManager()
    
    # Handle Ctrl+C gracefully
    def signal_handler(sig, frame):
        manager.stop_all()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("\n" + "=" * 60)
    print("🏛️  Citizen Services Portal - Local Development")
    print("=" * 60)
    
    try:
        if args.web_only:
            # Only start web app
            manager.start_web_app(web_app_config)
        elif args.mcp_only:
            # Only start MCP servers
            manager.start_mcp_servers()
        else:
            # Default: Start everything (MCP + Agent + Web)
            manager.start_mcp_servers()
            manager.start_agent(agent_config)
            manager.start_web_app(web_app_config)
        
        print("\n" + "=" * 60)
        print("✨ All services started!")
        print("=" * 60)
        print("\n📍 Service URLs:")
        for name, process in manager.processes.items():
            if "mcp-ladbs" in name:
                print("   • LADBS MCP:     http://localhost:8001")
            elif "mcp-ladwp" in name:
                print("   • LADWP MCP:     http://localhost:8002")
            elif "mcp-lasan" in name:
                print("   • LASAN MCP:     http://localhost:8003")
            elif "mcp-csp" in name:
                print("   • CSP MCP:       http://localhost:8004")
            elif "csp-agent" in name:
                print("   • CSP Agent:     http://localhost:8088")
            elif "web-app" in name:
                print("   • Web App:       http://localhost:8080")
        print()
        
        if not args.no_logs:
            manager.stream_logs()
        else:
            print("Services running in background. Press Ctrl+C to stop.")
            signal.pause()
            
    except KeyboardInterrupt:
        pass
    finally:
        manager.stop_all()


if __name__ == "__main__":
    main()
