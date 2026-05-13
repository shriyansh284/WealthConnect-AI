import os
from google.cloud import secretmanager
from dotenv import load_dotenv

load_dotenv()  # Load other env vars if needed


def get_secret(secret_id: str, version_id: str = "latest") -> str:
    """
    Access secrets from Google Cloud Secret Manager.
    
    Args:
        secret_id: The secret name (e.g., 'gemini-api-key')
        version_id: The version of the secret (default: 'latest')
    
    Returns:
        The secret value as a string
    """
    # Get project ID from environment or use default
    project_id = os.getenv("GCP_PROJECT_ID")
    if not project_id:
        raise RuntimeError("GCP_PROJECT_ID environment variable not set")
    
    # Create Secret Manager client
    client = secretmanager.SecretManagerServiceClient()
    
    # Build the resource name
    name = client.secret_version_path(project_id, secret_id, version_id)
    
    try:
        # Access the secret
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        raise RuntimeError(f"Failed to access secret '{secret_id}': {str(e)}")

# Try to get from Secret Manager first, fall back to environment variables
try:
    GEMINI_API_KEY = get_secret("BQ-Chatbot")  # ✅ matches your GCP secret
except RuntimeError:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")  # fallback for local dev

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY not set in Secret Manager or environment variables")

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-pro")
CORS_ALLOW_ORIGINS = os.getenv("CORS_ALLOW_ORIGINS", "*")