"""Research tools - web search, GitHub monitoring, competitor scanning."""
import logging

import httpx

from src.config import PERPLEXITY_API_KEY, OPENAI_API_KEY
from src.tools.registry import tool

logger = logging.getLogger(__name__)

GITHUB_API = "https://api.github.com"


@tool
async def search_web(query: str, focus: str = "internet") -> dict:
    """Search the web using Perplexity for research and trend detection.
    query: Search query
    focus: Search focus (internet, news, academic, social)
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.perplexity.ai/chat/completions",
            headers={"Authorization": f"Bearer {PERPLEXITY_API_KEY}"},
            json={
                "model": "sonar",
                "messages": [
                    {"role": "user", "content": query},
                ],
                "search_focus": focus,
            },
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()

        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        citations = data.get("citations", [])

        return {
            "answer": content,
            "citations": citations,
            "query": query,
        }


@tool
async def search_github_repos(query: str, language: str = "", sort: str = "updated") -> dict:
    """Search GitHub repositories for relevant open-source projects.
    query: Search query (e.g. 'claude agent', 'mcp server')
    language: Filter by language (python, typescript, etc.)
    sort: Sort by (stars, forks, updated)
    """
    params = {"q": query, "sort": sort, "per_page": 10}
    if language:
        params["q"] += f" language:{language}"

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{GITHUB_API}/search/repositories",
            params=params,
            headers={"Accept": "application/vnd.github.v3+json"},
            timeout=15.0,
        )
        response.raise_for_status()
        data = response.json()

        repos = []
        for repo in data.get("items", []):
            repos.append({
                "name": repo["full_name"],
                "description": repo.get("description", "")[:200],
                "stars": repo["stargazers_count"],
                "updated": repo["updated_at"],
                "url": repo["html_url"],
            })

        return {"repos": repos, "total": data.get("total_count", 0)}


@tool
async def scan_competitors(competitor_handles: list) -> dict:
    """Scan competitor social media for recent high-performing content.
    competitor_handles: List of competitor handles/names to scan
    """
    # Use Perplexity to search for recent competitor content
    results = {}

    async with httpx.AsyncClient() as client:
        for handle in competitor_handles:
            response = await client.post(
                "https://api.perplexity.ai/chat/completions",
                headers={"Authorization": f"Bearer {PERPLEXITY_API_KEY}"},
                json={
                    "model": "sonar",
                    "messages": [
                        {
                            "role": "user",
                            "content": (
                                f"What are the most recent and popular videos or posts from "
                                f"@{handle} on TikTok, YouTube, or Instagram in the last 7 days? "
                                f"Include view counts and topics if available."
                            ),
                        },
                    ],
                    "search_focus": "social",
                },
                timeout=30.0,
            )

            if response.status_code == 200:
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                results[handle] = {"summary": content}
            else:
                results[handle] = {"error": f"Search failed: {response.status_code}"}

    return {"competitors": results, "count": len(competitor_handles)}


@tool
async def check_claude_updates() -> dict:
    """Check for recent Claude Code and Anthropic SDK updates on GitHub."""
    repos_to_check = [
        "anthropics/claude-code",
        "anthropics/anthropic-sdk-python",
        "modelcontextprotocol/servers",
    ]

    updates = {}
    async with httpx.AsyncClient() as client:
        for repo in repos_to_check:
            # Check recent commits
            response = await client.get(
                f"{GITHUB_API}/repos/{repo}/commits",
                params={"per_page": 5},
                headers={"Accept": "application/vnd.github.v3+json"},
                timeout=15.0,
            )

            if response.status_code == 200:
                commits = response.json()
                updates[repo] = [
                    {
                        "message": c["commit"]["message"].split("\n")[0][:100],
                        "date": c["commit"]["author"]["date"],
                        "sha": c["sha"][:7],
                    }
                    for c in commits
                ]
            else:
                updates[repo] = {"error": f"Failed: {response.status_code}"}

            # Check latest release
            release_response = await client.get(
                f"{GITHUB_API}/repos/{repo}/releases/latest",
                headers={"Accept": "application/vnd.github.v3+json"},
                timeout=15.0,
            )
            if release_response.status_code == 200:
                release = release_response.json()
                updates[f"{repo}_release"] = {
                    "tag": release.get("tag_name", ""),
                    "name": release.get("name", ""),
                    "date": release.get("published_at", ""),
                }

    return {"updates": updates}


@tool
async def check_openclaw_updates() -> dict:
    """Check for recent OpenClaw project updates on GitHub."""
    # Search for OpenClaw repos
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{GITHUB_API}/search/repositories",
            params={"q": "openclaw", "sort": "updated", "per_page": 5},
            headers={"Accept": "application/vnd.github.v3+json"},
            timeout=15.0,
        )

        if response.status_code != 200:
            return {"error": f"Search failed: {response.status_code}"}

        repos = response.json().get("items", [])
        updates = {}

        for repo in repos:
            full_name = repo["full_name"]
            # Get recent commits for each repo
            commits_resp = await client.get(
                f"{GITHUB_API}/repos/{full_name}/commits",
                params={"per_page": 3},
                headers={"Accept": "application/vnd.github.v3+json"},
                timeout=15.0,
            )

            if commits_resp.status_code == 200:
                commits = commits_resp.json()
                updates[full_name] = {
                    "description": repo.get("description", "")[:200],
                    "stars": repo["stargazers_count"],
                    "recent_commits": [
                        {
                            "message": c["commit"]["message"].split("\n")[0][:100],
                            "date": c["commit"]["author"]["date"],
                        }
                        for c in commits
                    ],
                }

        return {"repos": updates}
