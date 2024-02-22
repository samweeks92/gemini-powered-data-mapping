/**
 * Copyright 2021 Google LLC
 */


// Define the base primary VPC that will be used for the Fashion Sustainability Project
module "networking" {

  # Set Source
  source = "./modules/networking"

  # Define Variables
  project                         = var.project
  region                          = var.region
  vpc-name                        = var.vpc-name
  subnet-name                     = var.subnet-name
  vpc-access-connector-name       = var.vpc-access-connector-name
  vpc-access-connector-cidr-range = var.vpc-access-connector-cidr-range

  depends_on = [
    google_project_service.enable-required-apis
  ]

}

module "job-scheduler" {

  # Set Source
  source = "./modules/job-scheduler"

  # Define Environment Variables
  project                     = var.project
  region                      = var.region
  gitlab-host-connection-name = var.gitlab-host-connection-name
  repo-name                   = var.repo-name
  dataset-id                  = var.dataset-id   
  raw_target_table            = var.raw_target_table
  target_table                = var.target_table
  raw_source_tables           = var.raw_source_tables
  raw_source_tables_wildcard  = var.raw_source_tables_wildcard
  source_table                = var.source_table 

}

module "job-runner" {

  # Set Source
  source = "./modules/job-runner"

  # Define Environment Variables
  project                     = var.project
  region                      = var.region
  gitlab-host-connection-name = var.gitlab-host-connection-name
  repo-name                   = var.repo-name
  queued-jobs-bucket-name     = module.job-scheduler.queued-jobs-bucket-name
  dataset-id                  = var.dataset-id   
  target_table                = var.target_table
  source_table                = var.source_table 
  mapped_table                = var.mapped_table 

  depends_on = [
    module.networking,
    module.job-scheduler,
    google_project_service.enable-required-apis
  ]
}