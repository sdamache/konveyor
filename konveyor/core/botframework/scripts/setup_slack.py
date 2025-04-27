from konveyor.core.botframework.services.channels import SlackChannelService
# Removed os and dotenv imports, and check_env_file function

def main():
    print("Starting Slack channel configuration...")
    # Removed call to check_env_file()
    try:
        service = SlackChannelService()
        service.configure_channel()
    except ValueError as e:
        print(f"Configuration failed: {str(e)}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    main()