from pathlib import Path

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

NOTES_DIR = Path(__file__).parent / "notes"

mcp = MCPServer("Notes")


@mcp.tool()
def list_notes() -> list[str]:
    """List the names of all notes (Markdown files) in the notes folder."""
    return sorted(path.name for path in NOTES_DIR.glob("*.md"))


@mcp.tool()
def read_note(name: str) -> str:
    """Read a note (Markdown file) in the notes folder."""
    path = NOTES_DIR / name
    if not path.is_file():
        raise ToolError(f"Note '{name}' not found.")
    return path.read_text(encoding="utf-8")


if __name__ == "__main__":
    mcp.run()
