import logging
from pathlib import Path

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError, ResourceNotFoundError
from mcp.shared.exceptions import MCPError
from mcp.types import INVALID_PARAMS, ToolAnnotations
from mcp.server.mcpserver.prompts.base import AssistantMessage, Message, UserMessage

NOTES_DIR = Path(__file__).parent / "notes"

logger = logging.getLogger(__name__)
mcp = MCPServer("Notes")


def note_path(name: str) -> Path:
    # Resolve a note name to a path, accepting only a .md file directly in the notes folder
    path = (NOTES_DIR / name).resolve()
    if path.parent != NOTES_DIR.resolve() or path.suffix != ".md":
        raise ToolError(
            f"Note name '{name}' must be a .md file name directly in the notes folder, for example 'todo.md'."
        )
    return path


@mcp.tool(annotations=ToolAnnotations(read_only_hint=True, open_world_hint=False))
def list_notes() -> list[str]:
    """List the names of all notes in the notes folder.

    Returns file names with the .md extension, sorted alphabetically,
    for example "shopping-list.md". Pass a name as-is to read_note.
    """
    logger.info("Listing notes")
    return sorted(path.name for path in NOTES_DIR.glob("*.md"))


@mcp.tool(annotations=ToolAnnotations(read_only_hint=True, open_world_hint=False))
def read_note(name: str) -> str:
    """Read the text of a note from the notes folder.

    `name` is the note's file name with the .md extension, exactly as
    returned by list_notes, for example "shopping-list.md".
    """
    path = note_path(name)
    if not path.is_file():
        raise ToolError(f"Note '{name}' not found.")
    return path.read_text(encoding="utf-8")


@mcp.tool(annotations=ToolAnnotations(destructive_hint=True, idempotent_hint=True, open_world_hint=False))
def write_note(name: str, content: str) -> str:
    """Create a note in the notes folder, or overwrite it if it exists.

    `name` is the file name with the .md extension, for example "todo.md".
    `content` is the full new content; an existing note's text is replaced.
    """
    path = note_path(name)
    path.write_text(content, encoding="utf-8")
    logger.info("Saved note '%s'", name)
    return f"Saved note '{name}'."


@mcp.resource("notes://index")
def notes_index() -> str:
    """All notes in the notes folder with the first line of each."""
    lines = []
    for name in list_notes():
        text = (NOTES_DIR / name).read_text(encoding="utf-8")
        first_line = (text.splitlines() or [""])[0]
        lines.append(f"{name}: {first_line}")
    return "\n".join(lines)


@mcp.resource("notes://{name}")
def note_content(name: str) -> str:
    """The full text of one note, for example notes://shopping-list.md."""
    try:
        return read_note(name)
    except ToolError as e:
        raise ResourceNotFoundError(str(e)) from e


@mcp.prompt()
def summarize_note(name: str) -> str:
    """Briefly summarize a note from the notes folder."""
    try:
        text = read_note(name)
    except ToolError as e:
        # Only MCPError reaches the client with its message; other errors become a generic one
        raise MCPError(INVALID_PARAMS, str(e)) from e
    return f"Briefly summarize the note '{name}':\n\n{text}"


@mcp.prompt()
def discuss_note(name: str) -> list[Message]:
    """Start a conversation about a note from the notes folder."""
    try:
        text = read_note(name)
    except ToolError as e:
        raise MCPError(INVALID_PARAMS, str(e)) from e
    return [
        UserMessage(f"Here is my note '{name}':"),
        UserMessage(text),
        AssistantMessage("I've read the note. What would you like to do with it?"),
    ]


if __name__ == "__main__":
    mcp.run()
