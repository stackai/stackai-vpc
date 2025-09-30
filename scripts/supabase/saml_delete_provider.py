#!/usr/bin/env python3
"""
Script to delete a SAML provider from Supabase by its UUID.
This script accepts a provider_id (UUID) and removes the provider.
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


def delete_sso_provider(provider_id: str, service_role_key: str, api_url: str) -> bool:
    """
    Delete an SSO provider from Supabase via the Admin API.
    
    Args:
        provider_id: UUID of the provider to delete
        service_role_key: Supabase service role key for authentication
        api_url: Base URL for the Supabase API
    
    Returns:
        bool: True if successful, False otherwise
    """
    url = f"{api_url}/auth/v1/admin/sso/providers/{provider_id}"
    
    headers = {
        'APIKey': service_role_key,
        'Authorization': f'Bearer {service_role_key}',
        'Content-Type': 'application/json'
    }
    
    logger.info("🔄 Deleting SSO provider from Supabase API...")
    logger.info(f"   URL: {url}")
    logger.info(f"   Provider ID: {provider_id}")
    logger.info("")
    
    try:
        response = requests.delete(url, headers=headers, timeout=10, verify=False)
        
        # Log the response
        logger.info("📥 Response from Supabase API:")
        logger.info(f"   Status Code: {response.status_code}")
        logger.info("")
        
        if response.status_code == 204:
            # 204 No Content is the typical success response for DELETE
            logger.info("✅ SSO provider deleted successfully!")
            return True
        elif response.status_code == 200:
            # Some APIs return 200 with content
            try:
                response_json = response.json()
                logger.info("Response Body:")
                logger.info(json.dumps(response_json, indent=2))
                logger.info("")
                logger.info("✅ SSO provider deleted successfully!")
                return True
            except json.JSONDecodeError:
                logger.info("✅ SSO provider deleted successfully!")
                return True
        elif response.status_code == 404:
            logger.error("❌ Provider not found!")
            logger.error("💡 Use 'make saml-list-providers' to see available providers")
            return False
        else:
            logger.error(f"❌ Failed to delete SSO provider. Status code: {response.status_code}")
            try:
                error_response = response.json()
                logger.error("Error details:")
                logger.error(json.dumps(error_response, indent=2))
            except json.JSONDecodeError:
                logger.error("Error response (raw):")
                logger.error(response.text)
            return False
            
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error making request: {e}")
        logger.error("")
        logger.error("💡 Make sure Supabase is running:")
        logger.error("   cd supabase && docker-compose up -d")
        return False


def validate_uuid(uuid_string: str) -> bool:
    """
    Validate if a string is a valid UUID format.
    
    Args:
        uuid_string: String to validate
    
    Returns:
        bool: True if valid UUID format, False otherwise
    """
    import uuid
    try:
        uuid.UUID(uuid_string)
        return True
    except ValueError:
        return False


def main():
    """Main function to delete an SSO provider."""
    parser = argparse.ArgumentParser(
        description='Delete an SSO provider from Supabase',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Delete a provider by UUID
  python saml_delete_provider.py --provider-id "12345678-1234-1234-1234-123456789abc"
        """
    )
    
    parser.add_argument(
        '--provider-id',
        required=True,
        help='UUID of the SSO provider to delete'
    )
    
    args = parser.parse_args()
    
    logger.info("🔧 StackAI SSO Provider Deletion")
    logger.info("=" * 45)
    logger.info("")
    
    # Validate UUID format
    if not validate_uuid(args.provider_id):
        logger.error("❌ Invalid provider ID format!")
        logger.error("   Provider ID must be a valid UUID")
        logger.error("")
        logger.error("💡 Use 'make saml-list-providers' to see available provider IDs")
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
    
    # Confirm deletion
    logger.info("⚠️  WARNING: This action cannot be undone!")
    logger.info(f"   You are about to delete provider: {args.provider_id}")
    logger.info("")
    
    # In a script context, we'll proceed without interactive confirmation
    # But we'll show what we're doing clearly
    logger.info("🗑️  Proceeding with deletion...")
    logger.info("")
    
    # Delete the SSO provider
    success = delete_sso_provider(
        provider_id=args.provider_id,
        service_role_key=service_role_key,
        api_url=api_url
    )
    
    if success:
        logger.info("")
        logger.info("📋 Next steps:")
        logger.info("1. Verify deletion with: make saml-list-providers")
        logger.info("2. Update your Identity Provider configuration if needed")
        logger.info("3. Inform users that this SSO method is no longer available")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
