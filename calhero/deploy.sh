#!/bin/bash
# Deployment script for Calendar Parser
# Supports multiple deployment targets and parser types

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
PARSER_TYPE="ml"
DEPLOYMENT_TYPE=""
PROJECT_ID=""
REGION="us-central1"
SERVICE_NAME="calhero"

# Print colored output
print_info() { echo -e "${BLUE}ℹ${NC}  $1"; }
print_success() { echo -e "${GREEN}✓${NC}  $1"; }
print_warning() { echo -e "${YELLOW}⚠${NC}  $1"; }
print_error() { echo -e "${RED}✗${NC}  $1"; }

# Usage information
usage() {
    cat << EOF
Calendar Parser Deployment Script
==================================

Usage: ./deploy.sh [OPTIONS]

Options:
    -t, --type TYPE          Deployment type: docker|cloudrun|function
    -p, --parser PARSER      Parser type: ml|llm|both (default: ml)
    -i, --project-id ID      GCP Project ID (required for cloudrun)
    -r, --region REGION      GCP Region (default: us-central1)
    -n, --name NAME          Service name (default: calhero)
    -h, --help              Show this help message

Parser Types:
    ml      - ML/OCR only (Tesseract, smaller image)
    llm     - LLM only (Gemini, no Tesseract)
    both    - Both parsers, switch at runtime (default)

Examples:
    # Deploy to Cloud Run with ML parser
    ./deploy.sh --type cloudrun --parser ml --project-id my-project

    # Deploy to Cloud Run with both parsers (switch at runtime)
    ./deploy.sh --type cloudrun --parser both --project-id my-project

    # Build Docker image locally
    ./deploy.sh --type docker --parser ml

    # Deploy Cloud Function
    ./deploy.sh --type function --project-id my-project

EOF
    exit 1
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--type)
            DEPLOYMENT_TYPE="$2"
            shift 2
            ;;
        -p|--parser)
            PARSER_TYPE="$2"
            shift 2
            ;;
        -i|--project-id)
            PROJECT_ID="$2"
            shift 2
            ;;
        -r|--region)
            REGION="$2"
            shift 2
            ;;
        -n|--name)
            SERVICE_NAME="$2"
            shift 2
            ;;
        -h|--help)
            usage
            ;;
        *)
            print_error "Unknown option: $1"
            usage
            ;;
    esac
done

# Validate deployment type
if [ -z "$DEPLOYMENT_TYPE" ]; then
    print_error "Deployment type required"
    usage
fi

# Main deployment logic
case $DEPLOYMENT_TYPE in
    docker)
        print_info "Building Docker image with $PARSER_TYPE parser..."
        
        if [ "$PARSER_TYPE" = "both" ]; then
            docker build -t $SERVICE_NAME .
        else
            docker build --build-arg PARSER_TYPE=$PARSER_TYPE -t $SERVICE_NAME .
        fi
        
        print_success "Docker image built: $SERVICE_NAME"
        print_info "Run with: docker run -e USE_LLM=false $SERVICE_NAME"
        ;;
        
    cloudrun)
        if [ -z "$PROJECT_ID" ]; then
            print_error "Project ID required for Cloud Run deployment"
            usage
        fi
        
        print_info "Deploying to Cloud Run..."
        print_info "  Project: $PROJECT_ID"
        print_info "  Region: $REGION"
        print_info "  Service: $SERVICE_NAME"
        print_info "  Parser: $PARSER_TYPE"
        
        # Set default environment variables based on parser type
        if [ "$PARSER_TYPE" = "llm" ]; then
            ENV_VARS="USE_LLM=true"
            print_warning "Remember to set GEMINI_API_KEY after deployment!"
        else
            ENV_VARS="USE_LLM=false"
        fi
        
        # Deploy with gcloud
        gcloud run deploy $SERVICE_NAME \
            --source . \
            --platform managed \
            --region $REGION \
            --project $PROJECT_ID \
            --allow-unauthenticated \
            --set-env-vars $ENV_VARS \
            --memory 1Gi \
            --timeout 300s \
            --min-instances 0 \
            --max-instances 5
        
        # Get service URL
        SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
            --platform managed \
            --region $REGION \
            --project $PROJECT_ID \
            --format 'value(status.url)')
        
        print_success "Deployed successfully!"
        print_info "Service URL: $SERVICE_URL"
        print_info "Test with: curl $SERVICE_URL/health"
        
        if [ "$PARSER_TYPE" = "llm" ]; then
            print_warning ""
            print_warning "To set GEMINI_API_KEY:"
            print_warning "  gcloud run services update $SERVICE_NAME \\"
            print_warning "    --set-env-vars GEMINI_API_KEY=your_key_here"
        fi
        ;;
        
    function)
        if [ -z "$PROJECT_ID" ]; then
            print_error "Project ID required for Cloud Functions deployment"
            usage
        fi
        
        print_info "Deploying to Cloud Functions..."
        
        gcloud functions deploy parse_calendar_screenshot \
            --gen2 \
            --runtime python311 \
            --region $REGION \
            --project $PROJECT_ID \
            --trigger-http \
            --allow-unauthenticated \
            --entry-point parse_calendar_screenshot \
            --source . \
            --memory 1GB \
            --timeout 300s
        
        print_success "Deployed successfully!"
        print_info "Test with: gcloud functions call parse_calendar_screenshot"
        ;;
        
    *)
        print_error "Invalid deployment type: $DEPLOYMENT_TYPE"
        usage
        ;;
esac

print_success "Deployment complete!"
