variable "gitlab-host-connection-name" {
  type        = string
  description = "The name of the connected gitlab host connection"
}

variable "repo-name" {
  type        = string
  description = "The name of the repository containing this code"
}

variable "project" {
  type        = string
  description = "The Google Cloud Project to deploy resources"
}

variable "region" {
  type        = string
  description = "The Google Cloud Region to deploy resources"
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

variable "mapped_table" {
  description = "Name to use for the BigQuery table for the source schema data created by the job-scheduler service after pre-processing"
  type        = string
}

# Below here are additional variables that are not updated from Cloud Build


variable "vpc-name" {
  type        = string
  description = "The name of the VPC"
  default     = "base-vpc"
}

variable "subnet-name" {
  type        = string
  description = "The name to use for the created VPC Subnetwork"
  default     = "subnet"
}

variable "vpc-access-connector-name" {
  type        = string
  description = "Name of the VPC Access Connector"
  default     = "vpc-access-connector"
}

variable "vpc-access-connector-cidr-range" {
  type        = string
  description = "CIDR range of the VPC Access Connector"
  default     = "10.8.0.0/28"
}