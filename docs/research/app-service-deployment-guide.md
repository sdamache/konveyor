# Azure App Service Deployment Guide for Konveyor

Below is a step-by-step deployment playbook—formatted in Markdown—that shows how to:
* Provision Azure App Service (Linux) + Azure Bot Service → Slack Channel with Terraform
* Build & ship your containerised Django backend through GitHub Actions
* Hook everything together so the Slack app talks to the same backend that now hosts your SK agents

## Assumptions
* You already have: Dockerfile, requirements.txt, gunicorn entry, and a Key Vault containing secrets.
* All infra goes into the existing Konveyor-infra Terraform project.
* The Slack app currently points at https://<domain>/slack/events; keep that path.

---

## 1 – Terraform Infrastructure

### 1.1 Core resources

```terraform
terraform {
  required_version = ">= 1.8.0"
  required_providers {
    azurerm = { source = "hashicorp/azurerm", version = "~> 3.105" }
  }
}
provider "azurerm" {
  features {}
}

resource "azurerm_resource_group" "rg" {
  name     = "rg-konveyor-prod"
  location = "eastus"
}

resource "azurerm_service_plan" "plan" {
  name                = "asp-konveyor-linux"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  os_type             = "Linux"
  sku_name            = "P1v3"          # S1 works for most PoCs
}

resource "azurerm_linux_web_app" "django" {
  name                = "konveyor-backend"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  service_plan_id     = azurerm_service_plan.plan.id

  site_config {
    linux_fx_version = "DOCKER|ghcr.io/<org>/konveyor:${var.image_tag}"
    app_command_line = ""              # gunicorn run cmd already in Dockerfile
  }

  app_settings = {
    "WEBSITES_PORT"             = "8000"
    "DJANGO_SETTINGS_MODULE"    = "config.settings.prod"
    "SLACK_BOT_TOKEN"           = var.slack_bot_token          # or Key Vault ref
    "SLACK_SIGNING_SECRET"      = var.slack_sign_secret
    "AZURE_OPENAI_ENDPOINT"     = var.openai_endpoint
    "AZURE_OPENAI_KEY"          = var.openai_key
  }
}
```

> Note: azurerm_linux_web_app supports direct container images via linux_fx_version.

### 1.2 Bot Service + Slack channel

```terraform
resource "azurerm_bot_channels_registration" "bot" {
  name                = "konveyor-bot"
  resource_group_name = azurerm_resource_group.rg.name
  location            = "global"
  microsoft_app_id    = var.bot_app_id
  microsoft_app_type  = "UserAssignedMSI"
  sku                 = "F0"
  endpoint            = "${azurerm_linux_web_app.django.default_hostname}/api/messages"
}

resource "azurerm_bot_channel_slack" "slack" {
  name                    = "SlackChannel"
  resource_group_name     = azurerm_resource_group.rg.name
  bot_name                = azurerm_bot_channels_registration.bot.name
  client_id               = var.slack_client_id
  client_secret           = var.slack_client_secret
  signing_secret          = var.slack_sign_secret
  verification_token      = var.slack_verification_token
}
```

> Note: Slack channel resource is in the Azurerm provider ≥ 3.71.0.
> Azure portal wiring steps are identical when provisioned manually.

### 1.3 Outputs

```terraform
output "webapp_url"  { value = azurerm_linux_web_app.django.default_hostname }
output "bot_app_id"  { value = azurerm_bot_channels_registration.bot.microsoft_app_id }
```

---

## 2 – GitHub Actions Pipeline

### .github/workflows/deploy.yml

```yaml
name: CI/CD – Build & Deploy Django

on:
  push:
    branches: [main]
  workflow_dispatch:

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: konveyor
  WEBAPP_NAME: konveyor-backend

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4

    - name: Log in to GHCR
      uses: docker/login-action@v3
      with:
        registry: ${{ env.REGISTRY }}
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}

    - name: Build & push
      run: |
        docker build -t $REGISTRY/${{ github.repository }}:$GITHUB_SHA .
        docker push $REGISTRY/${{ github.repository }}:$GITHUB_SHA
      # sets an output IMAGE_TAG you pass to Terraform plan/apply

  deploy:
    needs: build
    runs-on: ubuntu-latest
    permissions:
      id-token: write   # for OIDC
      contents: read
    steps:
    - uses: actions/checkout@v4

    - uses: azure/login@v2
      with:
        client-id:  ${{ secrets.AZURE_CLIENT_ID }}
        tenant-id:  ${{ secrets.AZURE_TENANT_ID }}
        subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}

    - name: Terraform apply
      run: |
        cd Konveyor-infra
        terraform init
        terraform apply -auto-approve \
          -var="image_tag=$GITHUB_SHA"
```

> Note: azure/webapps-deploy is not used here because we point App Service at the container tag; Terraform updates linux_fx_version instead.

---

## 3 – Slack & Bot Wiring

1. In Slack
   * Add/verify the Events API request URL: https://konveyor-backend.azurewebsites.net/slack/events
   * Reinstall the app to update scopes (chat:write, commands, app_mentions:read).

2. In Azure Portal (one-time)
   * Make sure "Slack" channel on the Bot resource shows "Running".
   * Copy the generated Webhook URL back into your Slack app → OAuth & Permissions.

3. Backend routes
   * Keep /api/messages for Bot Framework (Bot Service)
   * Keep /slack/events for Bolt. Bot Service will deliver Slack payloads to /api/messages; the Bolt path is still used for direct Slack traffic during local testing.

---

## 4 – Common Pitfalls & Fixes

| Area | Symptom | Cause | Fix |
|------|---------|-------|-----|
| App Service | Container restarts every 90s | Missing WEBSITES_PORT | Set to gunicorn listen port (8000) |
|  | HTTP 500 only in PROD | DEBUG=False but no ALLOWED_HOSTS | Add ALLOWED_HOSTS=["*.azurewebsites.net"] |
|  | "OS error / ENOMEM" on deploy | Python site-packages too large | Use --no-cache-dir in pip install / slim base image |
| GitHub Actions | AZURE_WEBAPP_NAME not found | Using WebApp deploy action on container | Drive image via Terraform or set publish-profile secrets |
| Bot Service | Messages show "403 forbidden" in Slack | Wrong Slack signing secret / timestamp delta > 5 min | Sync secret & ensure runner uses UTC |
|  | Slack channel stuck in "Waiting for event" | Forgot to reinstall Slack app after changing scopes | Reinstall app; verify "Bot User OAuth Token" |
| Terraform | linux_fx_version ignored | Web App created as Windows plan | Ensure os_type = "Linux" on azurerm_service_plan |
| Networking | Outbound calls blocked | App Service uses default route tables | For VNet-integrated plans, enable Route All or set NAT gateway |

> More deployment-related issues & troubleshooting tips available in documentation.

---

## 5 – End-to-End Checklist

1. terraform apply – verify outputs show WebApp URL & Bot App ID.
2. ghcr.io/...:$SHA tag appears under Container settings in App Service.
3. /healthz endpoint returns 200.
4. Message "@konveyor docs how do I set up CI?" in Slack → backend replies.
5. 👍 / 👎 reactions are logged (Task 8 will use this later).

---

## References

* [Deploy containerised Python app to App Service](https://learn.microsoft.com/en-us/azure/app-service/tutorial-custom-container?tabs=python)
* [Python App Service quick-start](https://learn.microsoft.com/en-us/azure/app-service/quickstart-python)
* [GitHub Action repository & Django sample workflow](https://github.com/Azure/actions-workflow-samples)
* [Terraform azurerm_linux_web_app docs](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/linux_web_app)
* [Terraform Slack channel resource](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/bot_channel_slack)
* [Bot → Slack channel configuration guide](https://learn.microsoft.com/en-us/azure/bot-service/bot-service-channel-connect-slack)
* [App Service deployment pitfalls & debugging](https://learn.microsoft.com/en-us/troubleshoot/azure/app-service/welcome-app-service)

⸻
