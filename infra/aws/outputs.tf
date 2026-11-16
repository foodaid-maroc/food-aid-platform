output "ingest_url" {
  description = "URL publique à donner à CMI et aux partenaires"
  value       = module.ingest.invoke_url
}

output "queue_url" {
  value = module.ingest.queue_url
}
