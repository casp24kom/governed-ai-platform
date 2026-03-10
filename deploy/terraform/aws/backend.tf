terraform {
  backend "azurerm" {
    resource_group_name  = "rg-governed-ai-platform-tfstate-dev-ae"
    storage_account_name = "stgovaiplatfdevae"
    container_name       = "tfstate"
    key                  = "aws/dev/terraform.tfstate"
    use_azuread_auth     = true
  }
}