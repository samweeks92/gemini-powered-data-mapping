/**
 * Copyright 2021 Google LLC
 */


variable "project" {
  type        = string
  description = "The GCP Project name to use for the deployments"
}

variable "region" {
  type        = string
  description = "The GCP Region to use for the deployments"
}

variable "vpc-name" {
  type        = string
  description = "The name to use for the created VPC"
}

variable "subnet-name" {
  type        = string
  description = "The name to use for the created VPC Subnetwork"
}

variable "vpc-access-connector-name" {
  description = "Name of the VPC Access Connector"
  type        = string
}

variable "vpc-access-connector-cidr-range" {
  description = "CIDR range of the VPC Access Connector"
  type        = string
}