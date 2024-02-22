resource "google_project_iam_member" "weekss-owner" {
  project = var.project
  role    = "roles/editor"
  member  = "user:weekss@google.com"
}