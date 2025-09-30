#!/usr/bin/env python3
"""
Script to list all SSO providers in Supabase.
This script retrieves and displays all configured SAML providers.
"""

import sys
import requests
import json
from pathlib import Path
import logging
import re
import urllib3

# Disable SSL warnings when verify=False is used
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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


def list_sso_providers(service_role_key: str, api_url: str) -> dict:
    """
    List all SSO providers from Supabase via the Admin API.
    
    Args:
        service_role_key: Supabase service role key for authentication
        api_url: Base URL for the Supabase API
    
    Returns:
        dict: Response from the API
    """
    url = f"{api_url}/auth/v1/admin/sso/providers"
    
    headers = {
        'APIKey': service_role_key,
        'Authorization': f'Bearer {service_role_key}',
        'Content-Type': 'application/json'
    }
    
    logger.info("🔄 Retrieving SSO providers from Supabase API...")
    logger.info(f"   URL: {url}")
    logger.info("")
    
    try:
        response = requests.get(url, headers=headers, timeout=10, verify=False)
        
        # Log the response
        logger.info("📥 Response from Supabase API:")
        logger.info(f"   Status Code: {response.status_code}")
        logger.info("")
        
        if response.status_code == 200:
            try:
                response_json = response.json()
                
                # Display providers in a formatted way
                if isinstance(response_json, list) and len(response_json) > 0:
                    logger.info("✅ SSO Providers Found:")
                    logger.info("=" * 50)
                    
                    for i, provider in enumerate(response_json, 1):
                        logger.info(f"\n🔹 Provider #{i}")
                        logger.info(f"   ID: {provider.get('id', 'N/A')}")
                        logger.info(f"   Type: {provider.get('type', 'N/A')}")
                        logger.info(f"   Metadata URL: {provider.get('metadata_url', 'N/A')}")
                        
                        domains = provider.get('domains', [])
                        if domains:
                            logger.info(f"   Domains: {', '.join(domains)}")
                        else:
                            logger.info("   Domains: None configured")
                        
                        # Show additional fields if available
                        if provider.get('created_at'):
                            logger.info(f"   Created: {provider.get('created_at')}")
                        if provider.get('updated_at'):
                            logger.info(f"   Updated: {provider.get('updated_at')}")
                
                elif isinstance(response_json, list) and len(response_json) == 0:
                    logger.info("📭 No SSO providers configured")
                    logger.info("")
                    logger.info("💡 To add a SAML provider, run:")
                    logger.info("   make saml-add-provider METADATA_URL='...' DOMAINS='...'")
                
                else:
                    logger.info("Raw Response:")
                    logger.info(json.dumps(response_json, indent=2))
                
                return response_json
                
            except json.JSONDecodeError:
                logger.info("Response Body (raw):")
                logger.info(response.text)
                return {}
        else:
            logger.error(f"❌ Failed to retrieve SSO providers. Status code: {response.status_code}")
            try:
                error_response = response.json()
                logger.error("Error details:")
                logger.error(json.dumps(error_response, indent=2))
            except json.JSONDecodeError:
                logger.error("Error response (raw):")
                logger.error(response.text)
            return {}
            
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error making request: {e}")
        logger.error("")
        logger.error("💡 Make sure Supabase is running:")
        logger.error("   cd supabase && docker-compose up -d")
        return {}


def main():
    """Main function to list SSO providers."""
    logger.info("🔧 StackAI SSO Providers List")
    logger.info("=" * 40)
    logger.info("")
    
    # Get the project root directory (go up two levels from scripts/supabase)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    supabase_env_path = project_root / "supabase" / ".env"
    
    # Check if .env file exists
    if not supabase_env_path.exists():
        logger.error(f"❌ Supabase .env file not found at {supabase_env_path}")
        logger.error("")
        logger.error("💡 Please run the environment setup script first:")
        logger.error("   make install-environment-variables")
        sys.exit(1)
    
    # Parse the .env file to get the SERVICE_ROLE_KEY and API_EXTERNAL_URL
    env_vars = parse_env_file(supabase_env_path)
    service_role_key = env_vars.get('SERVICE_ROLE_KEY')
    api_url = env_vars.get('API_EXTERNAL_URL')
    
    if not service_role_key:
        logger.error("❌ SERVICE_ROLE_KEY not found in the .env file")
        sys.exit(1)
    
    if not api_url:
        logger.error("❌ API_EXTERNAL_URL not found in the .env file")
        sys.exit(1)
    
    # List the SSO providers
    result = list_sso_providers(
        service_role_key=service_role_key,
        api_url=api_url
    )
    
    if not result and result != []:  # Allow empty list as valid result
        sys.exit(1)


if __name__ == "__main__":
    main()
