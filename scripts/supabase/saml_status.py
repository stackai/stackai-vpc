# This script will show the status of the SAML authentication in the instance
# - It should check the .env file to see if SAML_ENABLED is true
# - If true, it should return two URLs (built from the supabase/.env file):
#   - API_EXTERNAL_URL + /auth/v1/sso/saml/acs (Assertion Consumer Service)
#   - API_EXTERNAL_URL + /auth/v1/sso/saml/metadata (SAML Metadata)
# - If false, it should return a message saying that SAML is not enabled

import sys
import re
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)

def parse_env_file(env_path: Path) -> dict:
    """Parse .env file and return a dictionary of key-value pairs"""
    env_vars = {}
    with open(env_path, 'r') as file:
        content = file.read()
    
    # Pattern to match KEY=VALUE or KEY="VALUE" (including multi-line quoted values)
    pattern = r'^([A-Z_][A-Z0-9_]*)=(?:"([^"]*(?:\n[^"]*)*)"|([^\n]*))'
    
    for match in re.finditer(pattern, content, re.MULTILINE):
        key = match.group(1)
        # Use group 2 if quoted value, otherwise group 3
        value = match.group(2) if match.group(2) is not None else match.group(3)
        env_vars[key] = value
    
    return env_vars

def main():
    """Main function to show the status of the SAML authentication in the instance"""
    # Get the project root directory (go up two levels from scripts/supabase)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    supabase_env_path = project_root / "supabase" / ".env"

    # Check if the file exists
    if not supabase_env_path.exists():
        logger.error(f"❌ Supabase .env file not found at {supabase_env_path}")
        sys.exit(1)

    # Parse the .env file
    env_vars = parse_env_file(supabase_env_path)

    # Get the API_EXTERNAL_URL
    api_external_url = env_vars.get("API_EXTERNAL_URL")
    if not api_external_url:
        logger.error("❌ API_EXTERNAL_URL not found in the .env file")
        sys.exit(1)

    # Get the SAML_ENABLED
    saml_enabled = env_vars.get("SAML_ENABLED", "false").lower()
    
    if saml_enabled == "true":
        logger.info("✅ SAML is ENABLED")
        # Build the SAML URLs
        saml_acs_url = f"{api_external_url}/auth/v1/sso/saml/acs"
        saml_metadata_url = f"{api_external_url}/auth/v1/sso/saml/metadata"

        # Print the SAML URLs
        logger.info("🔗 SAML Endpoints:")
        logger.info(f"   • Assertion Consumer Service (ACS): {saml_acs_url}")
        logger.info(f"   • Metadata URL: {saml_metadata_url}")
    else:
        logger.info("❌ SAML is NOT ENABLED")
        logger.info("")
        logger.info("💡 To enable SAML, run:")
        logger.info("   make saml-enable")

if __name__ == "__main__":
    main()