from pathlib import Path

from mcp.server import MCPServer

NOTES_DIR = Path(__file__).parent / "notes"

mcp = MCPServer("Notes")


@mcp.tool()
def list_notes() -> list[str]:
    """List the names of all notes in the notes folder.

    Returns file names with the .md extension, sorted alphabetically,
    for example "shopping-list.md".
    """
    return sorted(path.name for path in NOTES_DIR.glob("*.md"))


if __name__ == "__main__":
    mcp.run()
