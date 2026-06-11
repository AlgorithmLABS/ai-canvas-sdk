# SDK PACKAGE KNOWLEDGE BASE

## OVERVIEW

Installed Python package containing the public SDK API, CLI package, node contract, serializer, and generated gRPC bindings.

## STRUCTURE

```text
ai_canvas_sdk/
|-- __init__.py        # public import surface and dynamic __version__
|-- serialization.py   # pandas/protobuf conversion
|-- cli/               # console-script package and node testing commands
|-- custom_node/       # public CustomNode contract and schema models
`-- grpc/              # generated protobuf/gRPC Python files
```

## WHERE TO LOOK

| Task | Location | Notes |
| --- | --- | --- |
| Add public export | `__init__.py` | Keep `__all__` in sync with imports. |
| Change node API | `custom_node/` | Update docs/examples if public shape changes. |
| Change CLI behavior | `cli/` | Console-script package; entry point is `__init__.py:main`. |
| Change serialization | `serialization.py` | Check protobuf `PortData` fields and docs data-type claims. |
| Change wire messages | `../proto/custom_node_service.proto` | Regenerate `grpc/` outputs after proto edits. |

## CONVENTIONS

- Public exports flow through `ai_canvas_sdk/__init__.py`; keep import names stable unless intentionally breaking SDK API.
- `__version__` is imported from generated `ai_canvas_sdk/_version.py` and falls back to `0.0.0+unknown`.
- `DataSerializer` uses pandas and pyarrow at runtime; changes here affect package import cost because it is re-exported at root.
- DataFrame serialization thresholds are embedded constants: 10,000 rows for JSON, 100,000 rows large-data guard, 3 MiB gRPC size limit.
- Generated files under `grpc/` use relative imports patched by `scripts/compile_protos.py`.

## ANTI-PATTERNS

- Do not edit generated `grpc/` files directly.
- Do not bypass `__all__` when adding or removing public root exports.
- Do not move heavy runtime dependencies into optional extras unless root imports stop requiring them.

## LOCAL CHECKS

```bash
python3 scripts/compile_protos.py
python3 -m build
```
