# Workshop: Your Own MCP Server for Claude Code

The goal is to write a minimal local "Notes" MCP server in Python with your own hands, connect it to Claude Code, and see how Claude works with it.

- **No API keys and no custom client**: Claude Code acts as the client.
- **No hosting**: the server runs locally over stdio, and Claude Code launches it as a subprocess itself.
- **No ready-made solutions**: each step has a task, API hints, and a check criterion. You write the code.

SDK version: `mcp` **2.3.0** (PyPI, October 2026).
> ⚠️ In SDK v2 the `FastMCP` class was renamed to `MCPServer`. Most tutorials on the internet (and the course in `cli_project`) are written for v1: `from mcp.server.fastmcp import FastMCP`. In v2 this import fails with `ModuleNotFoundError`. If an example from the internet doesn't work, check the version first.

SDK documentation: https://py.sdk.modelcontextprotocol.io
Claude Code MCP documentation: https://code.claude.com/docs/en/mcp

---

## How the "Notes" server is structured

```
mcp_practice/
├── COURSE.md        ← this file
├── server.py        ← your MCP server
└── notes/           ← the "database": plain .md files
    ├── shopping.md
    └── ideas.md
```

By the end of the course the server will support:

| Capability | What it is | Who initiates |
|---|---|---|
| **Tools** `list_notes`, `read_note`, `write_note` | Actions | Claude decides on its own when to call them |
| **Resources** `notes://index`, `notes://{name}` | Read-only data | You, via `@` in the input line |
| **Prompts** `summarize_note` | Ready-made request templates | You, via a slash command |

---

## Module 0. Environment setup

### Step 0.1 — Check the tools
- [ ] Make sure `uv`, `node`/`npx` (needed for MCP Inspector), and `claude` are available in the terminal.

**Check:** `uv --version`, `npx --version`, and `claude --version` print versions.

> The course uses `uv` to create the project, install dependencies, and run the server. If `uv` is not installed, install it following the instructions: https://docs.astral.sh/uv/getting-started/installation/
> For example, on Windows: `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`, on macOS and Linux: `curl -LsSf https://astral.sh/uv/install.sh | sh`. Restart the terminal after installation.

### Step 0.2 — Create the project
- [ ] Initialize a uv project in the `mcp_practice` folder (where this file is located).
- [ ] Add the SDK dependency with the CLI extra.

**Hints:** `uv init`, `uv add "mcp[cli]"`.

**Check:** `pyproject.toml` contains the dependency `mcp[cli]>=2.3.0`, and `uv run python -c "import mcp.server.mcpserver"` runs without errors.

### Step 0.3 — Prepare the data
- [ ] Create a `notes/` folder and put 2–3 `.md` files with any text into it.
- [ ] Delete the `main.py` file created by `uv init`: it is not needed (or rename it to `server.py`).

> If there is no `main.py` and a `src/` folder appeared instead (this is what `uv init --package` and the PyCharm uv template do), the project was created as an installable package. The course needs a flat layout with `server.py` in the root, so:
> - Delete the `src/` folder entirely.
> - Remove the `[project.scripts]` section from `pyproject.toml`: it points to the `main` function in the deleted folder.
> - Remove the `[build-system]` section from `pyproject.toml`. Without it, uv treats the project as a plain application and does not try to build and install a package on every `uv run`.
> - Run `uv sync` to remove the old package installation from `.venv`. Otherwise every run prints the warning `mcp_practice.pth: ...\src does not exist; skipping sys.path append`.
>
> **Check:** `uv run python -c "import mcp.server.mcpserver"` still runs without errors.

---

## Module 1. Server skeleton

### Step 1.1 — Minimal server
- [ ] Create `server.py`: a server instance named `"Notes"` that runs over stdio when the file is executed as a script.

**Hints:**
- `from mcp.server import MCPServer`
- `MCPServer(name: str)` — creates the server.
- `mcp.run()` — runs the server (stdio transport by default).
- Put the launch under `if __name__ == "__main__":`. The SDK tools (`mcp dev`, `mcp run`) import your file, and the server must not start on import.

### Step 1.2 — Observation: what stdio looks like
- [ ] Run `uv run server.py` manually.

**What you'll see:** nothing happens, the process "hangs". The server is waiting for JSON-RPC messages on stdin, meaning a client has to launch it and "feed" it. Stop the process with `Ctrl+C`.

**Comprehension question:** why is it pointless to keep such a server running in a separate terminal and expect Claude Code to connect to it?

---

## Module 2. The first tool

### Step 2.1 — `list_notes`
- [ ] Write a `list_notes` tool that returns the file names from the `notes/` folder.

**Hints:**
- The `@mcp.tool()` decorator (with the parentheses) turns a function into a tool.
- The SDK builds the tool description for the model itself:
  - **name** — from the function name;
  - **description** — from the docstring;
  - **argument schema** — from the type hints.
- Build the folder path relative to the file's location, not the current directory: `Path(__file__).parent / "notes"`. Claude Code may launch the server from a different working directory.
- Return type: `list[str]` or `str`. Try both and see in Inspector how the result differs.

### Step 2.2 — Check in MCP Inspector
- [ ] Run `uv run mcp dev server.py`.
- [ ] In the browser that opens, click Connect → **Tools** tab → `list_notes` → Run.

**Check:** you see the list of your files.

**Why this step:** Inspector is also an MCP client, just a manual one. This way you debug the server without involving the model and see the raw JSON of requests and responses.

---

## Module 3. Connecting to Claude Code

### Step 3.1 — Registration
- [ ] Register the server in Claude Code under the name `notes`.

**Hints:**
- Syntax: `claude mcp add [options] <name> -- <command> [args...]`.
- Everything after `--` is the command Claude Code will use to launch the server. Its own options (`--scope`, `--env`, `--transport`) go **before** `--`.
- To make the server launch correctly from any working directory, give uv the path to the project: `uv run --directory C:/Users/nikbu/PycharmProjects/mcp_practice server.py`.
- The default scope is `local`: the server is available only to you and only in the folder where the command was run.
- Useful commands: `claude mcp list`, `claude mcp get notes`, `claude mcp remove notes`.

### Step 3.2 — Check the connection
- [ ] Run `claude` in the folder where you registered the server.
- [ ] Run `/mcp`.

**Check:** the `notes` server has the status connected, and `list_notes` is in its list of tools.

### Step 3.3 — First conversation
- [ ] Ask Claude: "What notes do I have?"

**What to observe:**
- Claude will call the `mcp__notes__list_notes` tool. This is the full name: `mcp__<server>__<tool>`.
- Claude Code will ask for permission to make the call. This is a permission check on the host side: the server itself knows nothing about it.
- You didn't tell Claude the tool exists. It learned about it from the description the client received from the server.

---

## Module 4. Reading a note and error handling

### Step 4.1 — `read_note(name)`
- [ ] The tool takes a note name and returns its text.

### Step 4.2 — Expected errors
- [ ] If the note doesn't exist, return an error the model can understand instead of crashing with a traceback.

**Hints:**
- `from mcp.server.mcpserver.exceptions import ToolError`
- `raise ToolError("message")` — the model will receive a response with `is_error=True` and your text, and will be able to react to it.
- Any other exception is treated as a "crash": the model will only see `Error executing tool <name>`, without details.

**Experiment:**
1. Ask Claude to read a nonexistent note and see how it reacts to `ToolError`.
2. Temporarily replace `ToolError` with a plain `ValueError` and compare.

### Step 4.3 — Path safety
- [ ] Forbid reading outside of `notes/`.

**Check:** a call in Inspector with `name="../pyproject.toml"` returns an error, not the file contents.

**Hints:** `Path.resolve()`, `Path.is_relative_to()`.

**Comprehension question:** why does this check have to be done in the server, rather than hoping the model won't ask for too much?

---

## Module 5. Development loop and the description for the model

### Step 5.1 — How to apply changes
- [ ] Change something in `server.py` and get Claude Code to see the change.

**Hint:** Claude Code keeps the server process running. After editing the code, the server has to be reconnected via `/mcp` (reconnect), or Claude Code has to be restarted.

### Step 5.2 — The docstring is the interface for the model
- [ ] Experiment: temporarily make the `read_note` docstring useless (for example, `"""Does stuff."""`) or remove it entirely. Reconnect the server and ask Claude to read the shopping note.
- [ ] Restore a good docstring: what the tool does and what format `name` is expected in (with or without the `.md` extension).

**What to observe:** how confidently Claude picks the tool and whether it passes the arguments correctly.

---

## Module 6. A tool that modifies data

### Step 6.1 — `write_note(name, content)`
- [ ] Create or overwrite a note. The path protection from step 4.3 is mandatory here too.

### Step 6.2 — Observation
- [ ] Ask Claude: "Create a todo note with three items".

**What to observe:** the permission request before the call. Think about why host caution is especially important for tools that modify data.

**Extra:** you can pass `annotations` to `@mcp.tool()` with hints such as `readOnlyHint` and `destructiveHint`. Look up in the SDK documentation how they are set, and mark your tools with them.

---

## Module 7. Logging and the stdout trap

### Step 7.1 — The trap
- [ ] Add a plain `print("debug")` to `list_notes`, reconnect the server, and call the tool through Claude.

**What to observe:** with stdio, the server's stdout is occupied by the protocol, and your `print` goes straight into the JSON-RPC stream. See what happens to the connection. Then remove the `print`.

### Step 7.2 — The right ways
- [ ] Log to stderr, for example via the standard `logging` module: by default it writes to stderr.
- [ ] Send a log message to the client through the context.

**Hints:**
- `from mcp.server.mcpserver import Context`
- Add a parameter annotated with `Context` to the tool, for example `ctx: Context`. The SDK will inject it itself, and it won't appear in the argument schema for the model.
- `await ctx.info("...")` (as well as `debug`, `warning`, `error`). The tool function must then be `async def`.
- Look at these logs in Inspector (`mcp dev`).

---

## Module 8. Resources

Resources are data chosen by the **user**, not the model. Tools are actions chosen by the model.

### Step 8.1 — Static resource `notes://index`
- [ ] The resource returns a list of notes with their size or first line.

**Hints:**
- `@mcp.resource("notes://index")` — a URI without parameters means a static resource, and the function must have no parameters.
- The returned `str` becomes the text content of the resource. Optional decorator arguments: `name`, `description`, `mime_type`.

### Step 8.2 — Resource template `notes://{name}`
- [ ] The resource returns the contents of a specific note.

**Hints:** `{name}` in the URI must match the function parameter **exactly**. Don't forget the path protection.

### Step 8.3 — Check
- [ ] In Inspector: the Resources and Resource Templates tabs.
- [ ] In Claude Code: type `@` in the input line and find the resources of the `notes` server. Attach `notes://index` to a question.

**What to observe:**
- Which resources appear in the `@` autocomplete: static, templated, or both?
- How does the situation where you attached a resource differ from the one where Claude called `list_notes` on its own?

---

## Module 9. Prompts

### Step 9.1 — `summarize_note(name)`
- [ ] The prompt returns the request text "briefly summarize the note …" together with the note's contents.

**Hints:**
- `@mcp.prompt()`. The returned `str` becomes a user message.
- The function arguments become the prompt arguments.

### Step 9.2 — Multi-message prompt
- [ ] Make a second prompt that returns several messages, for example a "user → assistant" dialogue template.

**Hints:** `from mcp.server.mcpserver.prompts.base import Message, UserMessage, AssistantMessage`. The return type is `list[Message]`.

### Step 9.3 — Check in Claude Code
- [ ] Type `/` and find a command like `/mcp__notes__summarize_note`. Invoke it with a note name.

**What to observe:** a prompt is a template that you insert. Unlike tools, the model does not invoke prompts on its own.

---

## Module 10. Wrap-up

### Step 10.1 — `project` scope
- [ ] Remove the local registration and register the server with `--scope project`.

**What to observe:**
- A `.mcp.json` file appears in the project root. Study its format.
- This file can be committed, and anyone who opens the project in Claude Code will get the server (after confirmation).

### Step 10.2 — Final question
- [ ] Put into your own words when to use what:
  - **tool** — when?
  - **resource** — when?
  - **prompt** — when?

---

## What's next (beyond the course)
- Streamable HTTP transport: the same server as a network service, and `claude mcp add --transport http`.
- Structured tool output: returning Pydantic models and TypedDict.
- Progress for long-running operations: `ctx.report_progress(...)`.
