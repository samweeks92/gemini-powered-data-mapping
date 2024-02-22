data "google_project" "project" {
}

###################
###################
# Part 1: Buckets #
###################
###################

# Bucket for job-scheduler-bucket
resource "google_storage_bucket" "job-scheduler-bucket" {
  name          = "${var.project}-job-scheduler-bucket"
  location      = var.region
  project       = var.project
  uniform_bucket_level_access = true
  force_destroy = true
  storage_class = "STANDARD"
}

# Bucket for queued-jobs-bucket
resource "google_storage_bucket" "queued-jobs-bucket" {
  name          = "${var.project}-queued-jobs-bucket"
  location      = var.region
  project       = var.project
  uniform_bucket_level_access = true
  force_destroy = true
  storage_class = "STANDARD"
}


###############################
###############################
# Part 2: GCS>PubSub>CloudRun #
###############################
###############################

# Create the Service Account to use with the Cloud Run service and the pubsub notifications
resource "google_service_account" "job-scheduler-service-account" {
  account_id   = "job-scheduler-sa"
  display_name = "job scheduler service account"
  description  = "Service Account for the job-scheduler Cloud Run Service"
}

# Grant the project service agent the pubsub publisher role
resource "google_project_iam_member" "pubsub-monitoring-sa-pubsub-publish" {
  project = var.project
  role     = "roles/pubsub.publisher"
  member  = "serviceAccount:service-${data.google_project.project.number}@gs-project-accounts.iam.gserviceaccount.com"
}

# Create a Pub/Sub Topic used for notifications on bigquery updates
resource "google_pubsub_topic" "job-scheduler-bucket-notification-topic" {
  project     = var.project
  name     = "job-scheduler-bucket-notifications"
  provider = google-beta
}

# Enable notifications by giving the correct IAM permission to the unique service account.
data "google_storage_project_service_account" "gcs" {
  provider = google-beta
}

resource "google_pubsub_topic_iam_binding" "iam-binding" {
  provider = google-beta
  topic    = google_pubsub_topic.job-scheduler-bucket-notification-topic.id
  role     = "roles/pubsub.publisher"
  members  = ["serviceAccount:${data.google_storage_project_service_account.gcs.email_address}"]
}

# Create a Pub/Sub notification.
resource "google_storage_notification" "job-scheduler-bucket-notification" {
  provider       = google-beta
  bucket         = google_storage_bucket.job-scheduler-bucket.name
  payload_format = "JSON_API_V1"
  event_types    = ["OBJECT_FINALIZE"]
  topic          = google_pubsub_topic.job-scheduler-bucket-notification-topic.id
  depends_on     = [google_pubsub_topic_iam_binding.iam-binding]
  
}

resource "google_project_service_identity" "pub_sub_agent" {
  provider = google-beta
  project  = var.project
  service  = "pubsub.googleapis.com"
}

resource "google_project_iam_binding" "project_token_create" {
  project = var.project
  role    = "roles/iam.serviceAccountTokenCreator"
  members = ["serviceAccount:${google_project_service_identity.pub_sub_agent.email}"]
}

resource "google_pubsub_subscription" "job-scheduler-push" {
  project = var.project
  name  = "job-scheduler-push"
  topic = google_pubsub_topic.job-scheduler-bucket-notification-topic.name
  ack_deadline_seconds = 600
  push_config {
    push_endpoint = google_cloud_run_v2_service.job-scheduler.uri
    oidc_token {
      service_account_email = google_service_account.job-scheduler-service-account.email
    }
    attributes = {
      x-goog-version = "v1"
    }
  }
  depends_on = [google_cloud_run_v2_service.job-scheduler]
}

resource "google_cloud_run_service_iam_member" "job-scheduler-service-account-iam-member" {
  project = var.project
  location = var.region
  service  = google_cloud_run_v2_service.job-scheduler.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.job-scheduler-service-account.email}"
}

###############################
###############################
# Part 3: job-scheduler Image #
###############################
###############################

resource "google_artifact_registry_repository" "job-scheduler" {
  location      = var.region
  repository_id = "job-scheduler"
  description   = "Managed by Terraform - Do not manually edit - job-scheduler repository"
  format        = "DOCKER"

  docker_config {
    immutable_tags = false
  }

  lifecycle {
    ignore_changes = [ docker_config ]
  }
}

resource "google_cloudbuild_trigger" "repo-trigger" {
  location = var.region
  name        = "job-scheduler-build-deploy"
  description = "Managed by Terraform - Do not manually edit - job-scheduler image build and deployment"
  project     = var.project

  repository_event_config {
    repository = "projects/${var.project}/locations/${var.region}/connections/${var.gitlab-host-connection-name}/repositories/${var.repo-name}"
    push {
      branch = "^main$"
    }
  }

  substitutions = {
    _PROJECT_ID_ = var.project
    _REGION_     = var.region
  }

  included_files = ["data-mapping-poc/job-scheduler/**"]

  filename = "data-mapping-poc/cloudbuild/job-scheduler/cloudbuild.yaml"
}


###########################################
###########################################
# Part 4: job-scheduler Cloud Run service #
###########################################
###########################################

# Give the Service Account the Cloud Run Invoker role
resource "google_project_iam_member" "job-scheduler-sa-cloud-run-invoker-role" {
  project = var.project
  role    = "roles/run.invoker"
  member  = "serviceAccount:${google_service_account.job-scheduler-service-account.email}"
}

# Give the Service Account the Cloud Run Service Agent role
resource "google_project_iam_member" "job-scheduler-sa-cloud-run-service-agent-role" {
  project = var.project
  role    = "roles/serverless.serviceAgent"
  member  = "serviceAccount:${google_service_account.job-scheduler-service-account.email}"
}

# Give the Service Account the Cloud Run Invoker role
resource "google_project_iam_member" "job-scheduler-sa-bigquery-job-user-role" {
  project = var.project
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.job-scheduler-service-account.email}"
}

# Give the Cloud Build Service Account permissions to act as the Cloud Run service account so it can deploy a revision to Cloud Run
resource "google_service_account_iam_member" "act-as-cloud-run-sa" {
  service_account_id = google_service_account.job-scheduler-service-account.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${data.google_project.project.number}@cloudbuild.gserviceaccount.com"
}

# Give the Service Account the Big Query Data Editor role
resource "google_project_iam_member" "job-scheduler-sa-bq-admin-role" {
  project = var.project
  role    = "roles/bigquery.admin"
  member  = "serviceAccount:${google_service_account.job-scheduler-service-account.email}"
}

# Give the Service Account the Big Query Data Editor role
resource "google_project_iam_member" "job-scheduler-sa-bq-data-editor-role" {
  project = var.project
  role    = "roles/bigquery.dataEditor"
  member  = "serviceAccount:${google_service_account.job-scheduler-service-account.email}"
}

# Give the Service Account the Big Query Data Editor role
resource "google_project_iam_member" "job-scheduler-sa-bq-data-owner-role" {
  project = var.project
  role    = "roles/bigquery.dataOwner"
  member  = "serviceAccount:${google_service_account.job-scheduler-service-account.email}"
}

# Give the Service Account the GCS Object User
resource "google_project_iam_member" "job-scheduler-sa-gcs-admin-role" {
  project = var.project
  role    = "roles/storage.admin"
  member  = "serviceAccount:${google_service_account.job-scheduler-service-account.email}"
}

# Give the Service Account the GCS Object Creator
resource "google_project_iam_member" "job-scheduler-sa-gcs-creator-role" {
  project = var.project
  role    = "roles/storage.objectCreator"
  member  = "serviceAccount:${google_service_account.job-scheduler-service-account.email}"
}

# Give the Service Account the GCS Object Viewer
resource "google_project_iam_member" "job-scheduler-sa-gcs-viewer-role" {
  project = var.project
  role    = "roles/storage.objectViewer"
  member  = "serviceAccount:${google_service_account.job-scheduler-service-account.email}"
}

# Create the job-scheduler Cloud Run service
resource "google_cloud_run_v2_service" "job-scheduler" {
  name     = "job-scheduler"
  location = var.region
  ingress = "INGRESS_TRAFFIC_ALL"
  template {
    labels = {
      managed-by = "terraform"
    } 
    scaling {
      min_instance_count = 0
      max_instance_count = 1
    } 
    timeout = "3600s"
    service_account = google_service_account.job-scheduler-service-account.email   
    containers {
      image = "us-docker.pkg.dev/cloudrun/container/hello" #"${var.region}-docker.pkg.dev/${var.project}/job-scheduler/job-scheduler:latest" #"us-docker.pkg.dev/cloudrun/container/hello"
      env {
        name  = "PROJECT_ID"
        value = var.project
      } 
      env {
        name  = "DATASET_ID"
        value = "mstudy"
      } 
      env {
        name  = "RAW_TARGET_TABLE"
        value = "target2"
      } 
      env {
        name  = "TARGET_TABLE"
        value = "target2_ordered"
      }
      env {
        name  = "RAW_SOURCE_TABLES"
        value = "source-uipetmis:source-uispet"
      } 
      env {
        name  = "RAW_SOURCE_TABLES_WILDCARD"
        value = "source-*"
      }
      env {
        name  = "SOURCE_TABLE"
        value = "source_ordered"
      }       
      env {
        name  = "QUEUED_JOBS_BUCKET_NAME"
        value = google_storage_bucket.queued-jobs-bucket.name
      }   
      ports {
        container_port = 80
      }
      resources {
        limits = {
          cpu = "1",
          memory = "4Gi"
        }
      }
    }
    max_instance_request_concurrency = 1
  }

  lifecycle {
    ignore_changes = [
      client,
      client_version,
      template[0].containers[0].image
    ]
  }

  depends_on = [google_service_account_iam_member.act-as-cloud-run-sa]
}