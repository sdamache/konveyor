from services.secure_credential_service import SecureCredentialService
import os
from dotenv import load_dotenv

def main():
    """Initialize secure storage for bot credentials"""
    print("Setting up secure credential storage...")
    
    # Verify environment variables
    load_dotenv()
    required_vars = [
        'AZURE_KEY_VAULT_URL',
        'AZURE_TENANT_ID',
        'AZURE_CLIENT_ID',
        'AZURE_CLIENT_SECRET',
        'SLACK_CLIENT_ID',
        'SLACK_CLIENT_SECRET',
        'SLACK_SIGNING_SECRET',
        'SLACK_BOT_TOKEN'
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print("⚠ Missing required environment variables:")
        for var in missing_vars:
            print(f"  - {var}")
        return
    
    try:
        # Initialize and store credentials
        credential_service = SecureCredentialService()
        if credential_service.store_bot_credentials():
            print("✓ Bot credentials securely stored in Azure Key Vault")
            
            # Verify storage by retrieving credentials
            stored_creds = credential_service.get_bot_credentials()
            if stored_creds:
                print("✓ Successfully verified credential storage")
            else:
                print("⚠ Failed to verify stored credentials")
        else:
            print("⚠ Failed to store bot credentials")
            
    except Exception as e:
        print(f"⚠ Error during secure storage setup: {str(e)}")

if __name__ == "__main__":
    main()