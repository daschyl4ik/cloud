provider "aws" {
    access_key = var.AWS_ACCESS_KEY
    secret_key = var.AWS_SECRET_KEY
    region = var.AWS_REGION
}

terraform {
  required_providers {
    aws = {
      source = "hashicorp/aws"
    }
  }
  required_version = ">= 0.14"
}
