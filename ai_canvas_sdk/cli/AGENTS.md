# CLI KNOWLEDGE BASE

## OVERVIEW

Local development CLI for (a) loading a user node file, validating its schema, running it with test inputs (`test`), and (b) registering custom nodes to a backend over the Flow-A push CI path (`register`).

## STRUCTURE

```text
cli/
|-- __init__.py          # argparse main(), --version, test + register subcommand registration
|-- test.py              # node test command implementation
|-- register.py          # CI push registration command (token -> register -> poll)
|-- utils/
|   |-- node_loader.py   # dynamic import and CustomNode subclass discovery (test command)
|   |-- schema_validator.py
|   |-- git_changes.py   # git-diff changed top-level folder detection (register --changed)
|   `-- test_context.py  # local NodeContext implementation
|-- health.py            # empty placeholder
`-- list_nodes.py        # empty placeholder
```

## WHERE TO LOOK

| Task | Location | Notes |
| --- | --- | --- |
| Add CLI subcommand | `__init__.py` | Register parser via `subparsers`; command modules expose `setup_parser`. |
| Change node-file loading | `utils/node_loader.py` | Handles `.py` path checks, temporary `sys.path`, class discovery (test command). |
| Change schema rules | `utils/schema_validator.py` | Owns error/warning text and valid schema assumptions. |
| Change local execution | `test.py` | Loads input, parses params, applies defaults, calls `run()`. |
| Change CI registration | `register.py` | token acquire, requirements parse, AST node-name extract, register, poll, exit-code aggregation. |
| Change changed-folder detection | `utils/git_changes.py` | `git diff --name-only base head` → top-level folders; `is_unresolved_base` (all-zero/empty). |

## CONVENTIONS

- `ai-canvas-sdk test <node.py>` and `ai-canvas-sdk register` are the implemented subcommands.
- `test`: node files imported under `_loaded_node_<stem>`; only `CustomNode` subclasses defined in that module are eligible; `--input` JSON/CSV; `--params` JSON; `--validate-only` stops after schema validation.
- `register` (CI push / Flow A): registers custom node folders to the backend CI endpoints. Repo layout is top-level `<folder>/main.py` + `<folder>/req.txt` (req.txt optional). Node identity is `main.py`'s `NodeSchema.name`; the folder only groups/locates a node.
  - Auth/config from args or env: `--base-url`/`AI_CANVAS_BASE_URL`, `--client-id`/`AI_CANVAS_CLIENT_ID`, `--client-secret`/`AI_CANVAS_CLIENT_SECRET`. The CLI obtains a short-TTL bearer from `POST {base}/admin/custom-node-ci/token` and re-authenticates on HTTP 401 during polling (bounded retry).
  - Folder name MUST equal the static `NodeSchema.name` literal (extracted via AST, no node exec — so a node importing uninstalled third-party deps still validates). If the name is computed dynamically (not a literal), the CLI WARNs and defers identity validation to the backend (CNE schema extraction) rather than failing.
  - `--changed --base <sha> --head <sha>` registers only changed top-level folders (CI passes provider before/after SHAs). Edge cases: empty/all-zero base (first push) → ALL folders; a git-diff error → loud non-zero exit (never a silent exit-0); a changed top-level dir without `main.py` (deleted/non-node) → logged skip (no auto-unregister); changed files outside any folder → ignored.
  - Multi-node: attempt ALL changed folders, poll each task to terminal, exit 0 only if all COMPLETED; any FAILED/timeout/HTTP error → non-zero with a per-folder report. Exit codes gate the CI/merge.
  - Backend returns `status=failed` immediately (e.g. M-A: CI may not overwrite an admin-managed node) → the CLI surfaces it as a failure without polling.

## ANTI-PATTERNS

- Do not make imported `CustomNode` subclasses discoverable; loader filters to classes defined in the loaded file.
- Do not print local test logs to stdout from `TestNodeContext`; it deliberately uses stderr.
- Do not assume placeholders `health.py` and `list_nodes.py` contain working commands.
- Do not exec-load a node just to read its name in `register`; use the AST extractor (CI runners need not install each node's deps).
- Do not let a git-diff failure fall through to a silent success; `register --changed` must fail loud or fall back to ALL folders.

## COMMANDS

```bash
ai-canvas-sdk --version
ai-canvas-sdk test path/to/node.py --validate-only
ai-canvas-sdk test path/to/node.py -i input.csv -o output.json -v
ai-canvas-sdk register my_node                                   # single folder
ai-canvas-sdk register --changed --base "$BEFORE" --head "$AFTER" --repo-root .
```

See `docs/ci/github-actions.yml` and `docs/ci/.gitlab-ci.yml` for the push-model CI templates (the backend admin "repo connection" page can also emit a base-URL-filled copy).
