# Étudiant 3 · Service Bus + Container Apps (api + workers)
resource "azurerm_servicebus_namespace" "main" {
  name                = "sb-foodaid-${var.suffix}"
  resource_group_name = var.rg_name
  location            = var.location
  sku                 = "Basic" # files uniquement : suffisant ici, quelques centimes
  tags                = var.tags
}

resource "azurerm_servicebus_queue" "batches" {
  name                                 = "batches"
  namespace_id                         = azurerm_servicebus_namespace.main.id
  max_delivery_count                   = 3 # puis DLQ
  dead_lettering_on_message_expiration = true
}

# Règle d'écoute seule, utilisée par le scaler KEDA pour compter les messages
resource "azurerm_servicebus_queue_authorization_rule" "keda" {
  name     = "keda-listen"
  queue_id = azurerm_servicebus_queue.batches.id
  listen   = true
}

resource "azurerm_role_assignment" "apps_sb_send" {
  scope                = azurerm_servicebus_namespace.main.id
  role_definition_name = "Azure Service Bus Data Sender"
  principal_id         = var.apps_principal_id
}

resource "azurerm_role_assignment" "apps_sb_receive" {
  scope                = azurerm_servicebus_namespace.main.id
  role_definition_name = "Azure Service Bus Data Receiver"
  principal_id         = var.apps_principal_id
}

resource "azurerm_container_app_environment" "main" {
  name                       = "cae-foodaid-${var.suffix}"
  resource_group_name        = var.rg_name
  location                   = var.location
  log_analytics_workspace_id = var.log_analytics_workspace_id # plan Consumption par défaut
  tags                       = var.tags
}

locals {
  common_env = {
    AZURE_CLIENT_ID      = var.identity_client_id # identité managée utilisée par DefaultAzureCredential
    COSMOS_ENDPOINT      = var.cosmos_endpoint
    COSMOS_DATABASE      = "foodaid"
    BLOB_ACCOUNT_URL     = var.blob_account_url
    SERVICEBUS_NAMESPACE = "${azurerm_servicebus_namespace.main.name}.servicebus.windows.net"
    SERVICEBUS_QUEUE     = azurerm_servicebus_queue.batches.name
  }
}

# ---------- app api : 0–3 réplicas, entrée HTTPS publique ----------
resource "azurerm_container_app" "api" {
  name                         = "ca-foodaid-api"
  resource_group_name          = var.rg_name
  container_app_environment_id = azurerm_container_app_environment.main.id
  revision_mode                = "Single"
  tags                         = var.tags

  identity {
    type         = "UserAssigned"
    identity_ids = [var.identity_id]
  }

  secret {
    name                = "hmac-secret"
    key_vault_secret_id = var.hmac_secret_id # lu dans Key Vault par l'identité managée
    identity            = var.identity_id
  }

  ingress {
    external_enabled = true
    target_port      = 8080
    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }

  template {
    min_replicas = 0 # dev : échelle à zéro
    max_replicas = 3

    container {
      name   = "api"
      image  = var.api_image
      cpu    = 0.25
      memory = "0.5Gi"

      dynamic "env" {
        for_each = merge(local.common_env, {
          AUTH_MODE          = "entra"
          ALLOWED_ORIGINS    = var.allowed_origin # CORS géré par l'API (portail en plan Free)
          ENTRA_TENANT_ID    = var.entra_tenant_id
          ENTRA_API_AUDIENCE = var.entra_api_audience
        })
        content {
          name  = env.key
          value = env.value
        }
      }

      env {
        name        = "HMAC_SECRET"
        secret_name = "hmac-secret"
      }
    }
  }
}

# ---------- app workers : 0–5 réplicas, aucune entrée publique, KEDA sur la file ----------
resource "azurerm_container_app" "workers" {
  name                         = "ca-foodaid-workers"
  resource_group_name          = var.rg_name
  container_app_environment_id = azurerm_container_app_environment.main.id
  revision_mode                = "Single"
  tags                         = var.tags

  identity {
    type         = "UserAssigned"
    identity_ids = [var.identity_id]
  }

  secret {
    name  = "sb-keda"
    value = azurerm_servicebus_queue_authorization_rule.keda.primary_connection_string
  }

  template {
    min_replicas = 0
    max_replicas = 5

    container {
      name   = "workers"
      image  = var.workers_image
      cpu    = 0.25
      memory = "0.5Gi"

      dynamic "env" {
        for_each = local.common_env
        content {
          name  = env.key
          value = env.value
        }
      }
    }

    custom_scale_rule {
      name             = "servicebus-batches"
      custom_rule_type = "azure-servicebus"
      metadata = {
        queueName    = azurerm_servicebus_queue.batches.name
        messageCount = "5" # 1 réplica de plus tous les 5 messages en attente
      }
      authentication {
        secret_name       = "sb-keda"
        trigger_parameter = "connection"
      }
    }
  }
}
