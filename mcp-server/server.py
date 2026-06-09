import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

sys.path.insert(0, str(Path(__file__).resolve().parent))

from tools import add_text_document, list_knowledge_bases, search_knowledge_base


mcp = FastMCP("kk-knowledge")


mcp.tool()(search_knowledge_base)
mcp.tool()(list_knowledge_bases)
mcp.tool()(add_text_document)


if __name__ == "__main__":
    mcp.run()
