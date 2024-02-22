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

variable "dataset-id" {
  description = "Name of the BigQuery dataset holding the data"
  type        = string
}

variable "raw_target_table" {
  description = "Name of the BigQuery table holding the unprocessed target schema"
  type        = string
}

variable "target_table" {
  description = "Name to use for the BigQuery table for the target schema data created by the job-scheduler service after pre-processing"
  type        = string
}

variable "raw_source_tables" {
  description = "Names of the BigQuery source tables holding the unprocessed target schema"
  type        = string
}

variable "raw_source_tables_wildcard" {
  description = "wildcard to use when querying the source tables in a single query"
  type        = string
}

variable "source_table" {
  description = "Name to use for the BigQuery table for the source schema data created by the job-scheduler service after pre-processing"
  type        = string
}