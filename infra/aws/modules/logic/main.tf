# Étudiant 2 · Lambda (déclenchée par SQS) + DynamoDB (idempotence)
data "aws_region" "current" {}
data "aws_caller_identity" "current" {}

resource "aws_dynamodb_table" "idempotency" {
  name         = "foodaid-idempotency"
  billing_mode = "PAY_PER_REQUEST" # on ne paie que les requêtes
  hash_key     = "pk"

  attribute {
    name = "pk"
    type = "S"
  }

  ttl {
    attribute_name = "expiresAt" # les entrées expirées s'effacent seules
    enabled        = true
  }
}

data "archive_file" "lambda" {
  type        = "zip"
  source_file = "${path.root}/../../aws/logic/handler.py"
  output_path = "${path.module}/build/handler.zip"
}

resource "aws_iam_role" "lambda" {
  name = "foodaid-lambda-${var.env}"
  assume_role_policy = jsonencode({
    Version   = "2012-10-17"
    Statement = [{ Effect = "Allow", Principal = { Service = "lambda.amazonaws.com" }, Action = "sts:AssumeRole" }]
  })
}

resource "aws_iam_role_policy_attachment" "logs" {
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Moindre privilège : uniquement cette table, cette file, ce paramètre
resource "aws_iam_role_policy" "lambda" {
  role = aws_iam_role.lambda.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      { Effect = "Allow", Action = ["dynamodb:PutItem", "dynamodb:UpdateItem", "dynamodb:DeleteItem"], Resource = aws_dynamodb_table.idempotency.arn },
      { Effect = "Allow", Action = ["sqs:ReceiveMessage", "sqs:DeleteMessage", "sqs:GetQueueAttributes"], Resource = var.queue_arn },
      { Effect = "Allow", Action = "ssm:GetParameter", Resource = "arn:aws:ssm:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:parameter${var.hmac_ssm_param}" },
    ]
  })
}

resource "aws_lambda_function" "validate" {
  function_name    = "foodaid-validate-${var.env}"
  role             = aws_iam_role.lambda.arn
  runtime          = "python3.12"
  handler          = "handler.handler"
  filename         = data.archive_file.lambda.output_path
  source_code_hash = data.archive_file.lambda.output_base64sha256
  timeout          = 30
  memory_size      = 256

  environment {
    variables = {
      IDEMPOTENCY_TABLE = aws_dynamodb_table.idempotency.name
      AZURE_INGEST_URL  = var.azure_ingest_url
      HMAC_SSM_PARAM    = var.hmac_ssm_param
    }
  }
}

resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${aws_lambda_function.validate.function_name}"
  retention_in_days = 14
}

resource "aws_lambda_event_source_mapping" "sqs" {
  event_source_arn        = var.queue_arn
  function_name           = aws_lambda_function.validate.arn
  batch_size              = 10
  function_response_types = ["ReportBatchItemFailures"] # seuls les messages en échec sont réessayés
}
