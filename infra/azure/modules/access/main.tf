# Étudiant 5 · Static Web Apps
# L'App registration Entra ID (rôles Staff/Partner/Donor/Auditor) est créée à la main dans le portail :
# le tenant de l'école ne donne pas forcément à la CI les droits Microsoft Graph nécessaires.
resource "azurerm_static_web_app" "portal" {
  name                = "swa-foodaid-${var.suffix}"
  resource_group_name = var.rg_name
  location            = var.location
  sku_tier            = "Free" # passer à "Standard" la semaine de la démo pour le linked backend
  sku_size            = "Free"
  tags                = var.tags
}

# Plan Standard uniquement : relier /api à l'app api (linked backend).
# À faire dans le portail : Static Web App → APIs → Link → Container App « ca-foodaid-api ».
