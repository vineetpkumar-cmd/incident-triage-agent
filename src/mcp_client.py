import asyncio
import sys
from pathlib import Path

from langchain_mcp_adapters.client import (
    MultiServerMCPClient,
)


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SERVERS_DIR = PROJECT_ROOT / "servers"


def create_mcp_client() -> MultiServerMCPClient:
    """Configure clients for all three local MCP servers."""
    return MultiServerMCPClient(
        {
            "servicenow": {
                "transport": "stdio",
                "command": sys.executable,
                "args": [
                    str(SERVERS_DIR / "servicenow_server.py")
                ],
            },
            "jira": {
                "transport": "stdio",
                "command": sys.executable,
                "args": [
                    str(SERVERS_DIR / "jira_server.py")
                ],
            },
            "outlook": {
                "transport": "stdio",
                "command": sys.executable,
                "args": [
                    str(SERVERS_DIR / "outlook_server.py")
                ],
            },
        }
    )


async def get_mcp_tools():
    """Load tools from every configured MCP server."""
    client = create_mcp_client()
    return await client.get_tools()


async def main() -> None:
    """Display all tools available to LangChain."""
    tools = await get_mcp_tools()

    print("\nAvailable MCP tools:")

    for tool in tools:
        print(f"- {tool.name}")

    print(f"\nTotal: {len(tools)} tools")


if __name__ == "__main__":
    asyncio.run(main())