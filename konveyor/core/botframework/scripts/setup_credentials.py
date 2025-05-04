from konveyor.core.botframework.services.credentials import SecureCredentialService

# Removed os and dotenv imports


def main():
    """Initialize secure storage for bot credentials"""
    print("Setting up secure credential storage...")

    # Verify environment variables
    # Removed load_dotenv() and manual environment variable checks.
    # The SecureCredentialService will handle config loading and validation internally.

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
