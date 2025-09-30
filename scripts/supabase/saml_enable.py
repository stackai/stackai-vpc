#!/usr/bin/env python3
"""
Script to enable SAML authentication in StackAI on-premise deployment.
This script modifies the supabase/.env file to set SAML_ENABLED=true
and adds SAML endpoints to kong.yml.
"""

import sys
from pathlib import Path
import logging
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import base64

logger = logging.getLogger(__name__)


def generate_saml_private_key() -> str:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    # Export in DER (binary) format using PKCS#1
    der_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.TraditionalOpenSSL,  # PKCS#1 format for Supabase
        encryption_algorithm=serialization.NoEncryption(),
    )

    # Base64 encode like `base64 -i private_key.der`
    b64_str = base64.b64encode(der_bytes).decode("utf-8")
    
    # Format with line breaks every 64 characters (like terminal base64 command)
    formatted_b64 = '\n'.join(b64_str[i:i+64] for i in range(0, len(b64_str), 64))
    
    return formatted_b64

def update_env_file(env_file_path: Path, key: str, new_value: str) -> bool:
    """
    Update a specific key in an environment file.
    Handles multi-line values properly.
    
    Args:
        env_file_path: Path to the .env file
        key: Environment variable key to update
        new_value: New value to set
     
    Returns:
        bool: True if file was updated, False if key wasn't found
    """
    if not env_file_path.exists():
        logger.error(f"Environment file not found: {env_file_path}")
        return False
    
    # Read all content
    with open(env_file_path, 'r') as f:
        content = f.read()
    
    import re
    
    # Format new value - if it contains newlines, wrap in quotes
    if '\n' in new_value:
        formatted_value = f'{key}="{new_value}"'
    else:
        formatted_value = f'{key}={new_value}'
    
    # Pattern to match the key and its complete value (including multi-line quoted values)
    # This matches: KEY="multi\nline\nvalue" or KEY=singlevalue
    pattern = rf'^{re.escape(key)}=(?:"[^"]*(?:\n[^"]*)*"|[^\n]*)'
    
    # Check if key exists
    if re.search(rf'^{re.escape(key)}=', content, re.MULTILINE):
        # Key exists, replace it
        new_content = re.sub(pattern, formatted_value, content, flags=re.MULTILINE)
        logger.info(f"✅ Updated {key}")
    else:
        # Key not found, add it to the end
        # Add newline before if content doesn't end with one
        if content and not content.endswith('\n'):
            new_content = content + f'\n{formatted_value}\n'
        else:
            new_content = content + f'{formatted_value}\n'
        logger.info(f"✅ Added {key}")
    
    # Write the updated content back to the file
    with open(env_file_path, 'w') as f:
        f.write(new_content)
    
    return True

def update_kong_yml(kong_file_path: Path) -> bool:
    """
    Add SAML endpoints to kong.yml if they don't already exist.
    
    Args:
        kong_file_path: Path to the kong.yml file
     
    Returns:
        bool: True if file was updated, False otherwise
    """
    if not kong_file_path.exists():
        logger.error(f"Kong configuration file not found: {kong_file_path}")
        return False
    
    # Read the current kong.yml content
    with open(kong_file_path, 'r') as f:
        content = f.read()
    
    # Check if SAML endpoints already exist
    if 'auth-v1-open-sso-acs' in content:
        logger.info("✅ SAML endpoints already exist in kong.yml")
        return True
    
    # SAML endpoints configuration to insert (no leading newline)
    saml_config = """  ## Open SSO routes
  - name: auth-v1-open-sso-acs
    url: "http://auth:9999/sso/saml/acs"
    routes:
      - name: auth-v1-open-sso-acs
        strip_path: true
        paths:
        - /auth/v1/sso/saml/acs
        - /sso/saml/acs
    plugins:
      - name: cors
  - name: auth-v1-open-sso-metadata
    url: "http://auth:9999/sso/saml/metadata"
    routes:
      - name: auth-v1-open-sso-metadata
        strip_path: true
        paths:
        - /auth/v1/sso/saml/metadata
    plugins:
      - name: cors

"""
    
    # Find the insertion point - look for the end of the authorize route and before secure auth
    # This is more specific and reliable
    insertion_point = content.find("  ## Secure Auth routes")
    
    if insertion_point != -1:
        # Insert SAML config before the "Secure Auth routes" section
        new_content = content[:insertion_point] + saml_config + "\n" + content[insertion_point:]
        
        # Use the content as-is without YAML formatting to avoid issues
        # The SAML config is already properly formatted
        formatted_content = new_content
        
        # Write the updated content back to the file
        with open(kong_file_path, 'w') as f:
            f.write(formatted_content)
        
        logger.info("✅ Added SAML endpoints to kong.yml")
        return True
    else:
        logger.error("❌ Could not find '## Secure Auth routes' section in kong.yml")
        return False

def main():
    """Main function to enable SAML authentication."""
    logger.info("🔧 StackAI SAML Enabler Script")
    logger.info("=" * 40)
    
    # Get the project root directory (go up two levels from scripts/supabase)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    supabase_env_path = project_root / "supabase" / ".env"
    kong_yml_path = project_root / "supabase" / "volumes" / "api" / "kong.yml"
    
    logger.info(f"📁 Looking for Supabase environment file at: {supabase_env_path}")
    logger.info(f"📁 Looking for Kong configuration file at: {kong_yml_path}")
    
    # Check if files exist
    if not supabase_env_path.exists():
        logger.error(f"Supabase .env file not found at {supabase_env_path}")
        logger.info("💡 Please run the environment setup script first:")
        logger.info("   cd scripts/environment_variables && python create_env_variables.py")
        sys.exit(1)
    
    if not kong_yml_path.exists():
        logger.error(f"Kong configuration file not found at {kong_yml_path}")
        sys.exit(1)
    
    # Create backups of the original files
    env_backup_path = supabase_env_path.with_suffix('.env.backup')
    kong_backup_path = kong_yml_path.with_suffix('.yml.backup')
    
    if not env_backup_path.exists():
        import shutil
        shutil.copy2(supabase_env_path, env_backup_path)
        logger.info(f"Created backup at: {env_backup_path}")
    
    if not kong_backup_path.exists():
        import shutil
        shutil.copy2(kong_yml_path, kong_backup_path)
        logger.info(f"Created backup at: {kong_backup_path}")
    
    # Update SAML_ENABLED to true
    updated_saml_enabled = update_env_file(supabase_env_path, "SAML_ENABLED", "true")
    if not updated_saml_enabled:
        logger.error("Failed to update SAML_ENABLED")
        sys.exit(1)

    # Generate a new SAML private key
    updated_saml_private_key = update_env_file(supabase_env_path, "SAML_PRIVATE_KEY", generate_saml_private_key())
    if not updated_saml_private_key:
        logger.error("Failed to update SAML_PRIVATE_KEY")
        sys.exit(1)

    # Update Kong configuration
    updated_kong = update_kong_yml(kong_yml_path)
    if not updated_kong:
        logger.error("Failed to update Kong configuration")
        sys.exit(1)

    logger.info("🎉 SAML has been successfully enabled!")
    logger.info("\n📋 Next steps:")
    logger.info("1. Configure your SAML Identity Provider (IdP)")
    logger.info("2. Update SAML_PRIVATE_KEY if needed (already generated)")
    logger.info("3. Restart your Supabase services:")
    logger.info("   cd supabase && docker-compose down && docker-compose up -d")
    logger.info("\n⚠️  Note: You'll need to configure your SAML IdP settings in the Supabase Auth dashboard")
    logger.info("\n🔗 SAML endpoints will be available at:")
    logger.info("   - /auth/v1/sso/saml/acs (Assertion Consumer Service)")
    logger.info("   - /auth/v1/sso/saml/metadata (SAML Metadata)")

if __name__ == "__main__":
    main()