# Get Project ID
data "google_project" "project" {
  project_id = var.project
}

###################
###################
# Part 1: Buckets #
###################
###################

# Bucket for in_progress_jobs_bucket
resource "google_storage_bucket" "in_progress_jobs_bucket" {
  name          = "${var.project}-in_progress_jobs_bucket"
  location      = var.region
  project       = var.project
  uniform_bucket_level_access = true
  force_destroy = true
  storage_class = "STANDARD"
}

# Bucket for completed_jobs_bucket
resource "google_storage_bucket" "completed_jobs_bucket" {
  name          = "${var.project}-completed_jobs_bucket"
  location      = var.region
  project       = var.project
  uniform_bucket_level_access = true
  force_destroy = true
  storage_class = "STANDARD"
}

# Bucket for failed_jobs_bucket
resource "google_storage_bucket" "failed_jobs_bucket" {
  name          = "${var.project}-failed_jobs_bucket"
  location      = var.region
  project       = var.project
  uniform_bucket_level_access = true
  force_destroy = true
  storage_class = "STANDARD"
}

# Bucket for bq_uploads_queue
resource "google_storage_bucket" "bq_upload_queue_bucket" {
  name          = "${var.project}-bq_upload_queue_bucket"
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

# Create the Service Account to use with the job-runner Cloud Run service
resource "google_service_account" "job-runner-service-account" {
  account_id   = "job-runner--sa"
  display_name = "job runner service account"
  description  = "Service Account for the job-runner Cloud Run Service"
}

# Create a Pub/Sub Topic used for notifications on bigquery updates
resource "google_pubsub_topic" "queued-jobs-bucket-notification-topic" {
  project     = var.project
  name     = "queued-jobs-bucket-notifications"
  provider = google-beta
}

# Enable notifications by giving the correct IAM permission to the unique service account.
data "google_storage_project_service_account" "gcs_account" {
  provider = google-beta
}

resource "google_pubsub_topic_iam_binding" "binding" {
  provider = google-beta
  topic    = google_pubsub_topic.queued-jobs-bucket-notification-topic.id
  role     = "roles/pubsub.publisher"
  members  = ["serviceAccount:${data.google_storage_project_service_account.gcs_account.email_address}"]
}

# Create a Pub/Sub notification.
resource "google_storage_notification" "queued-jobs-bucket-notification" {
  provider       = google-beta
  bucket         = var.queued-jobs-bucket-name
  payload_format = "JSON_API_V1"
  event_types    = ["OBJECT_FINALIZE"]
  topic          = google_pubsub_topic.queued-jobs-bucket-notification-topic.id
  depends_on     = [google_pubsub_topic_iam_binding.binding]
  
}

resource "google_project_service_identity" "pubsub_agent" {
  provider = google-beta
  project  = var.project
  service  = "pubsub.googleapis.com"
}

resource "google_project_iam_binding" "project_token_creator" {
  project = var.project
  role    = "roles/iam.serviceAccountTokenCreator"
  members = ["serviceAccount:${google_project_service_identity.pubsub_agent.email}"]
}

# Create the PubSub subscription for the bigquery updates topic
resource "google_pubsub_subscription" "job-runner-push" {
  project = var.project
  name  = "job-runner-push"
  topic = google_pubsub_topic.queued-jobs-bucket-notification-topic.name
  ack_deadline_seconds = 600 #maximum
  message_retention_duration = "259200s" #16hrs=57600. minimum is 600s
  retry_policy {
    minimum_backoff = "10s" #maximum
  }
  push_config {
    push_endpoint = google_cloud_run_v2_service.job-runner.uri
    oidc_token {
      service_account_email = google_service_account.job-runner-service-account.email
    }
    attributes = {
      x-goog-version = "v1"
    }
  }
  depends_on = [google_cloud_run_v2_service.job-runner]
}

resource "google_cloud_run_service_iam_member" "job-runner-service-account-iam-member" {
  project = var.project
  location = var.region
  service  = google_cloud_run_v2_service.job-runner.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.job-runner-service-account.email}"
}

############################
############################
# Part 3: job-runner Image #
############################
############################

resource "google_artifact_registry_repository" "job-runner" {
  location      = var.region
  repository_id = "job-runner"
  description   = "Managed by Terraform - Do not manually edit - job-runner repository"
  format        = "DOCKER"

  docker_config {
    immutable_tags = false
  }

  lifecycle {
    ignore_changes = [ docker_config ]
  }
}

resource "google_cloudbuild_trigger" "job-runner-trigger" {
  location = var.region
  name        = "job-runner-build-deploy"
  description = "Managed by Terraform - Do not manually edit - job-runner image build"
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

  included_files = ["data-mapping-poc/job-runner/**"]

  filename = "data-mapping-poc/cloudbuild/job-runner/cloudbuild.yaml"
}

########################################
########################################
# Part 4: job-runner Cloud Run service #
########################################
########################################

# Give the Service Account the Big Query Data Editor role
resource "google_project_iam_member" "job-runner-sa-bq-admin-role" {
  project = var.project
  role    = "roles/bigquery.admin"
  member  = "serviceAccount:${google_service_account.job-runner-service-account.email}"
}

# Give the Service Account the Big Query Data Editor role
resource "google_project_iam_member" "job-runner-sa-bq-data-editor-role" {
  project = var.project
  role    = "roles/bigquery.dataEditor"
  member  = "serviceAccount:${google_service_account.job-runner-service-account.email}"
}

# Give the Service Account the Big Query Data Editor role
resource "google_project_iam_member" "job-runner-sa-bq-data-owner-role" {
  project = var.project
  role    = "roles/bigquery.dataOwner"
  member  = "serviceAccount:${google_service_account.job-runner-service-account.email}"
}

# Give the Service Account the Firestore Owner role
resource "google_project_iam_member" "job-runner-sa-firestore-owner-role" {
  project = var.project
  role    = "roles/datastore.owner"
  member  = "serviceAccount:${google_service_account.job-runner-service-account.email}"
}

# Give the Service Account the GCS Object User
resource "google_project_iam_member" "job-runner-sa-gcs-object-admin-role" {
  project = var.project
  role    = "roles/storage.objectAdmin"
  member  = "serviceAccount:${google_service_account.job-runner-service-account.email}"
}

# Give the Service Account the GCS Object User
resource "google_project_iam_member" "job-runner-sa-gcs-admin-role" {
  project = var.project
  role    = "roles/storage.admin"
  member  = "serviceAccount:${google_service_account.job-runner-service-account.email}"
}

# Give the Service Account the GCS Object Creator
resource "google_project_iam_member" "job-runner-sa-gcs-creator-role" {
  project = var.project
  role    = "roles/storage.objectCreator"
  member  = "serviceAccount:${google_service_account.job-runner-service-account.email}"
}

# Give the Service Account the GCS Object Viewer
resource "google_project_iam_member" "job-runner-sa-gcs-viewer-role" {
  project = var.project
  role    = "roles/storage.objectViewer"
  member  = "serviceAccount:${google_service_account.job-runner-service-account.email}"
}

resource "google_project_iam_member" "job-runner-sa-ai-platform-user" {
  project = var.project
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.job-runner-service-account.email}"
}

resource "google_project_iam_member" "job-runner-sa-discovery-engine-admin" {
  project = var.project
  role    = "roles/discoveryengine.admin"
  member  = "serviceAccount:${google_service_account.job-runner-service-account.email}"
}

# Give the Cloud Build Service Account permissions to act as the Cloud Run service account so it can deploy a revision to Cloud Run
resource "google_service_account_iam_member" "act-as-cloud-run-sa-job-runner" {
  service_account_id = google_service_account.job-runner-service-account.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${data.google_project.project.number}@cloudbuild.gserviceaccount.com"
}

# Create the job-runner Cloud Run service with a placeholder container image
resource "google_cloud_run_v2_service" "job-runner" {
  name     = "job-runner"
  location = var.region
  ingress = "INGRESS_TRAFFIC_ALL"
  template {
    labels = {
      managed-by = "terraform"
    } 
    scaling {
      min_instance_count = 1
      max_instance_count = 20
    }
    timeout = "3600s"
    service_account = google_service_account.job-runner-service-account.email   
    containers {
      image =  "${var.region}-docker.pkg.dev/${var.project}/job-runner/job-runner:latest" #"us-docker.pkg.dev/cloudrun/container/hello" # "${var.region}-docker.pkg.dev/${var.project}/job-runner/job-runner:latest"
      env {
        name  = "PROJECT_ID"
        value = var.project
      } 
      env {
        name  = "DATASET_ID"
        value = var.dataset-id
      } 
      env {
        name  = "TARGET_TABLE"
        value = var.target_table
      }
      env {
        name  = "MAPPED_TABLE"
        value = var.mapped_table
      } 
      env {
        name  = "SOURCE_TABLE"
        value = var.source_table
      } 
      env {
        name  = "IN_PROGRESS_JOBS_BUCKET_NAME"
        value = google_storage_bucket.in_progress_jobs_bucket.name
      }
      env {
        name  = "COMPLETED_JOBS_BUCKET_NAME"
        value = google_storage_bucket.completed_jobs_bucket.name
      }       
      env {
        name  = "FAILED_JOBS_BUCKET_NAME"
        value = google_storage_bucket.failed_jobs_bucket.name
      }
      env {
        name  = "BQ_UPLOAD_QUEUE_BUCKET_NAME"
        value = google_storage_bucket.bq_upload_queue_bucket.name
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
    max_instance_request_concurrency = 5
  }

  lifecycle {
    ignore_changes = [
      client,
      client_version,
      template[0].containers[0].image
    ]
  }

  depends_on = [
    google_service_account_iam_member.act-as-cloud-run-sa-job-runner,
    google_artifact_registry_repository.job-runner
    ]
}