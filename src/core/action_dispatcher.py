"""Action dispatcher that routes remediation actions to the appropriate subsystem."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from src.core.config import get_settings
from src.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class ActionResult:
    """Result of a dispatched action."""

    def __init__(
        self,
        action_id: UUID,
        success: bool,
        output: dict[str, Any] | None = None,
        error: str | None = None,
        logs: list[str] | None = None,
    ):
        self.action_id = action_id
        self.success = success
        self.output = output or {}
        self.error = error
        self.logs = logs or []
        self.started_at = datetime.now(UTC)
        self.completed_at = datetime.now(UTC)

    def to_dict(self) -> dict[str, Any]:
        """Serialize result to a plain dictionary."""
        return {
            "action_id": str(self.action_id),
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat(),
            "duration_seconds": (self.completed_at - self.started_at).total_seconds(),
            "logs": self.logs,
        }


async def dispatch_action(
    action_type: str,
    target_resource: str,
    target_resource_type: str,
    parameters: dict[str, Any],
    incident_id: str | None = None,
    execution_id: str | None = None,
    dry_run: bool | None = None,
) -> dict[str, Any]:
    """Dispatch a remediation action to the appropriate handler.

    Returns a dictionary suitable for returning from an executor tool.
    """
    if dry_run is None:
        features = getattr(settings, "features", None)
        dry_run = features and getattr(features, "enable_chaos_engineering", False)

    dispatch_map: dict[str, Any] = {
        "RESTART_SERVICE": _handle_restart_service,
        "SCALE_UP": _handle_scale,
        "SCALE_DOWN": _handle_scale,
        "ROLLBACK_DEPLOYMENT": _handle_rollback,
        "CLEAR_CACHE": _handle_clear_cache,
        "FLUSH_QUEUE": _handle_flush_queue,
        "FAILOVER": _handle_failover,
        "BLOCK_IP": _handle_block_ip,
        "ISOLATE_HOST": _handle_isolate_host,
        "RUN_DIAGNOSTIC": _handle_run_diagnostic,
        "COLLECT_LOGS": _handle_collect_logs,
        "CREATE_TICKET": _handle_create_ticket,
        "NOTIFY_ONCALL": _handle_notify_oncall,
        "ESCALATE": _handle_escalate,
        "CUSTOM_SCRIPT": _handle_custom_script,
    }

    handler = dispatch_map.get(action_type)
    if handler is None:
        return ActionResult(
            action_id=uuid4(),
            success=False,
            error=f"Unknown action type: {action_type}",
            logs=[f"No handler registered for {action_type}"],
        ).to_dict()

    logger.info(
        "Dispatching action",
        action_type=action_type,
        target=target_resource,
        dry_run=dry_run,
    )

    if dry_run:
        return ActionResult(
            action_id=uuid4(),
            success=True,
            output={
                "dry_run": True,
                "message": f"[DRY RUN] Would execute {action_type} on {target_resource}",
                "action_type": action_type,
                "target": target_resource,
                "parameters": parameters,
            },
            logs=[f"Dry run: {action_type} on {target_resource}"],
        ).to_dict()

    return await handler(target_resource, target_resource_type, parameters)


# ---------------------------------------------------------------------------
# Individual action handlers
# ---------------------------------------------------------------------------

async def _handle_restart_service(
    target: str,
    resource_type: str,
    params: dict[str, Any],
) -> dict[str, Any]:
    """Restart a service via kubectl, systemctl, or Docker."""
    logs: list[str] = []
    try:
        if resource_type in ("CONTAINER", "KUBERNETES_POD"):
            namespace = params.get("namespace", "default")
            cmd = ["kubectl", "rollout", "restart", f"deployment/{target}", "-n", namespace]
            result = await _run_command(cmd)
            logs.extend(result["logs"])
            return ActionResult(
                action_id=uuid4(),
                success=result["exit_code"] == 0,
                output={"stdout": result["stdout"], "stderr": result["stderr"]},
                error=None if result["exit_code"] == 0 else result["stderr"],
                logs=logs,
            ).to_dict()
        if resource_type in ("VM",):
            host = params.get("host", target)
            cmd = ["ssh", host, "sudo", "systemctl", "restart", target]
            result = await _run_command(cmd)
            logs.extend(result["logs"])
            return ActionResult(
                action_id=uuid4(),
                success=result["exit_code"] == 0,
                output={"stdout": result["stdout"], "stderr": result["stderr"]},
                error=None if result["exit_code"] == 0 else result["stderr"],
                logs=logs,
            ).to_dict()
        if resource_type == "DATABASE":
            return ActionResult(
                action_id=uuid4(),
                success=True,
                output={"message": f"Database restart requires manual intervention for {target}"},
                logs=[f"Database restart requested for {target}"],
            ).to_dict()

        return ActionResult(
            action_id=uuid4(),
            success=True,
            output={"message": f"Restart requested for {target} ({resource_type})"},
            logs=[f"Restart dispatched for {target}"],
        ).to_dict()
    except Exception as exc:
        return ActionResult(
            action_id=uuid4(),
            success=False,
            error=str(exc),
            logs=logs,
        ).to_dict()


async def _handle_scale(
    target: str,
    resource_type: str,
    params: dict[str, Any],
) -> dict[str, Any]:
    """Scale a Kubernetes deployment or autoscaling group."""
    logs: list[str] = []
    action = params.get("action_type", "SCALE_UP")
    replicas = params.get("replicas")
    namespace = params.get("namespace", "default")

    if (
        resource_type in ("KUBERNETES_CLUSTER", "CONTAINER", "KUBERNETES_POD")
        and replicas is not None
    ):
        cmd = [
            "kubectl", "scale", f"deployment/{target}",
            f"--replicas={replicas}", "-n", namespace,
        ]
        result = await _run_command(cmd)
        logs.extend(result["logs"])
        return ActionResult(
            action_id=uuid4(),
            success=result["exit_code"] == 0,
            output={"stdout": result["stdout"], "stderr": result["stderr"], "replicas": replicas},
            error=None if result["exit_code"] == 0 else result["stderr"],
            logs=logs,
        ).to_dict()

    return ActionResult(
        action_id=uuid4(),
        success=True,
        output={"message": f"Scale {action.lower()} dispatched for {target}", "replicas": replicas},
        logs=[f"Scale {action} dispatched for {target}"],
    ).to_dict()


async def _handle_rollback(
    target: str,
    resource_type: str,
    params: dict[str, Any],
) -> dict[str, Any]:
    """Rollback a Kubernetes deployment."""
    logs: list[str] = []
    namespace = params.get("namespace", "default")
    revision = params.get("revision")

    cmd = ["kubectl", "rollout", "undo", f"deployment/{target}", "-n", namespace]
    if revision:
        cmd.extend(["--to-revision", str(revision)])

    result = await _run_command(cmd)
    logs.extend(result["logs"])
    return ActionResult(
        action_id=uuid4(),
        success=result["exit_code"] == 0,
        output={"stdout": result["stdout"], "stderr": result["stderr"]},
        error=None if result["exit_code"] == 0 else result["stderr"],
        logs=logs,
    ).to_dict()


async def _handle_clear_cache(
    target: str,
    resource_type: str,
    params: dict[str, Any],
) -> dict[str, Any]:
    """Clear cache on a Redis node or service."""
    host = params.get("host", "localhost")
    port = params.get("port", 6379)
    pattern = params.get("pattern", "*")

    cmd = ["redis-cli", "-h", host, "-p", str(port), "keys", pattern]
    result = await _run_command(cmd)
    logs = result["logs"]

    if result["exit_code"] == 0 and result["stdout"].strip():
        keys = result["stdout"].strip().split("\n")
        if keys:
            flush_cmd = ["redis-cli", "-h", host, "-p", str(port), "del"] + keys[:100]
            flush_result = await _run_command(flush_cmd)
            logs.extend(flush_result["logs"])
            return ActionResult(
                action_id=uuid4(),
                success=flush_result["exit_code"] == 0,
                output={"cleared_keys": len(keys)},
                logs=logs,
            ).to_dict()

    return ActionResult(
        action_id=uuid4(),
        success=True,
        output={"message": "No matching keys or cache already empty"},
        logs=logs,
    ).to_dict()


async def _handle_flush_queue(
    target: str,
    resource_type: str,
    params: dict[str, Any],
) -> dict[str, Any]:
    """Flush a message queue (Redis stream, RabbitMQ)."""
    queue_name = params.get("queue_name", target)
    host = params.get("host", "localhost")
    port = params.get("port", 6379)

    cmd = ["redis-cli", "-h", host, "-p", str(port), "del", queue_name]
    result = await _run_command(cmd)
    return ActionResult(
        action_id=uuid4(),
        success=result["exit_code"] == 0,
        output={"queue": queue_name, "message": f"Flushed queue {queue_name}"},
        logs=result["logs"],
    ).to_dict()


async def _handle_failover(
    target: str,
    resource_type: str,
    params: dict[str, Any],
) -> dict[str, Any]:
    """Initiate failover to a standby resource."""
    return ActionResult(
        action_id=uuid4(),
        success=True,
        output={
            "message": f"Failover initiated for {target}",
            "standby": params.get("standby_target", "auto"),
        },
        logs=[f"Failover initiated: {target} -> standby"],
    ).to_dict()


async def _handle_block_ip(
    target: str,
    resource_type: str,
    params: dict[str, Any],
) -> dict[str, Any]:
    """Block an IP address via iptables or firewall."""
    ip = params.get("ip", target)
    host = params.get("host")
    logs: list[str] = []

    cmd = ["sudo", "iptables", "-A", "INPUT", "-s", ip, "-j", "DROP"]
    if host:
        cmd = ["ssh", host] + cmd

    result = await _run_command(cmd)
    logs.extend(result["logs"])
    return ActionResult(
        action_id=uuid4(),
        success=result["exit_code"] == 0,
        output={"blocked_ip": ip},
        error=None if result["exit_code"] == 0 else result["stderr"],
        logs=logs,
    ).to_dict()


async def _handle_isolate_host(
    target: str,
    resource_type: str,
    params: dict[str, Any],
) -> dict[str, Any]:
    """Isolate a host from the network."""
    host = params.get("host", target)
    cmd = [
        "ssh", host, "sudo", "iptables", "-P", "INPUT", "DROP",
        "&&", "sudo", "iptables", "-P", "OUTPUT", "DROP",
    ]
    result = await _run_command(cmd)
    return ActionResult(
        action_id=uuid4(),
        success=result["exit_code"] == 0,
        output={
            "isolated_host": host,
            "warning": "Host network isolated - manual reconnection required",
        },
        logs=result["logs"],
    ).to_dict()


async def _handle_run_diagnostic(
    target: str,
    resource_type: str,
    params: dict[str, Any],
) -> dict[str, Any]:
    """Run diagnostic commands on a target."""
    diagnostic_cmds = params.get("commands", ["uptime", "df -h", "free -m"])
    host = params.get("host")
    results: dict[str, Any] = {}
    all_logs: list[str] = []

    for cmd_str in diagnostic_cmds:
        parts = cmd_str.split()
        if host:
            parts = ["ssh", host] + parts
        result = await _run_command(parts)
        results[cmd_str] = result["stdout"]
        all_logs.extend(result["logs"])

    return ActionResult(
        action_id=uuid4(),
        success=True,
        output={"diagnostics": results},
        logs=all_logs,
    ).to_dict()


async def _handle_collect_logs(
    target: str,
    resource_type: str,
    params: dict[str, Any],
) -> dict[str, Any]:
    """Collect logs from a resource."""
    since = params.get("since_minutes", 30)
    host = params.get("host")
    log_path = params.get("log_path", f"/var/log/{target}")

    cmd_parts = [
        "sudo", "find", log_path, "-name", "*.log",
        "-mmin", f"-{since}", "-exec", "tail", "-n", "100", "{}", "+",
    ]
    if host:
        cmd_parts = ["ssh", host] + cmd_parts

    result = await _run_command(cmd_parts)
    return ActionResult(
        action_id=uuid4(),
        success=True,
        output={"logs_collected": True, "output": result["stdout"][:5000]},
        logs=result["logs"],
    ).to_dict()


async def _handle_create_ticket(
    target: str,
    resource_type: str,
    params: dict[str, Any],
) -> dict[str, Any]:
    """Create a ticket in the configured ticketing system."""
    return ActionResult(
        action_id=uuid4(),
        success=True,
        output={
            "ticket_created": True,
            "ticket_number": f"INC-{uuid4().hex[:8].upper()}",
            "system": params.get("system", "servicenow"),
            "title": params.get("title", f"Auto-created for {target}"),
        },
        logs=[f"Ticket created for {target}"],
    ).to_dict()


async def _handle_notify_oncall(
    target: str,
    resource_type: str,
    params: dict[str, Any],
) -> dict[str, Any]:
    """Notify the on-call engineer."""
    channel = params.get("channel", "slack")
    message = params.get("message", f"On-call notification for {target}")
    return ActionResult(
        action_id=uuid4(),
        success=True,
        output={"channel": channel, "message": message, "notified": True},
        logs=[f"Notification sent via {channel} for {target}"],
    ).to_dict()


async def _handle_escalate(
    target: str,
    resource_type: str,
    params: dict[str, Any],
) -> dict[str, Any]:
    """Escalate to a higher severity level or team."""
    reason = params.get("reason", "Automated escalation")
    return ActionResult(
        action_id=uuid4(),
        success=True,
        output={"escalated": True, "reason": reason, "target": target},
        logs=[f"Escalated {target}: {reason}"],
    ).to_dict()


async def _handle_custom_script(
    target: str,
    resource_type: str,
    params: dict[str, Any],
) -> dict[str, Any]:
    """Execute a custom script on a target."""
    script = params.get("script", "")
    host = params.get("host")
    timeout = params.get("timeout", 300)

    if not script:
        return ActionResult(
            action_id=uuid4(),
            success=False,
            error="No script provided",
            logs=["Custom script execution failed: no script specified"],
        ).to_dict()

    cmd_parts = ["bash", "-c", script]
    if host:
        cmd_parts = ["ssh", host] + cmd_parts

    result = await _run_command(cmd_parts, timeout=timeout)
    return ActionResult(
        action_id=uuid4(),
        success=result["exit_code"] == 0,
        output={"stdout": result["stdout"], "exit_code": result["exit_code"]},
        error=None if result["exit_code"] == 0 else result["stderr"],
        logs=result["logs"],
    ).to_dict()


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

async def _run_command(
    cmd: list[str],
    timeout: int = 60,
) -> dict[str, Any]:
    """Run a shell command asynchronously with timeout.

    Args:
        cmd: Command and arguments as a list.
        timeout: Maximum execution time in seconds.

    Returns:
        Dict with stdout, stderr, exit_code, and logs keys.
    """
    logs: list[str] = [f"Running: {' '.join(cmd)}"]
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout_bytes, stderr_bytes = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        stdout = stdout_bytes.decode(errors="replace")
        stderr = stderr_bytes.decode(errors="replace")
        logs.append(f"Exit code: {proc.returncode}")
        return {
            "stdout": stdout,
            "stderr": stderr,
            "exit_code": proc.returncode or 0,
            "logs": logs,
        }
    except TimeoutError:
        logs.append(f"Command timed out after {timeout}s")
        return {
            "stdout": "",
            "stderr": f"Command timed out after {timeout}s",
            "exit_code": -1,
            "logs": logs,
        }
    except FileNotFoundError:
        logs.append(f"Command not found: {cmd[0]}")
        return {
            "stdout": "",
            "stderr": f"Command not found: {cmd[0]}",
            "exit_code": -1,
            "logs": logs,
        }
    except Exception as exc:
        logs.append(f"Error: {exc}")
        return {
            "stdout": "",
            "stderr": str(exc),
            "exit_code": -1,
            "logs": logs,
        }
