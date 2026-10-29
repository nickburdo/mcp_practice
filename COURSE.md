# Workshop: Your Own MCP Server for Claude Code and Claude Desktop

The goal is to write a minimal local "Notes" MCP server in Python with your own hands, check it in MCP Inspector, then connect it to Claude Code and Claude Desktop and see how Claude works with it.

- **No API keys and no custom client**: during development the server is checked in MCP Inspector, and in the last module Claude Code and Claude Desktop act as the clients.
- **No hosting**: the server runs locally over stdio, and the client launches it as a subprocess itself.
- **No ready-made solutions**: each step has a task, API hints, and a check criterion. You write the code.

SDK version: `mcp` **2.3.0** (PyPI, October 2026).
> ⚠️ In SDK v2 the `FastMCP` class was renamed to `MCPServer`. Most tutorials on the internet (and the course in `cli_project`) are written for v1: `from mcp.server.fastmcp import FastMCP`. In v2 this import fails with `ModuleNotFoundError`. If an example from the internet doesn't work, check the version first.

### Documentation
- MCP Python SDK: https://py.sdk.modelcontextprotocol.io
- Claude Code MCP: https://code.claude.com/docs/en/mcp
- Claude Desktop and local MCP servers: https://modelcontextprotocol.io/docs/develop/connect-local-servers

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
| **Resources** `notes://index`, `notes://{name}` | Read-only data | You, by attaching a resource to a message |
| **Prompts** `summarize_note` | Ready-made request templates | You, by picking a prompt from the client's menu or with a slash command |

---

## Module 0. Environment setup

### Step 0.1 — Check the tools
- [ ] Make sure `uv` and `node`/`npx` (needed for MCP Inspector) are available in the terminal.

**Check:** `uv --version` and `npx --version` print versions.

> You will need Claude Code and Claude Desktop only in module 8.

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
- This is exactly the exchange that MCP Inspector and clients such as Claude Code and Claude Desktop perform for you. Repeat `tools/list` after module 2 and you will see `list_notes` with its description and argument schema.

**Comprehension question 1.** Why is it pointless to keep such a server running in a separate terminal and expect a client, such as Claude Code, to connect to it? ([answer](#answers-to-comprehension-questions))

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
- Build the folder path relative to the file's location, not the current directory: `Path(__file__).parent / "notes"`. The client may launch the server from a different working directory.
- Return type: `list[str]` or `str`. Try both and see in Inspector how the result differs.

### Step 2.2 — Check in MCP Inspector
- [ ] Run `uv run mcp dev server.py`.
- [ ] In the browser that opens, click Connect → **Tools** tab → `list_notes` → Run.

**Documentation:** [First steps](https://py.sdk.modelcontextprotocol.io/get-started/first-steps/) (the section on `mcp dev`)

**Check:** you see the list of your files.

**Why this step:** Inspector is also an MCP client, just a manual one. This way you debug the server without involving the model and see the raw JSON of requests and responses.

**Note:** Inspector doesn't pick up changes in `server.py` on its own. To make it see the new code, click Disconnect and then Connect: Inspector starts the server again. There is no need to restart `mcp dev`.

---

## Module 3. Reading a note and error handling

### Step 3.1 — `read_note(name)`
- [ ] The tool takes a note name and returns its text.

**Documentation:** [Tools](https://py.sdk.modelcontextprotocol.io/servers/tools/)

**Hint:** in the docstring, state what the name alone doesn't tell: what format `name` is expected in (for example, a file name with the `.md` extension, as returned by `list_notes`).

### Step 3.2 — Expected errors
- [ ] If the note doesn't exist, return an error the model can understand instead of crashing with a traceback.

**Documentation:** [Handling errors](https://py.sdk.modelcontextprotocol.io/servers/handling-errors/)

### Step 3.3 — Path safety
- [ ] Forbid reading outside of `notes/`.

**Why this is needed.** Right now `read_note` builds the path as `NOTES_DIR / name` and reads any file it can reach. There are two dangerous cases:
- `name="../pyproject.toml"`: `..` leads out of the `notes/` folder upwards.
- `name="C:/Windows/win.ini"` (on macOS and Linux, `name="/etc/hosts"`): if the right side of `/` is an absolute path, `pathlib` drops everything on the left, and `NOTES_DIR` simply disappears.

**Hints:**
1. Bring the path to its final form: `(NOTES_DIR / name).resolve()`. [`resolve()`](https://docs.python.org/3/library/pathlib.html#pathlib.Path.resolve) makes the path absolute and removes `..`: `notes/../pyproject.toml` becomes `.../mcp_practice/pyproject.toml`.
2. Check that the result lies inside the notes folder: [`path.is_relative_to(NOTES_DIR.resolve())`](https://docs.python.org/3/library/pathlib.html#pathlib.PurePath.is_relative_to). Resolve the folder too, otherwise you compare paths of different forms.
3. If the check fails, raise `ToolError`, as in step 3.2.
4. You will need this check again in `write_note` (step 4.1) and in the `notes://{name}` resource (step 6.2), so it is convenient to move it into a separate function.

### Step 3.4 — Check in Inspector
- [ ] Call `read_note` with the name of an existing note, for example `shopping-list.md`.
- [ ] Call `read_note` with the name of a nonexistent note.
- [ ] Call `read_note` with `name="../pyproject.toml"` and with `name="C:/Windows/win.ini"` (on macOS and Linux, `name="/etc/hosts"`).

**Check:**
- the existing note returns its text;
- for the nonexistent note, Inspector shows an error with your text;
- both dangerous paths return an error, not the file contents.

**Experiment:** temporarily replace `ToolError` with a plain `ValueError` and call `read_note` with a nonexistent note again. Your text is gone, and only a generic "Error executing tool read_note" remains: the SDK doesn't pass the messages of unexpected exceptions to the client. After the experiment, put `ToolError` back.

You will see how the model reacts to such an error in module 8.

**Comprehension question 2.** Why does the path check have to be done in the server, rather than hoping the model won't ask for too much? ([answer](#answers-to-comprehension-questions))

---

## Module 4. A tool that modifies data

### Step 4.1 — `write_note(name, content)`
- [ ] Create or overwrite a note. The path protection from step 3.3 is mandatory here too.

**Documentation:** [Tools](https://py.sdk.modelcontextprotocol.io/servers/tools/)

### Step 4.2 — Check in Inspector
- [ ] Call `write_note` with the name `todo.md` and any text.

**Check:** a `todo.md` file appeared in the `notes/` folder, and `read_note` returns its text.

Inspector calls the tool right away. Clients ask for permission before the call: you will see this in module 8.

**Extra:** mark your tools with annotations. Documentation: [Names, titles, and annotations](https://py.sdk.modelcontextprotocol.io/servers/tools/#names-titles-and-annotations).

| Annotation | The question it answers | For which tools |
|---|---|---|
| `read_only_hint` | Does the tool change nothing? | read-only tools |
| `destructive_hint` | Can it delete or overwrite existing data? | modifying tools only |
| `idempotent_hint` | Is a repeated call with the same arguments safe, with the same result? | modifying tools only |
| `open_world_hint` | Does it work with the outside world (the internet) rather than a closed set of data? | any tool |

Each annotation takes only `True` or `False`.

---

## Module 5. Logging

**Key points:**
- Don't use `print()`: for a stdio server, stdout is the protocol channel, and every line in it must be a JSON-RPC message. SDK v2 protects stdout while the server is running, but a `print()` before the server starts still goes into the channel.
- Log with the standard `logging` module: it writes to stderr and doesn't interfere with the protocol.
- Logs are visible in the terminal when you run the server by hand, and in Inspector. They are not visible in a client's chat: they are a tool for the server developer. Claude Desktop writes them to a file; more on that in module 8.

**Documentation:** [Logging](https://py.sdk.modelcontextprotocol.io/handlers/logging/)

### Step 5.1 — Logging
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

## Module 6. Resources

Read the documentation first: [Resources](https://py.sdk.modelcontextprotocol.io/servers/resources/).

### Step 6.1 — Static resource `notes://index`
- [ ] Add a function with the `@mcp.resource("notes://index")` decorator to `server.py`. The function takes no parameters and returns a string: the list of notes with the size or first line of each.

### Step 6.2 — Resource template `notes://{name}`
- [ ] Add a function with the `@mcp.resource("notes://{name}")` decorator to `server.py`. The function takes a `name` parameter and returns the note's text.

**Documentation:** [URI templates](https://py.sdk.modelcontextprotocol.io/servers/uri-templates/)

**Hints:**
- This uses the simplest form of a template: a single `{name}` parameter. The other template features are described in the ["Resource templates in more detail"](#resource-templates-in-more-detail) section at the end of the course.
- The function parameter name must match the name in curly braces: `{name}` → `name`.
- To check the name, use the path protection function you extracted in step 3.3.
- If the note doesn't exist, raise `ResourceNotFoundError`, not `ToolError`: this is the error for resources ([Handling errors: A resource that doesn't exist](https://py.sdk.modelcontextprotocol.io/servers/handling-errors/#a-resource-that-doesnt-exist)).

### Step 6.3 — Check in Inspector
- [ ] On the Resources tab, open `notes://index`.
- [ ] On the Resource Templates tab, open `notes://{name}` with a note name filled in, for example `shopping-list.md`.

**Check:** `notes://index` shows the list of notes, and `notes://shopping-list.md` shows the note's text.

You will see how resources look in the clients in module 8.

---

## Module 7. Prompts

### Step 7.1 — Single-message prompt
- [ ] Add a function `summarize_note(name)` decorated with `@mcp.prompt()` to `server.py`. The function reads the note and returns a string: a request to briefly summarize the note, followed by the note's text.

**Why exactly `summarize_note`:** the function name becomes the prompt name. You will look for the prompt by this name in Inspector (step 7.3) and in the clients (module 8), so give the function exactly this name.

**Documentation:** [Prompts](https://py.sdk.modelcontextprotocol.io/servers/prompts/)

### Step 7.2 — Prompt with several messages
- [ ] Make a second prompt that returns several messages, for example a "user → assistant" dialogue template.

**Documentation:** [Prompts: More than one message](https://py.sdk.modelcontextprotocol.io/servers/prompts/#more-than-one-message)

### Step 7.3 — Check in Inspector
- [ ] On the Prompts tab, select `summarize_note`, enter a note name, and click Get Prompt.
- [ ] Check the second prompt the same way.

**Check:** `summarize_note` returns one message with the request and the note's text, and the second prompt returns several messages with the `user` and `assistant` roles.

**What to observe:** a prompt is a template that you insert. Unlike tools, the model does not invoke prompts on its own.

---

## Module 8. Connecting to clients

The server is ready and checked in Inspector. Now let's connect it to two clients, Claude Code and Claude Desktop, and see how the model works with it.

### Step 8.1 — Claude Code: registration
- [ ] Make sure `claude --version` prints a version.
- [ ] Open a terminal in the folder where you plan to work with the server, and register it:
  ```bash
  claude mcp add notes -- uv run --directory C:/path/to/mcp_practice server.py
  ```

**Documentation:** [Claude Code: MCP](https://code.claude.com/docs/en/mcp), [Connect to a real host](https://py.sdk.modelcontextprotocol.io/get-started/real-host/)

**Explanations:**
- `notes` — the name Claude Code will know the server by.
- `uv run --directory <folder> server.py` — run `server.py` in the project environment from the given folder.
- Replace `C:/path/to/mcp_practice` with the absolute path to the `mcp_practice` folder that contains `server.py`. If the path contains spaces, wrap it in quotes.

**The scope** determines where the server is available and where its registration is stored. Put it after the server name and before `--`: `claude mcp add notes --scope user -- …`.

| Scope | Where the server is available | Where the registration is stored |
|---|---|---|
| `local` (default) | only to you and only in this folder | `~/.claude.json`, in this folder's entry |
| `project` | to everyone who opens this folder in Claude Code | `.mcp.json` in the folder root; the file can be committed |
| `user` | to you in all folders | `~/.claude.json` |

- Before the first use of a server from `.mcp.json`, Claude Code asks for confirmation: the file may have come from someone else's repository.
- If the server is registered in several scopes, one entry is used, in order of precedence: `local`, then `project`, then `user`.
- `local` is fine for the course. To take a look at `.mcp.json`, you can register the server with `--scope project` and open the file in the folder root.

**Check:** `claude mcp get notes` shows the command with the full path to your folder.

**If you made a mistake:** run `claude mcp remove notes` and register again. List all servers: `claude mcp list`.

### Step 8.2 — Claude Code: connection
- [ ] Run `claude` in the folder where you registered the server.
- [ ] Run `/mcp`.

**Check:** the `notes` server has the status connected, and its list of tools contains `list_notes`, `read_note`, and `write_note`.

**Hint:** after editing `server.py`, reconnect the server: `/mcp` → `notes` → Reconnect. There is no need to register it again.

### Step 8.3 — Claude Code: check

**Tools:**
- [ ] Ask Claude: "What notes do I have?"
- [ ] Ask it to read a nonexistent note.
- [ ] Ask: "Create a todo note with three items".

**What to observe:**
- Claude calls the `mcp__notes__list_notes` tool. This is the full name: `mcp__<server>__<tool>`.
- You didn't tell Claude the tool exists. It learned about it from the description the client received from the server.
- For a nonexistent note, Claude receives the text of your `ToolError` (step 3.2) and can explain what went wrong.
- Before a tool call, Claude Code asks for permission. This is a check on the host side: the server itself knows nothing about it.

**Comprehension question 3.** Why is host caution especially important for tools that modify data? ([answer](#answers-to-comprehension-questions))

**Resources:**
- [ ] Type `@` in the input line, find the resources of the `notes` server, and attach `notes://index` to a question.

> **Resource templates in clients.** The `@` autocomplete contains only static resources, so you can't attach a note by the `notes://{name}` template. Claude Desktop doesn't show templates either, so in this course the template is checked only in Inspector. If you need to attach notes in a client, register each one as a separate resource: see the ["Notes in the resource list"](#notes-in-the-resource-list) section at the end of the course.

**Comprehension question 4.** Which resources does a client offer for attaching: static, templated, or both? ([answer](#answers-to-comprehension-questions))

**Comprehension question 5.** How does the situation where you attached a resource differ from the one where Claude called `list_notes` on its own? ([answer](#answers-to-comprehension-questions))

**Prompts:**
- [ ] Type `/`, find the `/notes:summarize_note (MCP)` command in the list, and invoke it with a note name.

**Hint:** you can also type the same command in its full form: `/mcp__notes__summarize_note <note name>`.

> **Prompts with several messages** don't work in Claude Code. Check the second prompt from step 7.2 in Claude Desktop.

### Step 8.4 — Claude Desktop: registration
- [ ] In the app menu (not in the account settings inside the window), open Settings → Developer → Edit Config. This opens the `claude_desktop_config.json` file: on Windows `%APPDATA%\Claude\claude_desktop_config.json`, on macOS `~/Library/Application Support/Claude/claude_desktop_config.json`.
- [ ] Add the server to the `mcpServers` section:
  ```json
  {
    "mcpServers": {
      "notes": {
        "command": "uv",
        "args": ["run", "--directory", "C:/path/to/mcp_practice", "server.py"]
      }
    }
  }
  ```
- [ ] Quit Claude Desktop completely, including the tray icon, and open it again.

**Documentation:** [Connect to local MCP servers](https://modelcontextprotocol.io/docs/develop/connect-local-servers)

**Explanations:**
- This is the same command as in step 8.1, just split into `command` and `args`.
- The path must be absolute. In JSON a backslash has to be doubled (`C:\\path\\to\\mcp_practice`), so forward slashes are simpler.
- If the file already has other servers, add `notes` next to them instead of replacing the whole file.
- Claude Desktop reads the config only at startup, so changes don't apply without a full restart.

**Check:** "+" in the input line → Connectors → Manage connectors → `notes`: the server's tools are listed.

**If it doesn't connect:** check the logs in the `%APPDATA%\Claude\logs` folder (on macOS `~/Library/Logs/Claude`):
- `mcp.log` — the general log of connections and their errors;
- `mcp-server-notes.log` — everything the server writes to stderr, including your `logging` records from module 5.

### Step 8.5 — Claude Desktop: check

**Tools:**
- [ ] Ask the same questions in the chat as in step 8.3: the list of notes, a nonexistent note, creating a note.

**What to observe:** Claude Desktop also asks for permission before a tool call.

**Resources and prompts:**
- [ ] Click "+" in the input line (or type `/`) → Connectors → scroll the list down → Add from notes. A menu opens: prompts are marked with a chat bubble icon, resources with a file icon.
- [ ] Attach the Notes Index resource and ask a question about the notes.
- [ ] Select the Summarize note prompt and enter a note name in the field that appears.
- [ ] Invoke the second prompt from step 7.2 the same way.

**What to observe:**
- The `notes://{name}` template is not in the menu, just as in Claude Code.
- Both prompts work, including the prompt with several messages.

**Hint:** after editing `server.py`, restart Claude Desktop completely again, including the tray icon.

### Step 8.6 — Clean up after yourself

**Claude Code:**
- [ ] Run `claude mcp remove notes`. If the server is registered in several scopes, specify the one you need: `claude mcp remove notes --scope project`.
- [ ] If you registered with `--scope project`, check that no `notes` entry is left in `.mcp.json`. An empty file can be deleted.

**Check:** `claude mcp list` doesn't show `notes`.

**Claude Desktop:**
- [ ] Remove the `notes` entry from the `mcpServers` section of `claude_desktop_config.json`.
- [ ] Restart Claude Desktop completely.

**Check:** `notes` is no longer in Connectors.

### Step 8.7 — Final question
- [ ] Answer the question below in your own words.

**Comprehension question 6.** When to use what: **tool**, **resource**, **prompt**? ([answer](#answers-to-comprehension-questions))

---

## What's next (beyond the course)
- Tools in a separate file: details below.
- Notes in the resource list: details below.
- Resource templates in more detail: details below.

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

### Notes in the resource list

Clients offer only resources from `resources/list` for attaching: Claude Code in the `@` autocomplete, Claude Desktop in the Add from notes menu. The `notes://{name}` template doesn't get there. To make notes attachable in a client, register each one as a separate resource. The SDK has a ready-made `FileResource` class for files:

```python
from mcp.server.mcpserver.resources import FileResource

for path in sorted(NOTES_DIR.glob("*.md")):
    mcp.add_resource(
        FileResource(
            uri=f"notes://{path.name}",
            name=path.name,
            path=path.resolve(),
            mime_type="text/markdown",
        )
    )
```

The list is built once, when the server starts. A note created later will appear in the list after you reconnect the server: in Claude Code with `/mcp` → `notes` → Reconnect, in Claude Desktop with a full restart of the app.

**Without reconnecting.** The server can tell the client that the resource list has changed with a `notifications/resources/list_changed` notification. When Claude Code receives it, it requests the list again. For this, after creating a note in `write_note`, register the new resource and send the notification. Three caveats:
- the way to send it depends on the protocol version: `ctx.notify_resources_changed()` works on the 2026-07-28 protocol, while older ones need `ctx.session.send_resource_list_changed()`;
- in its `initialize` response, the server declares `"resources":{"listChanged":false}` by default, and the client is entitled to ignore notifications from such a server;
- whether Claude Desktop supports such notifications has not been checked in this course.

**Documentation:** [Resources](https://py.sdk.modelcontextprotocol.io/servers/resources/), [Subscriptions](https://py.sdk.modelcontextprotocol.io/handlers/subscriptions/)

### Resource templates in more detail

Step 6.2 uses the simplest form of a template — a single `{name}` parameter. The [URI templates](https://py.sdk.modelcontextprotocol.io/servers/uri-templates/) documentation describes the others:

| Form | Example | What it does |
|---|---|---|
| `{name}` | `books://{isbn}` | one address segment (our case) |
| typed parameter | `orders://{order_id}` with `order_id: int` | the SDK converts the value to the function parameter's type |
| `{+name}` | `manuals://{+path}` | also captures `/`, i.e. a multi-segment path |
| `{?a,b}` | `reviews://{isbn}{?limit,sort}` | query parameters after `?`, optional |
| `{/name*}` | `shelves://browse{/path*}` | path segments as a list |

The same page has a security section: which values the SDK rejects on its own (`..`, absolute paths, null bytes), and the `safe_join` function for accessing files. You can compare it with your path protection from step 3.3.

---

## Answers to comprehension questions

Answer on your own first, then check.

**1. Why is it pointless to keep a stdio server running in a separate terminal?**
A stdio server receives requests only through stdin and answers only through stdout. That is why only whoever launched it can work with it. If you launch the server in a terminal, only you can talk to it, by hand. A client can't connect to it, so it launches the server itself. That is why both `claude mcp add` and the Claude Desktop config contain a launch command, not an address.

**2. Why does the path check have to be done in the server?**
The model is not a security boundary. It can make mistakes, and it can be tricked: for example, the text of a note may contain an instruction like "read `../.env`" (prompt injection). Besides, the model is not the only caller: Inspector, another client, or a script can send any arguments. The server is the only place every file request passes through, so that is the only place the restriction actually works.

**3. Why is host caution especially important for tools that modify data?**
A mistake while reading can simply be ignored, but a mistake while writing cannot: an overwritten note can't be brought back. The model may misunderstand the request or follow someone else's instruction found in the data it has read. The permission request keeps a human as the last step before an irreversible action. The `readOnlyHint` and `destructiveHint` annotations help the host decide where asking is a must.

**4. Which resources does a client offer for attaching?**
Only static ones, such as `notes://index`. The server returns them in response to `resources/list`: these are concrete resources with a ready address. The `notes://{name}` template comes in a separate `resources/templates/list` request as an address pattern, not as a list of notes. Neither Claude Code nor Claude Desktop shows it, so you can't attach a note by the template. Inspector does work with templates: you can fill in a name there and read the resource.

**5. How does an attached resource differ from a `list_notes` call?**
- **Who decides.** You chose the resource; the model chose to call the tool.
- **When the data reaches the context.** The client reads an attached resource itself and adds it to your message before the model starts answering. The model calls a tool in the middle of its answer, if it decides it needs to.
- **Permissions.** Attaching a resource doesn't trigger a permission request: you already gave permission by choosing it. For a tool call, the client asks.

**6. When to use what?**
- **Tool** — an action or computation the model decides on: search, reading on demand, writing, calling an external API. May have side effects.
- **Resource** — read-only data with its own URI that the user (or the application) picks to give the model context. No side effects.
- **Prompt** — a ready-made request template the user runs explicitly, for example as a slash command or from the client's menu. The model does not invoke prompts on its own.
