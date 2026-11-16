# Étudiant 1 · API Gateway (REST) -> SQS, sans code (intégration directe)
data "aws_region" "current" {}
data "aws_caller_identity" "current" {}

locals {
  name = "foodaid-lots"
}

# ---------- SQS + DLQ ----------
resource "aws_sqs_queue" "dlq" {
  name                      = "${local.name}-dlq"
  message_retention_seconds = 1209600 # 14 jours
  sqs_managed_sse_enabled   = true
}

resource "aws_sqs_queue" "lots" {
  name                       = local.name
  visibility_timeout_seconds = 60 # > timeout de la Lambda
  message_retention_seconds  = 345600
  sqs_managed_sse_enabled    = true
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = 3
  })
}

# ---------- Rôle : API Gateway peut UNIQUEMENT envoyer dans cette file ----------
resource "aws_iam_role" "apigw_to_sqs" {
  name = "foodaid-apigw-to-sqs-${var.env}"
  assume_role_policy = jsonencode({
    Version   = "2012-10-17"
    Statement = [{ Effect = "Allow", Principal = { Service = "apigateway.amazonaws.com" }, Action = "sts:AssumeRole" }]
  })
}

resource "aws_iam_role_policy" "apigw_to_sqs" {
  role = aws_iam_role.apigw_to_sqs.id
  policy = jsonencode({
    Version   = "2012-10-17"
    Statement = [{ Effect = "Allow", Action = "sqs:SendMessage", Resource = aws_sqs_queue.lots.arn }]
  })
}

# ---------- API REST : POST /donations ----------
resource "aws_api_gateway_rest_api" "ingest" {
  name = "foodaid-ingest-${var.env}"
  endpoint_configuration { types = ["REGIONAL"] }
}

resource "aws_api_gateway_resource" "donations" {
  rest_api_id = aws_api_gateway_rest_api.ingest.id
  parent_id   = aws_api_gateway_rest_api.ingest.root_resource_id
  path_part   = "donations"
}

resource "aws_api_gateway_model" "lot" {
  rest_api_id  = aws_api_gateway_rest_api.ingest.id
  name         = "Lot"
  content_type = "application/json"
  # Validation minimale ; le contrat complet est contracts/lot.schema.json
  schema = jsonencode({
    "$schema"  = "http://json-schema.org/draft-04/schema#"
    type       = "object"
    required   = ["donationId", "source", "partnerId", "receivedAt", "items"]
    properties = { donationId = { type = "string" }, partnerId = { type = "string" }, items = { type = "array" } }
  })
}

resource "aws_api_gateway_request_validator" "body" {
  rest_api_id           = aws_api_gateway_rest_api.ingest.id
  name                  = "body"
  validate_request_body = true
}

resource "aws_api_gateway_method" "post" {
  rest_api_id          = aws_api_gateway_rest_api.ingest.id
  resource_id          = aws_api_gateway_resource.donations.id
  http_method          = "POST"
  authorization        = "NONE" # TODO (Étudiant 1) : clé d'API par partenaire (usage plan) ou vérification de signature CMI
  request_validator_id = aws_api_gateway_request_validator.body.id
  request_models       = { "application/json" = aws_api_gateway_model.lot.name }
}

resource "aws_api_gateway_integration" "sqs" {
  rest_api_id             = aws_api_gateway_rest_api.ingest.id
  resource_id             = aws_api_gateway_resource.donations.id
  http_method             = aws_api_gateway_method.post.http_method
  type                    = "AWS"
  integration_http_method = "POST"
  credentials             = aws_iam_role.apigw_to_sqs.arn
  uri                     = "arn:aws:apigateway:${data.aws_region.current.name}:sqs:path/${data.aws_caller_identity.current.account_id}/${aws_sqs_queue.lots.name}"
  request_parameters      = { "integration.request.header.Content-Type" = "'application/x-www-form-urlencoded'" }
  request_templates       = { "application/json" = "Action=SendMessage&MessageBody=$util.urlEncode($input.body)" }
  passthrough_behavior    = "NEVER"
}

resource "aws_api_gateway_method_response" "ok" {
  rest_api_id = aws_api_gateway_rest_api.ingest.id
  resource_id = aws_api_gateway_resource.donations.id
  http_method = aws_api_gateway_method.post.http_method
  status_code = "202"
}

resource "aws_api_gateway_integration_response" "ok" {
  rest_api_id        = aws_api_gateway_rest_api.ingest.id
  resource_id        = aws_api_gateway_resource.donations.id
  http_method        = aws_api_gateway_method.post.http_method
  status_code        = aws_api_gateway_method_response.ok.status_code
  response_templates = { "application/json" = "{\"status\":\"queued\"}" }
  depends_on         = [aws_api_gateway_integration.sqs]
}

resource "aws_api_gateway_deployment" "this" {
  rest_api_id = aws_api_gateway_rest_api.ingest.id
  triggers = {
    redeploy = sha1(jsonencode([aws_api_gateway_method.post, aws_api_gateway_integration.sqs, aws_api_gateway_model.lot]))
  }
  lifecycle { create_before_destroy = true }
  depends_on = [aws_api_gateway_integration_response.ok]
}

resource "aws_api_gateway_stage" "this" {
  rest_api_id   = aws_api_gateway_rest_api.ingest.id
  deployment_id = aws_api_gateway_deployment.this.id
  stage_name    = var.env
}

resource "aws_api_gateway_method_settings" "throttle" {
  rest_api_id = aws_api_gateway_rest_api.ingest.id
  stage_name  = aws_api_gateway_stage.this.stage_name
  method_path = "*/*"
  settings {
    throttling_rate_limit  = 50 # requêtes/s : protège contre les abus
    throttling_burst_limit = 100
  }
}

# ---------- Alerte : un message est arrivé en DLQ ----------
resource "aws_cloudwatch_metric_alarm" "dlq_not_empty" {
  alarm_name          = "foodaid-dlq-not-empty-${var.env}"
  namespace           = "AWS/SQS"
  metric_name         = "ApproximateNumberOfMessagesVisible"
  dimensions          = { QueueName = aws_sqs_queue.dlq.name }
  statistic           = "Maximum"
  period              = 300
  evaluation_periods  = 1
  threshold           = 0
  comparison_operator = "GreaterThanThreshold"
}
