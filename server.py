#!/usr/bin/env python3
"""
Robot 2013 MCP Server — entry point.

Implements the MCP stdio transport manually (newline-delimited JSON-RPC 2.0)
to avoid dependency on a specific mcp SDK version while remaining compatible
with Claude Desktop and the MCP protocol.

Requirements:
    pip install mcp pywin32
"""
from __future__ import annotations

import sys
import json
import asyncio
import traceback
from typing import Any


# ── Tool registry ─────────────────────────────────────────────────
try:
    from src.tools.registry import TOOLS, HANDLERS
except ImportError as e:
    print(json.dumps({"error": f"Failed to import tools: {e}"}), file=sys.stderr)
    sys.exit(1)


SERVER_NAME    = "robot2013-mcp"
SERVER_VERSION = "1.0.0"
PROTO_VERSION  = "2025-03-26"


# ── I/O helpers ───────────────────────────────────────────────────

def send(msg: dict) -> None:
    sys.stdout.write(json.dumps(msg) + "\n")
    sys.stdout.flush()


def send_result(req_id: Any, result: Any) -> None:
    send({"jsonrpc": "2.0", "id": req_id, "result": result})


def send_error(req_id: Any, code: int, message: str) -> None:
    send({"jsonrpc": "2.0", "id": req_id,
          "error": {"code": code, "message": message}})


# ── Tool serialisation ────────────────────────────────────────────

def serialise_tools() -> list[dict]:
    """Convert mcp.types.Tool objects to plain dicts for JSON-RPC."""
    out = []
    for t in TOOLS:
        tool_dict: dict = {
            "name": t.name,
            "description": t.description or "",
        }
        # Handle different MCP SDK versions: inputSchema vs input_schema
        schema = getattr(t, "inputSchema", None) or getattr(t, "input_schema", None)
        if schema is not None:
            if hasattr(schema, "model_dump"):
                schema = schema.model_dump(exclude_none=True)
            elif hasattr(schema, "dict"):
                schema = schema.dict(exclude_none=True)
            tool_dict["inputSchema"] = schema
        else:
            tool_dict["inputSchema"] = {"type": "object", "properties": {}}
        out.append(tool_dict)
    return out


# ── Request dispatcher ────────────────────────────────────────────

async def dispatch(req: dict) -> None:
    req_id = req.get("id")
    method = req.get("method", "")
    params = req.get("params") or {}

    # Notifications — no response
    if method.startswith("notifications/") or method == "notifications/initialized":
        return

    # ── Protocol methods ──────────────────────────────────────────
    if method == "initialize":
        send_result(req_id, {
            "protocolVersion": params.get("protocolVersion", PROTO_VERSION),
            "capabilities": {"tools": {}, "resources": {}, "prompts": {}},
            "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
        })
        return

    if method == "tools/list":
        send_result(req_id, {"tools": serialise_tools()})
        return

    if method == "resources/list":
        send_result(req_id, {"resources": []})
        return

    if method == "prompts/list":
        send_result(req_id, {"prompts": []})
        return

    if method == "ping":
        send_result(req_id, {})
        return

    # ── Tool call ─────────────────────────────────────────────────
    if method == "tools/call":
        name = params.get("name")
        args = params.get("arguments") or {}

        if name not in HANDLERS:
            send_result(req_id, {
                "content": [{"type": "text", "text": f"Error: Unknown tool '{name}'"}],
                "isError": True,
            })
            return

        handler = HANDLERS[name]
        # Safety net: if a client serialised an array/object as a JSON string,
        # parse it back so handlers always receive the correct Python type.
        for _k, _v in list(args.items()):
            if isinstance(_v, str) and len(_v) > 1 and _v[0] in ("[", "{"):
                try:
                    args[_k] = json.loads(_v)
                except Exception:
                    pass
        try:
            data = await handler(args)  # type: ignore[operator]
            send_result(req_id, {
                "content": [{"type": "text", "text": json.dumps(data, default=str)}],
            })
        except Exception as exc:
            tb = traceback.format_exc()
            sys.stderr.write(f"[{name}] {tb}\n")
            sys.stderr.flush()
            send_result(req_id, {
                "content": [{"type": "text",
                              "text": f"Error in {name}: {exc}\n\nDetails:\n{tb}"}],
                "isError": True,
            })
        return

    # Unknown method
    if req_id is not None:
        send_error(req_id, -32601, f"Method not found: {method}")


# ── Main loop ─────────────────────────────────────────────────────

async def main() -> None:
    # CLI helper: list all tool names
    if "--list" in sys.argv:
        for t in TOOLS:
            print(t.name)
        return

    # CLI helper: dump tool schemas
    if "--dump" in sys.argv:
        print(json.dumps(serialise_tools(), indent=2))
        return

    sys.stderr.write(
        f"[{SERVER_NAME} v{SERVER_VERSION}] "
        f"Started — {len(TOOLS)} tools available\n"
    )
    sys.stderr.flush()

    loop = asyncio.get_event_loop()
    queue: asyncio.Queue[str | None] = asyncio.Queue()

    def _read_stdin() -> None:
        """Read stdin lines in a background thread (Windows-safe)."""
        try:
            stdin_bin = sys.stdin.buffer
            while True:
                line_bytes = stdin_bin.readline()
                if not line_bytes:
                    break
                loop.call_soon_threadsafe(queue.put_nowait,
                                          line_bytes.decode("utf-8", errors="replace"))
        except Exception:
            pass
        finally:
            loop.call_soon_threadsafe(queue.put_nowait, None)

    import threading
    threading.Thread(target=_read_stdin, daemon=True).start()

    while True:
        line = await queue.get()
        if line is None:
            break

        line = line.strip()
        if not line:
            continue

        try:
            req = json.loads(line)
        except json.JSONDecodeError as e:
            sys.stderr.write(f"JSON parse error: {e}\n")
            continue

        try:
            await dispatch(req)
        except Exception as e:
            sys.stderr.write(f"Dispatch error: {e}\n{traceback.format_exc()}\n")


if __name__ == "__main__":
    asyncio.run(main())
