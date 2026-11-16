output "function_name" {
  value = aws_lambda_function.validate.function_name
}

output "table_name" {
  value = aws_dynamodb_table.idempotency.name
}
