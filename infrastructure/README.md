## Infrastructure

This directory provides for the deployment of the infrastructure for the gemini powered data mapping project

The deployment of the infrastructure is managed by Terraform and it uses a single Project.

Cloud Build is used as the environment to apply the Terraform from, and will run all the Cloud Build jobs from the same GCP Project. The Cloud Build execution YAML are available in the /cloudbuild directory.

Terraform State is stored in a GCS Bucket in the same Project.

### Infrastructure Deployment

Follow the intructions in the [root readme](../README.md)