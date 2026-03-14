"""Browser-based tools - Playwright automation for HeyGen, Invideo, Higgsfield, CapCut."""
import asyncio
import logging
from pathlib import Path

from src.config import (
    BROWSER_PROFILES_DIR,
    MEDIA_OUTPUT_DIR,
    HEYGEN_API_KEY,
    GOOGLE_AUTH_EMAIL,
    HIGGSFIELD_EMAIL,
    HIGGSFIELD_PASSWORD,
)
from src.tools.registry import tool

logger = logging.getLogger(__name__)


async def _get_browser_context(profile_name: str):
    """Get a persistent browser context with saved session cookies."""
    from playwright.async_api import async_playwright

    profile_dir = Path(BROWSER_PROFILES_DIR) / profile_name
    profile_dir.mkdir(parents=True, exist_ok=True)

    pw = await async_playwright().start()
    browser = await pw.chromium.launch_persistent_context(
        user_data_dir=str(profile_dir),
        headless=True,
        viewport={"width": 1920, "height": 1080},
        accept_downloads=True,
    )
    return pw, browser


@tool
async def heygen_create_video(
    script: str, avatar_id: str = "", voice_id: str = "", aspect_ratio: str = "9:16"
) -> dict:
    """Create talking head video using HeyGen API.
    script: The script text for the avatar to speak
    avatar_id: HeyGen avatar ID (uses default JAH avatar if empty)
    voice_id: HeyGen voice ID (uses default JAH voice if empty)
    aspect_ratio: Video aspect ratio (16:9, 9:16)
    """
    import httpx

    # Use HeyGen's API v2 for video generation
    dimension = {"width": 1080, "height": 1920} if aspect_ratio == "9:16" else {"width": 1920, "height": 1080}

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.heygen.com/v2/video/generate",
            headers={"X-Api-Key": HEYGEN_API_KEY},
            json={
                "video_inputs": [{
                    "character": {
                        "type": "avatar",
                        "avatar_id": avatar_id or "default",
                        "avatar_style": "normal",
                    },
                    "voice": {
                        "type": "text",
                        "input_text": script,
                        "voice_id": voice_id or "default",
                    },
                }],
                "dimension": dimension,
            },
            timeout=60.0,
        )
        response.raise_for_status()
        data = response.json()

        return {
            "status": "processing",
            "video_id": data.get("data", {}).get("video_id", ""),
            "model": "heygen",
            "note": "Poll /v1/video_status.get for completion",
        }


@tool
async def invideo_create_video(prompt: str, style: str = "cinematic") -> dict:
    """Create full AI video using Invideo via browser automation.
    prompt: Detailed video prompt describing scenes and narration
    style: Visual style (cinematic, minimal, energetic, professional)
    """
    pw, browser = await _get_browser_context("invideo")

    try:
        page = await browser.new_page()
        await page.goto("https://ai.invideo.io/workspace")

        # Check if logged in, if not return login needed
        if "login" in page.url.lower():
            await page.close()
            return {
                "status": "auth_required",
                "model": "invideo",
                "note": "Browser session expired. Need to re-authenticate via Google.",
            }

        # Click create new video
        await page.click("text=Create new")
        await page.wait_for_timeout(2000)

        # Enter prompt
        prompt_input = await page.wait_for_selector("textarea", timeout=10000)
        await prompt_input.fill(prompt)

        # Select style if available
        style_btn = await page.query_selector(f"text={style}")
        if style_btn:
            await style_btn.click()

        # Submit
        await page.click("text=Generate")
        await page.wait_for_timeout(5000)

        # Get the video URL from the page
        current_url = page.url

        await page.close()
        return {
            "status": "generating",
            "model": "invideo",
            "workspace_url": current_url,
            "note": "Video is generating in Invideo. Check workspace for progress.",
        }
    except Exception as e:
        logger.error(f"Invideo browser automation failed: {e}")
        return {"status": "error", "model": "invideo", "error": str(e)}
    finally:
        await browser.close()
        await pw.stop()


@tool
async def higgsfield_create_avatar(prompt: str, reference_image: str = "") -> dict:
    """Create expressive AI avatar video using Higgsfield via browser.
    prompt: Description of the avatar performance and expressions
    reference_image: Path or URL to reference image for avatar appearance
    """
    pw, browser = await _get_browser_context("higgsfield")

    try:
        page = await browser.new_page()
        await page.goto("https://www.higgsfield.ai/")

        if "login" in page.url.lower() or "sign" in page.url.lower():
            await page.close()
            return {
                "status": "auth_required",
                "model": "higgsfield",
                "note": "Need to authenticate with Higgsfield account.",
            }

        # Navigate to creation page
        create_btn = await page.query_selector("text=Create")
        if create_btn:
            await create_btn.click()
            await page.wait_for_timeout(2000)

        # Enter prompt
        prompt_input = await page.query_selector("textarea")
        if prompt_input:
            await prompt_input.fill(prompt)

        # Upload reference image if provided
        if reference_image and not reference_image.startswith("http"):
            file_input = await page.query_selector("input[type='file']")
            if file_input:
                await file_input.set_input_files(reference_image)

        # Submit
        generate_btn = await page.query_selector("text=Generate")
        if generate_btn:
            await generate_btn.click()
            await page.wait_for_timeout(5000)

        current_url = page.url
        await page.close()

        return {
            "status": "generating",
            "model": "higgsfield",
            "workspace_url": current_url,
        }
    except Exception as e:
        logger.error(f"Higgsfield browser automation failed: {e}")
        return {"status": "error", "model": "higgsfield", "error": str(e)}
    finally:
        await browser.close()
        await pw.stop()


@tool
async def capcut_auto_captions(video_path: str, style: str = "bold") -> dict:
    """Add auto captions to video using CapCut via browser automation.
    video_path: Path to the video file to add captions to
    style: Caption style (bold, minimal, colorful, subtitle)
    """
    pw, browser = await _get_browser_context("capcut")

    try:
        page = await browser.new_page()
        await page.goto("https://www.capcut.com/editor")

        if "login" in page.url.lower():
            await page.close()
            return {
                "status": "auth_required",
                "model": "capcut",
                "note": "Need to authenticate with CapCut/Google account.",
            }

        # Upload video
        file_input = await page.wait_for_selector("input[type='file']", timeout=15000)
        if file_input:
            await file_input.set_input_files(video_path)
            await page.wait_for_timeout(10000)  # Wait for upload

        # Click auto captions
        captions_btn = await page.query_selector("text=Auto captions")
        if captions_btn:
            await captions_btn.click()
            await page.wait_for_timeout(3000)

        # Generate captions
        generate_btn = await page.query_selector("text=Generate")
        if generate_btn:
            await generate_btn.click()
            await page.wait_for_timeout(15000)  # Wait for caption generation

        # Export
        export_btn = await page.query_selector("text=Export")
        if export_btn:
            await export_btn.click()
            await page.wait_for_timeout(5000)

        await page.close()
        return {
            "status": "processing",
            "model": "capcut",
            "input_video": video_path,
            "note": "Captions generated. Check CapCut for export download.",
        }
    except Exception as e:
        logger.error(f"CapCut browser automation failed: {e}")
        return {"status": "error", "model": "capcut", "error": str(e)}
    finally:
        await browser.close()
        await pw.stop()
