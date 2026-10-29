from pathlib import Path

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

NOTES_DIR = Path(__file__).parent / "notes"

mcp = MCPServer("Notes")


def note_path(name: str) -> Path:
    # Resolve a note name to a path, accepting only a .md file directly in the notes folder
    path = (NOTES_DIR / name).resolve()
    if path.parent != NOTES_DIR.resolve() or path.suffix != ".md":
        raise ToolError(
            f"Note name '{name}' must be a .md file name directly in the notes folder, for example 'todo.md'."
        )
    return path


@mcp.tool()
def list_notes() -> list[str]:
    """List the names of all notes in the notes folder.

    Returns file names with the .md extension, sorted alphabetically,
    for example "shopping-list.md". Pass a name as-is to read_note.
    """
    return sorted(path.name for path in NOTES_DIR.glob("*.md"))


@mcp.tool()
def read_note(name: str) -> str:
    """Read the text of a note from the notes folder.

    `name` is the note's file name with the .md extension, exactly as
    returned by list_notes, for example "shopping-list.md".
    """
    path = note_path(name)
    if not path.is_file():
        raise ToolError(f"Note '{name}' not found.")
    return path.read_text(encoding="utf-8")


if __name__ == "__main__":
    mcp.run()
