"""Tool package - import all tool modules to register them."""


def register_all_tools():
    """Import all tool modules so @tool decorators fire."""
    from src.tools import notion_tools  # noqa: F401
    from src.tools import video_tools  # noqa: F401
    from src.tools import voice_tools  # noqa: F401
    from src.tools import browser_tools  # noqa: F401
    from src.tools import assembly_tools  # noqa: F401
    from src.tools import research_tools  # noqa: F401
