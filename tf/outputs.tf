output "sqs_url" { value = aws_sqs_queue.aid_queue.id }
output "dynamo_table" { value = aws_dynamodb_table.aid_table.name }
output "node_ip" { value = aws_instance.k8s_node.public_ip }
