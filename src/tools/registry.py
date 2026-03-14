"""Tool registry - @tool decorator + dispatch."""
import inspect
import json
import logging
from typing import Callable, Any, get_type_hints

logger = logging.getLogger(__name__)

_REGISTRY: dict[str, Callable] = {}
_DEFINITIONS: dict[str, dict] = {}

# Python type -> JSON Schema type
_TYPE_MAP = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
    list: "array",
    dict: "object",
}


def tool(func: Callable) -> Callable:
    """Register a function as an Anthropic-compatible tool."""
    name = func.__name__
    hints = get_type_hints(func)
    sig = inspect.signature(func)

    # Strip return type hint
    hints.pop("return", None)

    properties = {}
    required = []

    for param_name, param in sig.parameters.items():
        annotation = hints.get(param_name, str)
        json_type = _TYPE_MAP.get(annotation, "string")

        prop: dict[str, Any] = {"type": json_type}

        # Extract description from docstring (param_name: description)
        if func.__doc__:
            for line in func.__doc__.splitlines():
                stripped = line.strip()
                if stripped.startswith(f"{param_name}:"):
                    prop["description"] = stripped.split(":", 1)[1].strip()
                    break

        properties[param_name] = prop

        if param.default is inspect.Parameter.empty:
            required.append(param_name)

    definition = {
        "name": name,
        "description": (func.__doc__ or "").split("\n")[0].strip(),
        "input_schema": {
            "type": "object",
            "properties": properties,
            "required": required,
        },
    }

    _REGISTRY[name] = func
    _DEFINITIONS[name] = definition
    return func


def get_all_tools() -> list[dict]:
    """Return all registered tool definitions."""
    return list(_DEFINITIONS.values())


def get_tools_by_names(names: list[str]) -> list[dict]:
    """Return tool definitions for specific tool names."""
    return [_DEFINITIONS[n] for n in names if n in _DEFINITIONS]


async def run_tool(name: str, inputs: dict) -> str:
    """Execute a registered tool and return JSON string result."""
    if name not in _REGISTRY:
        return json.dumps({"error": f"Unknown tool: {name}"})

    func = _REGISTRY[name]
    try:
        if inspect.iscoroutinefunction(func):
            result = await func(**inputs)
        else:
            result = func(**inputs)
        return json.dumps(result, default=str)
    except Exception as e:
        logger.error(f"Tool {name} failed: {e}", exc_info=True)
        return json.dumps({"error": str(e)})
