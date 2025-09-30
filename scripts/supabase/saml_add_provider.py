#!/usr/bin/env python3
"""
Script to add a SAML provider to Supabase.
This script accepts a metadata_url and a list of domains (comma-separated).
"""

import sys
import argparse
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


def add_saml_provider(metadata_url: str, domains: list, service_role_key: str, api_url: str = "http://localhost:8443") -> dict:
    """
    Add a SAML provider to Supabase via the Admin API.
    
    Args:
        metadata_url: The SAML metadata URL from the Identity Provider
        domains: List of domains that can authenticate with this provider
        service_role_key: Supabase service role key for authentication
        api_url: Base URL for the Supabase API (default: http://localhost:8443)
    
    Returns:
        dict: Response from the API
    """
    url = f"{api_url}/auth/v1/admin/sso/providers"
    
    headers = {
        'APIKey': service_role_key,
        'Authorization': f'Bearer {service_role_key}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        'type': 'saml',
        'metadata_url': metadata_url,
        'domains': domains
    }
    
    logger.info("🔄 Sending request to Supabase API...")
    logger.info(f"   URL: {url}")
    logger.info(f"   Metadata URL: {metadata_url}")
    logger.info(f"   Domains: {', '.join(domains)}")
    logger.info("")
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10, verify=False)
        
        # Log the response
        logger.info("📥 Response from Supabase API:")
        logger.info(f"   Status Code: {response.status_code}")
        logger.info("")
        
        try:
            response_json = response.json()
            logger.info("Response Body:")
            logger.info(json.dumps(response_json, indent=2))
        except json.JSONDecodeError:
            logger.info("Response Body (raw):")
            logger.info(response.text)
        
        if response.status_code in [200, 201]:
            logger.info("")
            logger.info("✅ SAML provider added successfully!")
            return response_json if 'response_json' in locals() else {'status': 'success'}
        else:
            logger.error("")
            logger.error(f"❌ Failed to add SAML provider. Status code: {response.status_code}")
            return {}
            
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error making request: {e}")
        logger.error("")
        logger.error("💡 Make sure Supabase is running:")
        logger.error("   cd supabase && docker-compose up -d")
        return {}


def main():
    """Main function to add a SAML provider."""
    parser = argparse.ArgumentParser(
        description='Add a SAML provider to Supabase',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single domain
  python saml_add_provider.py --metadata-url "https://idp.example.com/metadata" --domains "example.com"
  
  # Multiple domains (comma-separated)
  python saml_add_provider.py --metadata-url "https://idp.example.com/metadata" --domains "example.com,test.com"
        """
    )
    
    parser.add_argument(
        '--metadata-url',
        required=True,
        help='SAML metadata URL from your Identity Provider'
    )
    
    parser.add_argument(
        '--domains',
        required=True,
        help='Domain(s) that can use this provider (comma-separated for multiple)'
    )
    
    parser.add_argument(
        '--api-url',
        default='http://localhost:8443',
        help='Supabase API base URL (default: http://localhost:8443)'
    )
    
    args = parser.parse_args()
    
    logger.info("🔧 StackAI SAML Provider Configuration")
    logger.info("=" * 50)
    logger.info("")
    
    # Parse domains (split by comma and strip whitespace)
    domains = [d.strip() for d in args.domains.split(',') if d.strip()]
    
    if not domains:
        logger.error("❌ No valid domains provided")
        sys.exit(1)
    
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
    
    # Parse the .env file to get the SERVICE_ROLE_KEY
    env_vars = parse_env_file(supabase_env_path)
    service_role_key = env_vars.get('SERVICE_ROLE_KEY')
    
    if not service_role_key:
        logger.error("❌ SERVICE_ROLE_KEY not found in the .env file")
        sys.exit(1)
    
    # Add the SAML provider
    result = add_saml_provider(
        metadata_url=args.metadata_url,
        domains=domains,
        service_role_key=service_role_key,
        api_url=env_vars.get("API_EXTERNAL_URL")
    )
    
    if result:
        logger.info("")
        logger.info("📋 Next steps:")
        logger.info("1. Test SSO login with one of the configured domains")
        logger.info("2. Check your Identity Provider logs if authentication fails")
        logger.info("3. View SAML metadata at: /auth/v1/sso/saml/metadata")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
