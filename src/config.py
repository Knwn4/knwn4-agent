"""Configuration loaded from environment variables (injected by Doppler)."""
import os

# --- API Keys ---
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_USER_ID = int(os.environ.get("TELEGRAM_USER_ID", "0"))
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY", "")
FAL_KEY = os.environ.get("FAL_KEY", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
PI_API_KEY = os.environ.get("PI_API_KEY", "")
HEYGEN_API_KEY = os.environ.get("HEYGEN_API_KEY", "")
NOTION_API_KEY = os.environ.get("NOTION_API_KEY", "")
PERPLEXITY_API_KEY = os.environ.get("PERPLEXITY_API_KEY", "")
N8N_API_KEY = os.environ.get("N8N_API_KEY", "")

# --- Browser Auth ---
GOOGLE_AUTH_EMAIL = os.environ.get("GOOGLE_AUTH_EMAIL", "")
GOOGLE_AUTH_PASSWORD = os.environ.get("GOOGLE_AUTH_PASSWORD", "")
HIGGSFIELD_EMAIL = os.environ.get("HIGGSFIELD_EMAIL", "")
HIGGSFIELD_PASSWORD = os.environ.get("HIGGSFIELD_PASSWORD", "")

# --- Model Tiers ---
MODEL_ORCHESTRATOR = "claude-sonnet-4-5-latest"
MODEL_WORKER = "claude-haiku-4-5-latest"
MODEL_REASONING = "claude-opus-4-5-latest"

# --- Limits ---
MAX_TOKENS_DEFAULT = 4096
MAX_AGENTIC_TURNS = 25

# --- Notion Data Sources ---
NOTION_CONTENT_DB = "collection://2d3ed1c0-3a9c-8169-ae90-000b513db7c2"
NOTION_TOOLS_DB = "collection://9c5a3981-682b-40cf-8b73-cca0ac6ed6d8"
NOTION_AUTOMATION_LOG_DB = "collection://5eec6a60-a0d2-4b04-a7c5-e476a592ef86"
NOTION_PROMPTS_DB = "collection://9ab25adf-bbfa-42cf-95da-9be2120ddcba"
NOTION_TASK_DB = "collection://2d3ed1c0-3a9c-8147-8dd2-000b69aed75a"

# --- External URLs ---
N8N_BASE_URL = "https://n8n.knwn4.com"

# --- Paths ---
CONTENT_PROJECT_DIR = "/opt/knwn4-content"  # Clone of CONTENTCREATORJAH on VPS
BROWSER_PROFILES_DIR = "/opt/knwn4-agent/browser-profiles"
MEDIA_OUTPUT_DIR = "/opt/knwn4-agent/media"
