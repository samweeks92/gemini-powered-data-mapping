# Output the backend service URI
output "queued-jobs-bucket-name" {
  value = google_storage_bucket.queued-jobs-bucket.name
}