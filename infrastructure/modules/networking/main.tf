resource "google_compute_network" "vpc" {
  project                 = var.project
  name                    = var.vpc-name
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "subnet" {
  name                     = var.subnet-name
  provider                 = google-beta
  ip_cidr_range            = "10.1.2.0/24"
  region                   = var.region
  network                  = google_compute_network.vpc.id
  private_ip_google_access = true
}

# Reserve an IP Range for use with Private Service Access
resource "google_compute_global_address" "google-managed-services-range" {

  project       = var.project
  name          = "psa"
  purpose       = "VPC_PEERING"
  prefix_length = "20"
  ip_version    = "IPV4"
  address_type  = "INTERNAL"
  network       = google_compute_network.vpc.self_link
}

# Setup the Private Service Access network connection
resource "google_service_networking_connection" "private_service_access" {

  network                 = google_compute_network.vpc.self_link
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.google-managed-services-range.name]

}

# Create a VPC Access Connector for Cloud Run so it can connect to the Project's VPC
resource "google_vpc_access_connector" "connector" {
  name          = var.vpc-access-connector-name
  ip_cidr_range = var.vpc-access-connector-cidr-range
  region        = var.region
  network       = var.vpc-name

  depends_on = [google_compute_network.vpc]
}