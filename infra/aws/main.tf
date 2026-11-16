# Étudiant 1
module "ingest" {
  source = "./modules/ingest"
  env    = var.env
}

# Étudiant 2
module "logic" {
  source           = "./modules/logic"
  env              = var.env
  queue_arn        = module.ingest.queue_arn
  azure_ingest_url = var.azure_ingest_url
  hmac_ssm_param   = var.hmac_ssm_param
}
