"""Test tool registry."""
import pytest
from src.tools.registry import tool, get_all_tools, run_tool, _REGISTRY, _DEFINITIONS


# Reset registry before each test
@pytest.fixture(autouse=True)
def clean_registry():
    _REGISTRY.clear()
    _DEFINITIONS.clear()
    yield
    _REGISTRY.clear()
    _DEFINITIONS.clear()


def test_tool_decorator_registers_function():
    @tool
    def greet(name: str) -> str:
        """Say hello to someone."""
        return {"greeting": f"Hello, {name}"}

    tools = get_all_tools()
    assert len(tools) == 1
    assert tools[0]["name"] == "greet"
    assert tools[0]["input_schema"]["required"] == ["name"]


def test_tool_with_optional_params():
    @tool
    def search(query: str, limit: int = 10) -> dict:
        """Search for content."""
        return {"results": [], "query": query}

    tools = get_all_tools()
    assert "query" in tools[0]["input_schema"]["required"]
    assert "limit" not in tools[0]["input_schema"]["required"]


@pytest.mark.asyncio
async def test_run_tool_executes():
    @tool
    def add(a: int, b: int) -> dict:
        """Add two numbers."""
        return {"sum": a + b}

    result = await run_tool("add", {"a": 3, "b": 4})
    assert '"sum": 7' in result


@pytest.mark.asyncio
async def test_run_async_tool():
    @tool
    async def async_greet(name: str) -> dict:
        """Async greeting."""
        return {"greeting": f"Hi {name}"}

    result = await run_tool("async_greet", {"name": "Eli"})
    assert "Hi Eli" in result


@pytest.mark.asyncio
async def test_run_unknown_tool_returns_error():
    result = await run_tool("nonexistent", {})
    assert "error" in result
