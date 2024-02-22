/**
 * Copyright 2021 Google LLC
 */


# Define Terraform Backend Remote State
terraform {
  backend "gcs" {}
  required_providers {
    google-beta = {
      source = "hashicorp/google-beta"
      version = "4.74.0"
    }
  }
}