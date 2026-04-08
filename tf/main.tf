terraform {
  required_providers {
    aws = { source = "hashicorp/aws", version = ">=5.55" }
  }
}

provider "aws" { region = var.region }

resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
  enable_dns_hostnames = true
  tags = { Name = "aid-logix-vpc" }
}

resource "aws_subnet" "public" {
  vpc_id     = aws_vpc.main.id
  cidr_block = "10.0.1.0/24"
  map_public_ip_on_launch = true
}

resource "aws_internet_gateway" "gw" { vpc_id = aws_vpc.main.id }

resource "aws_route_table" "rt" {
  vpc_id = aws_vpc.main.id
  route { cidr_block = "0.0.0.0/0", gateway_id = aws_internet_gateway.gw.id }
}

resource "aws_route_table_association" "a" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.rt.id
}

resource "aws_sqs_queue" "aid_queue" { name = "aid-requests-queue" }

resource "aws_dynamodb_table" "aid_table" {
  name         = "aid-requests-table"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "uid"
  attribute { name = "uid", type = "S" }
}

resource "aws_security_group" "sg" {
  vpc_id = aws_vpc.main.id
  ingress { from_port = 22; to_port = 22; protocol = "tcp"; cidr_blocks = ["0.0.0.0/0"] }
  ingress { from_port = 80; to_port = 80; protocol = "tcp"; cidr_blocks = ["0.0.0.0/0"] }
  egress { from_port = 0; to_port = 0; protocol = "-1"; cidr_blocks = ["0.0.0.0/0"] }
}

resource "aws_instance" "k8s_node" {
  ami           = var.ami
  instance_type = "t2.medium"
  subnet_id     = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.sg.id]
  key_name      = var.key_pair_name
  tags          = { Name = "aid-logix-node" }
}
