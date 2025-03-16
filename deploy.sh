#!/bin/bash

# Set variables
PROJECT_ID="price-tracker-2025"
IMAGE_NAME="gcr.io/${PROJECT_ID}/price-tracker:latest"
SERVICE_NAME="price-tracker"
REGION="us-central1"

# MySQL credentials from your provided details
DB_USER="rondras"
DB_HOST="34.28.89.52"
DB_NAME="mydatabase"
INTERVAL_MINUTES="5"

# Check if .env file exists and source DB_PASSWORD
if [ -f ".env" ]; then
    source .env
    if [ -z "$DB_PASSWORD" ]; then
        echo "DB_PASSWORD not found in .env. Please enter it now:"
        read -s DB_PASSWORD
    fi
else
    echo "No .env file found. Please enter your DB_PASSWORD:"
    read -s DB_PASSWORD
fi

# Validate DB_PASSWORD is set
if [ -z "$DB_PASSWORD" ]; then
    echo "Error: DB_PASSWORD is required."
    exit 1
fi

# Step 1: Build the Docker image
echo "Building Docker image: $IMAGE_NAME"
docker build --no-cache -t "$IMAGE_NAME" . || {
    echo "Docker build failed."
    exit 1
}

# Step 2: Push the image to Artifact Registry
echo "Pushing image to Artifact Registry..."
docker push "$IMAGE_NAME" || {
    echo "Docker push failed."
    exit 1
}

# Step 3: Deploy to Cloud Run
echo "Deploying to Cloud Run..."
gcloud run deploy "$SERVICE_NAME" \
    --image "$IMAGE_NAME" \
    --platform managed \
    --region "$REGION" \
    --no-allow-unauthenticated \
    --set-env-vars "DB_USER=$DB_USER,DB_PASSWORD=$DB_PASSWORD,DB_HOST=$DB_HOST,DB_NAME=$DB_NAME,INTERVAL_MINUTES=$INTERVAL_MINUTES" || {
    echo "Cloud Run deployment failed."
    exit 1
}

echo "Deployment completed successfully."
echo "Next, set up Cloud Scheduler with the Service URL shown above."