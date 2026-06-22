# CLI KNOWLEDGE BASE

## OVERVIEW

Local development CLI for loading a user node file, validating its schema, running it with test inputs, and saving/printing results.

## STRUCTURE

```text
cli/
|-- __init__.py          # argparse main(), --version, test subcommand registration
|-- test.py              # node test command implementation
|-- utils/
|   |-- node_loader.py   # dynamic import and CustomNode subclass discovery
|   |-- schema_validator.py
|   `-- test_context.py  # local NodeContext implementation
|-- health.py            # empty placeholder
|-- list_nodes.py        # empty placeholder
`-- register.py          # empty placeholder
```

## WHERE TO LOOK

| Task | Location | Notes |
| --- | --- | --- |
| Add CLI subcommand | `__init__.py` | Register parser via `subparsers`; command modules expose `setup_parser`. |
| Change node-file loading | `utils/node_loader.py` | Handles `.py` path checks, temporary `sys.path`, class discovery. |
| Change schema rules | `utils/schema_validator.py` | Owns error/warning text and valid schema assumptions. |
| Change local execution | `test.py` | Loads input, parses params, applies defaults, calls `run()`. |
| Change test logging/progress | `utils/test_context.py` | Prints ANSI logs and progress to stderr. |

## CONVENTIONS

- `ai-canvas-sdk test <node.py>` is the only implemented subcommand.
- Node files are imported under `_loaded_node_<stem>`; only `CustomNode` subclasses defined in that module are eligible.
- If multiple node classes are present, the first discovered class is used unless `--class` is supplied.
- `--input` accepts JSON or CSV. JSON objects map port labels to values; JSON arrays and CSV bind to the first input port.
- Parameter input is a JSON object string via `--params`; schema defaults fill missing parameter names before execution.
- `--validate-only` stops after schema validation.

## ANTI-PATTERNS

- Do not make imported `CustomNode` subclasses discoverable; loader currently filters to classes defined in the loaded file.
- Do not print local test logs to stdout from `TestNodeContext`; it deliberately uses stderr.
- Do not assume placeholders `health.py`, `list_nodes.py`, and `register.py` contain working commands.

## COMMANDS

```bash
ai-canvas-sdk --version
ai-canvas-sdk test path/to/node.py --validate-only
ai-canvas-sdk test path/to/node.py -i input.csv -o output.json -v
```
