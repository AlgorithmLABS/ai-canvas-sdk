# CUSTOM NODE KNOWLEDGE BASE

## OVERVIEW

Public contract for user-authored AI Canvas nodes: abstract base class, execution context, schema dataclasses, port enums, and parameter metadata.

## STRUCTURE

```text
custom_node/
|-- __init__.py        # CustomNode ABC and public re-exports
|-- node_context.py    # runtime context, logging, progress, cancellation
`-- models/
    |-- node_schema.py # NodeData, NodeMetadata, NodeSchema
    |-- port.py        # port direction, position, port type, Port dataclass
    `-- parameter.py   # parameter value type enum and Parameter dataclass
```

## WHERE TO LOOK

| Task | Location | Notes |
| --- | --- | --- |
| Change required node methods | `__init__.py` | `CustomNode` currently requires `get_schema()` and `run()`. |
| Change runtime context | `node_context.py` | Metadata is read-only through properties; callbacks do work. |
| Change schema fields | `models/node_schema.py` | Defaults are part of public SDK behavior. |
| Change port choices | `models/port.py` | Keep CLI validator and docs aligned. |
| Change parameter choices | `models/parameter.py` | Keep CLI validator and docs aligned. |

## CONVENTIONS

- `CustomNode.get_schema()` returns `NodeSchema`.
- `CustomNode.run(inputs, parameters, ctx)` returns a dict keyed by output port labels or IDs.
- `NodeContext.progress()` accepts 0.0 to 1.0, while proto streaming progress comments use 0.0 to 100.0.
- Input ports are expected to use `PortEnum.TARGET`; output ports use `PortEnum.SOURCE`.
- Input positions are usually `LEFT` or `TOP`; output positions are usually `RIGHT` or `BOTTOM`.
- `NodeSchema` defaults: `category="custom"`, `width=200`, `height=142`, `version="1.0.0"`.
- `Parameter.value_type` defaults to `ValueTypeEnum.STRING`.

## ANTI-PATTERNS

- Do not add abstract methods lightly; every user node subclass would be affected.
- Do not change enum string values without treating it as a wire/UI compatibility break.
- Do not remove schema defaults unless docs, examples, and CLI validation change together.
- Do not rely on `validate()` as required behavior; it is mentioned in comments but not abstract.
