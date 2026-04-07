import os
from dotenv import load_dotenv
from langchain_core.tools import tool
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

load_dotenv()


def _db_url() -> str:
    return (
        f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    )


@tool
async def query_database(sql: str) -> str:
    """
    Execute a read-only SQL query against the PostgreSQL database.

    Args:
        sql: SQL query to execute.

    Returns:
        Query results as text.
    """
    server_params = StdioServerParameters(
        command="mcp-server-postgres",
        args=[_db_url()],
    )
    async with stdio_client(server_params, errlog=open(os.devnull, "w")) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool("query", {"sql": sql})
            return str(result.content)


tools = [query_database]
