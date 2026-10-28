# Workshop: Your Own MCP Server for Claude Code

The goal is to write a minimal local "Notes" MCP server in Python with your own hands, connect it to Claude Code, and see how Claude works with it.

- **No API keys and no custom client**: Claude Code acts as the client.
- **No hosting**: the server runs locally over stdio, and Claude Code launches it as a subprocess itself.
- **No ready-made solutions**: each step has a task, API hints, and a check criterion. You write the code.

SDK version: `mcp` **2.3.0** (PyPI, October 2026).
> ⚠️ In SDK v2 the `FastMCP` class was renamed to `MCPServer`. Most tutorials on the internet (and the course in `cli_project`) are written for v1: `from mcp.server.fastmcp import FastMCP`. In v2 this import fails with `ModuleNotFoundError`. If an example from the internet doesn't work, check the version first.

### Documentation
- MCP Python SDK: https://py.sdk.modelcontextprotocol.io
- Claude Code MCP: https://code.claude.com/docs/en/mcp

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

**Documentation:** [First steps](https://py.sdk.modelcontextprotocol.io/get-started/first-steps/), [Connect to a real host](https://py.sdk.modelcontextprotocol.io/get-started/real-host/)

**Hint:**
- Store the instance in a module-level variable named `mcp`: `mcp = MCPServer("Notes")`. All later hints in the course use this name (`@mcp.tool()`, `@mcp.resource()`, `@mcp.prompt()`), and the `mcp dev` and `mcp run` commands look for an object named `mcp`, `server`, or `app` in the file.

### Step 1.2 — Experiment: be the client yourself
- [ ] Run `uv run server.py` and paste the three messages below into the terminal one at a time, pressing Enter after each. Each message is a single line of JSON.

1. `initialize`:
   ```json
   {"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-11-25","capabilities":{},"clientInfo":{"name":"manual","version":"0.1"}}}
   ```
2. `notifications/initialized`:
   ```json
   {"jsonrpc":"2.0","method":"notifications/initialized"}
   ```
3. `tools/list`:
   ```json
   {"jsonrpc":"2.0","id":2,"method":"tools/list"}
   ```

**What you'll see:**
- After `initialize`, the server answers with a line that contains `"serverInfo":{"name":"Notes",...}` and the list of its capabilities.
- `notifications/initialized` gets no answer: it is a notification, it has no `id`.
- `tools/list` returns `{"tools":[]}`: there are no tools yet.

Stop the process with `Ctrl+C`.

**What to notice:**
- `initialize` must come first: this is the handshake in which the client and the server agree on the protocol version.
- The `id` field links each response to its request.
- This is exactly the exchange that Claude Code and MCP Inspector perform for you. Repeat `tools/list` after module 2 and you will see `list_notes` with its description and argument schema.

**Comprehension question 1.** Why is it pointless to keep such a server running in a separate terminal and expect Claude Code to connect to it? ([answer](#answers-to-comprehension-questions))

---

## Module 2. The first tool

### Step 2.1 — `list_notes`
- [ ] Write a `list_notes` tool that returns a sorted list of file names from the `notes/` folder.

**Documentation:** [Tools](https://py.sdk.modelcontextprotocol.io/servers/tools/), [Structured Output](https://py.sdk.modelcontextprotocol.io/servers/structured-output/)

**Hints:**
- Write the tools right in `server.py`. Importing a function from another file is not enough: it also has to be registered on the server. How to do that is described in the ["Tools in a separate file"](#tools-in-a-separate-file) section at the end of the course.
- The server launch (the `if __name__ == "__main__":` block) must stay at the end of the file: `mcp.run()` does not return, and nothing below it will run. Inspector won't reveal this mistake, because `mcp dev` imports the file and skips this block.
- The docstring is the triple-quoted string right below `def`. It is not just a comment: the SDK sends it to the model as the tool description, and the model uses it to decide when to call the tool. Without a docstring, the model sees only the function name and its arguments. For `list_notes`, this would work, for example:
  ```python
  """List the names of all notes (Markdown files) in the notes folder."""
  ```
- Build the folder path relative to the file's location, not the current directory: `Path(__file__).parent / "notes"`. Claude Code may launch the server from a different working directory.
- Return type: `list[str]` or `str`. Try both and see in Inspector how the result differs.

### Step 2.2 — Check in MCP Inspector
- [ ] Run `uv run mcp dev server.py`.
- [ ] In the browser that opens, click Connect → **Tools** tab → `list_notes` → Run.

**Documentation:** [First steps](https://py.sdk.modelcontextprotocol.io/get-started/first-steps/) (the section on `mcp dev`)

**Check:** you see the list of your files.

**Why this step:** Inspector is also an MCP client, just a manual one. This way you debug the server without involving the model and see the raw JSON of requests and responses.

---

## Module 3. Connecting to Claude Code

### Step 3.1 — Registration
- [ ] Open a terminal in the folder where you plan to work with our training MCP server, and register it in Claude:
  ```bash
  claude mcp add notes -- uv run --directory C:/path/to/mcp_practice server.py
  ```

**Documentation:** [Claude Code: MCP](https://code.claude.com/docs/en/mcp), [Connect to a real host](https://py.sdk.modelcontextprotocol.io/get-started/real-host/)

**Explanations:**
- `notes` — the name Claude Code will know the server by.
- `uv run --directory <folder> server.py` — run `server.py` in the project environment from the given folder.
- Replace `C:/path/to/mcp_practice` with the absolute path to the `mcp_practice` folder that contains `server.py`. If the path contains spaces, wrap it in quotes.
- The default scope is `local`: the server is available only to you and only in this folder.
- If you want to set the scope (for example, `user`, to make the server available in all folders) or other options, put them after the server name and before `--`: `claude mcp add notes --scope user -- …`.

**Check:** `claude mcp get notes` shows the command with the full path to your folder.

**If you made a mistake:** run `claude mcp remove notes` and register again. List all servers: `claude mcp list`.

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

**Documentation:** [Tools](https://py.sdk.modelcontextprotocol.io/servers/tools/)

**Hint:** in the docstring, state what the name alone doesn't tell: what format `name` is expected in (for example, a file name with the `.md` extension, as returned by `list_notes`).

### Step 4.2 — Expected errors
- [ ] If the note doesn't exist, return an error the model can understand instead of crashing with a traceback.

**Documentation:** [Handling errors](https://py.sdk.modelcontextprotocol.io/servers/handling-errors/)

**Experiment:**
1. After editing `server.py`, reconnect the server in Claude Code: `/mcp` → `notes` → Reconnect. There is no need to register the server again.
2. Ask Claude to read a nonexistent note and see how it reacts to `ToolError`.
3. Temporarily replace `ToolError` with a plain `ValueError` and compare.

### Step 4.3 — Path safety
- [ ] Forbid reading outside of `notes/`.

**Why this is needed.** Right now `read_note` builds the path as `NOTES_DIR / name` and reads any file it can reach. There are two dangerous cases:
- `name="../pyproject.toml"`: `..` leads out of the `notes/` folder upwards.
- `name="C:/Windows/win.ini"` (on macOS and Linux, `name="/etc/hosts"`): if the right side of `/` is an absolute path, `pathlib` drops everything on the left, and `NOTES_DIR` simply disappears.

**Hints:**
1. Bring the path to its final form: `(NOTES_DIR / name).resolve()`. [`resolve()`](https://docs.python.org/3/library/pathlib.html#pathlib.Path.resolve) makes the path absolute and removes `..`: `notes/../pyproject.toml` becomes `.../mcp_practice/pyproject.toml`.
2. Check that the result lies inside the notes folder: [`path.is_relative_to(NOTES_DIR.resolve())`](https://docs.python.org/3/library/pathlib.html#pathlib.PurePath.is_relative_to). Resolve the folder too, otherwise you compare paths of different forms.
3. If the check fails, raise `ToolError`, as in step 4.2.
4. You will need this check again in `write_note` (step 5.1) and in the `notes://{name}` resource (step 7.2), so it is convenient to move it into a separate function.

**Check:** in Inspector, both calls, `name="../pyproject.toml"` and `name="C:/Windows/win.ini"`, return an error, not the file contents. `name="shopping-list.md"` still reads fine.

**Comprehension question 2.** Why does this check have to be done in the server, rather than hoping the model won't ask for too much? ([answer](#answers-to-comprehension-questions))

---

## Module 5. A tool that modifies data

### Step 5.1 — `write_note(name, content)`
- [ ] Create or overwrite a note. The path protection from step 4.3 is mandatory here too.

**Documentation:** [Tools](https://py.sdk.modelcontextprotocol.io/servers/tools/)

### Step 5.2 — Observation
- [ ] Ask Claude: "Create a todo note with three items".

**What to observe:** the permission request before the call.

**Comprehension question 3.** Why is host caution especially important for tools that modify data? ([answer](#answers-to-comprehension-questions))

**Extra:** mark your tools with annotations. Documentation: [Names, titles, and annotations](https://py.sdk.modelcontextprotocol.io/servers/tools/#names-titles-and-annotations).

| Annotation | The question it answers | For which tools |
|---|---|---|
| `read_only_hint` | Does the tool change nothing? | read-only tools |
| `destructive_hint` | Can it delete or overwrite existing data? | modifying tools only |
| `idempotent_hint` | Is a repeated call with the same arguments safe, with the same result? | modifying tools only |
| `open_world_hint` | Does it work with the outside world (the internet) rather than a closed set of data? | any tool |

Each annotation takes only `True` or `False`.

---

## Module 6. Logging

**Key points:**
- Don't use `print()`: for a stdio server, stdout is the protocol channel, and every line in it must be a JSON-RPC message. SDK v2 protects stdout while the server is running, but a `print()` before the server starts still goes into the channel.
- Log with the standard `logging` module: it writes to stderr and doesn't interfere with the protocol.
- Logs are visible in the terminal when you run the server by hand, and in Inspector. In a client such as Claude Code they are not visible during normal work: they are a tool for the server developer.

**Documentation:** [Logging](https://py.sdk.modelcontextprotocol.io/handlers/logging/)

### Step 6.1 — Logging
- [ ] Add a log record to `list_notes` using `logging`.
- [ ] **Terminal:** run `uv run server.py`, paste three messages one at a time, and find your record:
  1. `initialize`:
     ```json
     {"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-11-25","capabilities":{},"clientInfo":{"name":"manual","version":"0.1"}}}
     ```
  2. `notifications/initialized`:
     ```json
     {"jsonrpc":"2.0","method":"notifications/initialized"}
     ```
  3. The `list_notes` call:
     ```json
     {"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"list_notes","arguments":{}}}
     ```
- [ ] **Inspector:** run `uv run mcp dev server.py`, call `list_notes`, and find your record.

**Note:** there is no need to send logs to the client through `Context` (`ctx.info()` and so on): the 2026-07-28 protocol deprecates this capability ([Deprecated features](https://py.sdk.modelcontextprotocol.io/deprecated/)).

---

## Module 7. Resources

Resources are data chosen by the **user**, not the model. Tools are actions chosen by the model.

### Step 7.1 — Static resource `notes://index`
- [ ] The resource returns a list of notes with their size or first line.

**Hints:**
- `@mcp.resource("notes://index")` — a URI without parameters means a static resource, and the function must have no parameters.
- The returned `str` becomes the text content of the resource. Optional decorator arguments: `name`, `description`, `mime_type`.

### Step 7.2 — Resource template `notes://{name}`
- [ ] The resource returns the contents of a specific note.

**Hints:** `{name}` in the URI must match the function parameter **exactly**. Don't forget the path protection.

### Step 7.3 — Check
- [ ] In Inspector: the Resources and Resource Templates tabs.
- [ ] In Claude Code: type `@` in the input line and find the resources of the `notes` server. Attach `notes://index` to a question.

**Comprehension question 4.** Which resources appear in the `@` autocomplete: static, templated, or both? ([answer](#answers-to-comprehension-questions))

**Comprehension question 5.** How does the situation where you attached a resource differ from the one where Claude called `list_notes` on its own? ([answer](#answers-to-comprehension-questions))

---

## Module 8. Prompts

### Step 8.1 — `summarize_note(name)`
- [ ] The prompt returns the request text "briefly summarize the note …" together with the note's contents.

**Hints:**
- `@mcp.prompt()`. The returned `str` becomes a user message.
- The function arguments become the prompt arguments.

### Step 8.2 — Multi-message prompt
- [ ] Make a second prompt that returns several messages, for example a "user → assistant" dialogue template.

**Hints:** `from mcp.server.mcpserver.prompts.base import Message, UserMessage, AssistantMessage`. The return type is `list[Message]`.

### Step 8.3 — Check in Claude Code
- [ ] Type `/` and find the `/notes:summarize_note (MCP)` command in the list. Invoke it with a note name.

**Hint:** you can also type the same command in its full form: `/mcp__notes__summarize_note <note name>`.

**What to observe:** a prompt is a template that you insert. Unlike tools, the model does not invoke prompts on its own.

---

## Module 9. Wrap-up

### Step 9.1 — `project` scope
- [ ] Remove the local registration and register the server with `--scope project`.

**What to observe:**
- A `.mcp.json` file appears in the project root. Study its format.
- This file can be committed, and anyone who opens the project in Claude Code will get the server (after confirmation).

### Step 9.2 — Final question
- [ ] Answer the question below in your own words.

**Comprehension question 6.** When to use what: **tool**, **resource**, **prompt**? ([answer](#answers-to-comprehension-questions))

---

## What's next (beyond the course)
- Streamable HTTP transport: the same server as a network service, and `claude mcp add --transport http`.
- Structured tool output: returning Pydantic models and TypedDict.
- Progress for long-running operations: `ctx.report_progress(...)`.
- Tools in a separate file: details below.

### Tools in a separate file

When there are many tools, it is convenient to move them out of `server.py` into a separate module. A tool is a plain function, but importing it is not enough: it has to be registered on the `mcp` object that actually runs.

**The right way:** the function lives in a separate file, and `server.py` registers it with `mcp.add_tool(...)`. This is the same as `@mcp.tool()`: the decorator calls `add_tool` internally, and the name, description, and argument schema are built the same way.

`tools.py`:
```python
from pathlib import Path

NOTES_DIR = Path(__file__).parent / "notes"


def list_notes() -> list[str]:
    """List the names of all notes (Markdown files) in the notes folder."""
    return sorted(path.name for path in NOTES_DIR.glob("*.md"))
```

`server.py`:
```python
from mcp.server import MCPServer

from tools import list_notes

mcp = MCPServer("Notes")
mcp.add_tool(list_notes)

if __name__ == "__main__":
    mcp.run()
```

`tools.py` has no imports from the MCP SDK: these are plain functions you can call and test separately from the server.

**The trap:** don't import `mcp` from `server.py` into the tools file (`from server import mcp` with `@mcp.tool()` above the function). When run with `uv run server.py`, this breaks silently:
1. `server.py` is run as a script, so Python loads it under the name `__main__`.
2. `tools.py` runs `from server import mcp`. Python hasn't loaded a module named `server` yet, so it loads `server.py` a second time and creates a second `mcp` object.
3. The tools are registered on the second object, while the first one runs. `tools/list` returns an empty list.

Inspector won't show this mistake: `mcp dev` imports the file rather than running it as a script. The rule is simple: the server imports the tools, and the tools don't import the server.

---

## Answers to comprehension questions

Answer on your own first, then check.

**1. Why is it pointless to keep a stdio server running in a separate terminal?**
A stdio server receives requests only through stdin and answers only through stdout. That is why only whoever launched it can work with it. If you launch the server in a terminal, only you can talk to it, by hand. Claude Code can't connect to it, so it launches the server itself. That is why `claude mcp add` takes a launch command, not an address.

**2. Why does the path check have to be done in the server?**
The model is not a security boundary. It can make mistakes, and it can be tricked: for example, the text of a note may contain an instruction like "read `../.env`" (prompt injection). Besides, the model is not the only caller: Inspector, another client, or a script can send any arguments. The server is the only place every file request passes through, so that is the only place the restriction actually works.

**3. Why is host caution especially important for tools that modify data?**
A mistake while reading can simply be ignored, but a mistake while writing cannot: an overwritten note can't be brought back. The model may misunderstand the request or follow someone else's instruction found in the data it has read. The permission request keeps a human as the last step before an irreversible action. The `readOnlyHint` and `destructiveHint` annotations help the host decide where asking is a must.

**4. Which resources appear in the `@` autocomplete?**
Expected: only static ones, such as `notes://index`. The server returns them in response to `resources/list`: these are concrete resources with a ready URI. The `notes://{name}` template comes in a separate `resources/templates/list` request and is not a resource by itself until a name is filled in. You can attach a note through the template by typing a concrete URI, for example `@notes:notes://shopping`. Check this on your version of Claude Code: the documentation does not say whether the autocomplete shows templates.

**5. How does an attached resource differ from a `list_notes` call?**
- **Who decides.** You chose the resource; the model chose to call the tool.
- **When the data reaches the context.** Claude Code reads an attached resource itself and adds it to your message before the model starts answering. The model calls a tool in the middle of its answer, if it decides it needs to.
- **Permissions.** Attaching a resource doesn't trigger a permission request: you already gave permission by choosing it. For a tool call, Claude Code asks.

**6. When to use what?**
- **Tool** — an action or computation the model decides on: search, reading on demand, writing, calling an external API. May have side effects.
- **Resource** — read-only data with its own URI that the user (or the application) picks to give the model context. No side effects.
- **Prompt** — a ready-made request template the user runs explicitly, for example as a slash command. The model does not invoke prompts on its own.
