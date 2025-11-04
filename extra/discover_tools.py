#!/usr/bin/env python3
"""
discover_tools.py
────────────────────────────────────────────────────────────────────
**Purpose**  
Connect to a running FastMCP server and print a one-line summary
(name + description) of every tool the server currently exposes.

Why you might run this
----------------------
* Quick sanity-check that your MCP server is live.
* See the exact spelling of tool names before calling them.
* Share a lightweight script with teammates who don’t know FastMCP yet.

Assumptions
-----------
* The server is reachable at `http://127.0.0.1:8000/mcp/`.
* No authentication is required (default local dev setup).
"""

import asyncio                    # built-in: run asynchronous code
from fastmcp import Client        # official async JSON-RPC wrapper

# ╔════════════════════════════════════════════════════════════════╗
# 1.  Async entry-point                                           ║
# ╚════════════════════════════════════════════════════════════════╝
async def main() -> None:
    """
    Open an async connection to the MCP endpoint, retrieve the list of
    tools, and print `name: description` for each.
    """
    # `Client` is an asynchronous context-manager: it opens the HTTP
    # connection on entry and closes it on exit.
    async with Client("http://127.0.0.1:8000/mcp/") as mcp:

        # `list_tools()` sends a JSON-RPC request {method:"tools/list"}
        # and returns a list of Tool objects (attributes: name, description…)
        tools = await mcp.list_tools()

        # Print a simple catalogue
        for tool in tools:
            print(f"{tool.name}: {tool.description}")

# ╔════════════════════════════════════════════════════════════════╗
# 2.  Synchronous bootstrap                                       ║
# ╚════════════════════════════════════════════════════════════════╝
# asyncio.run() creates an event-loop, executes `main()`, and
# automatically shuts everything down when `main()` finishes.
if __name__ == "__main__":
    asyncio.run(main())
