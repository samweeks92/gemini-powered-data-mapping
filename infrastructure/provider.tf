/**
 * Copyright 2021 Google LLC
 */

provider "google" {
  project = var.project
}

provider "google-beta" {
  project = var.project
}

provider "local" {
}
