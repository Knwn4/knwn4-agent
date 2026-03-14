"""Notion tools - Content DB, Tools DB, Automation Log CRUD via Notion API."""
import logging
from datetime import datetime, timezone

import httpx

from src.config import NOTION_API_KEY, NOTION_CONTENT_DB, NOTION_AUTOMATION_LOG_DB
from src.tools.registry import tool

logger = logging.getLogger(__name__)

NOTION_API_BASE = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"


def _notion_headers() -> dict:
    return {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def _extract_db_id(collection_uri: str) -> str:
    """Extract database ID from collection:// URI."""
    return collection_uri.replace("collection://", "")


async def _notion_request(method: str, path: str, json_body: dict | None = None) -> dict:
    """Make an authenticated Notion API request."""
    async with httpx.AsyncClient() as client:
        response = await client.request(
            method=method,
            url=f"{NOTION_API_BASE}{path}",
            headers=_notion_headers(),
            json=json_body,
            timeout=30.0,
        )
        response.raise_for_status()
        return response.json()


@tool
async def search_content_pipeline(query: str, status: str = "") -> dict:
    """Search the content pipeline by text query and optional status filter.
    query: Search text to match against content titles and descriptions
    status: Filter by status (e.g. 'Idea', 'Scripting', 'Film', 'Edit', 'Scheduled', 'Published')
    """
    db_id = _extract_db_id(NOTION_CONTENT_DB)

    filter_conditions = []
    if query:
        filter_conditions.append({
            "property": "Name",
            "title": {"contains": query},
        })
    if status:
        filter_conditions.append({
            "property": "Status",
            "status": {"equals": status},
        })

    body = {"page_size": 20}
    if len(filter_conditions) == 1:
        body["filter"] = filter_conditions[0]
    elif len(filter_conditions) > 1:
        body["filter"] = {"and": filter_conditions}

    result = await _notion_request("POST", f"/databases/{db_id}/query", body)

    items = []
    for page in result.get("results", []):
        props = page.get("properties", {})
        title_prop = props.get("Name", {}).get("title", [])
        title = title_prop[0]["plain_text"] if title_prop else "Untitled"
        status_prop = props.get("Status", {}).get("status", {})

        items.append({
            "id": page["id"],
            "title": title,
            "status": status_prop.get("name", "Unknown") if status_prop else "Unknown",
            "url": page.get("url", ""),
        })

    return {"items": items, "count": len(items)}


@tool
async def get_pipeline_health() -> dict:
    """Get content pipeline health - count of items per status."""
    db_id = _extract_db_id(NOTION_CONTENT_DB)

    statuses = ["Idea", "Scripting", "Film", "Edit", "Scheduled", "Published"]
    health = {}

    for status in statuses:
        body = {
            "filter": {"property": "Status", "status": {"equals": status}},
            "page_size": 1,
        }
        result = await _notion_request("POST", f"/databases/{db_id}/query", body)
        # Use has_more + results length for approximate count
        count = len(result.get("results", []))
        if result.get("has_more"):
            # Fetch full count
            body["page_size"] = 100
            full_result = await _notion_request("POST", f"/databases/{db_id}/query", body)
            count = len(full_result.get("results", []))
        health[status] = count

    return {"pipeline": health, "total": sum(health.values())}


@tool
async def update_content_status(page_id: str, new_status: str) -> dict:
    """Update the status of a content item in the pipeline.
    page_id: Notion page ID of the content item
    new_status: New status value (Idea, Scripting, Film, Edit, Scheduled, Published)
    """
    body = {
        "properties": {
            "Status": {"status": {"name": new_status}},
        }
    }
    result = await _notion_request("PATCH", f"/pages/{page_id}", body)
    return {"success": True, "page_id": page_id, "new_status": new_status}


@tool
async def create_content_idea(title: str, pillar: str, hook_angle: str, notes: str = "") -> dict:
    """Create a new content idea in the pipeline.
    title: Title of the content idea
    pillar: Content pillar (AI Tools, Money Online, Business Growth, Personal Brand)
    hook_angle: The hook angle or approach for this content
    notes: Additional notes or context
    """
    db_id = _extract_db_id(NOTION_CONTENT_DB)

    body = {
        "parent": {"database_id": db_id},
        "properties": {
            "Name": {"title": [{"text": {"content": title}}]},
            "Status": {"status": {"name": "Idea"}},
            "Pillar": {"select": {"name": pillar}},
        },
    }

    # Add hook angle and notes to page content
    children = []
    if hook_angle:
        children.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {"rich_text": [{"text": {"content": "Hook Angle"}}]},
        })
        children.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {"rich_text": [{"text": {"content": hook_angle}}]},
        })
    if notes:
        children.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {"rich_text": [{"text": {"content": "Notes"}}]},
        })
        children.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {"rich_text": [{"text": {"content": notes}}]},
        })

    if children:
        body["children"] = children

    result = await _notion_request("POST", "/pages", body)
    return {
        "success": True,
        "page_id": result["id"],
        "title": title,
        "url": result.get("url", ""),
    }


@tool
async def log_automation_action(action: str, details: str, status: str = "Success") -> dict:
    """Log an automated action to the Automation Log DB.
    action: Short description of the action taken
    details: Detailed description of what happened
    status: Result status (Success, Failed, Partial)
    """
    db_id = _extract_db_id(NOTION_AUTOMATION_LOG_DB)

    body = {
        "parent": {"database_id": db_id},
        "properties": {
            "Name": {"title": [{"text": {"content": action}}]},
            "Status": {"select": {"name": status}},
            "Details": {"rich_text": [{"text": {"content": details}}]},
            "Timestamp": {
                "date": {"start": datetime.now(timezone.utc).isoformat()},
            },
        },
    }

    result = await _notion_request("POST", "/pages", body)
    return {"success": True, "log_id": result["id"]}
