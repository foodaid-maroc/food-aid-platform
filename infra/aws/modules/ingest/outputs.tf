output "queue_arn" {
  value = aws_sqs_queue.lots.arn
}

output "queue_url" {
  value = aws_sqs_queue.lots.url
}

output "invoke_url" {
  value = "${aws_api_gateway_stage.this.invoke_url}/donations"
}
