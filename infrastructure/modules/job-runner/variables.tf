variable "project" {
  type        = string
  description = "The GCP Project name to use for the deployments"
}

variable "region" {
  type        = string
  description = "The GCP Region to use for the deployments"
}

variable "repo-name" {
  description = "Name of the cloud source repos repository holding the source code"
  type        = string
}

variable "gitlab-host-connection-name" {
  type        = string
  description = "The name of the connected gitlab host connection"
}

variable "queued-jobs-bucket-name" {
  description = "Name of the queued-jobs-bucket"
  type        = string
}

variable "dataset-id" {
  description = "Name of the BigQuery dataset holding the data"
  type        = string
}

variable "target_table" {
  description = "Name of the BigQuery table for the target schema data created by the job-scheduler service after pre-processing"
  type        = string
}

variable "source_table" {
  description = "Name of the BigQuery table for the source schema data created by the job-scheduler service after pre-processing"
  type        = string
}

variable "mapped_table" {
  description = "Name to use for the BigQuery table for the outputted mappings data created by the job-runner service"
  type        = string
}