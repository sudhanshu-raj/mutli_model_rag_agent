# QueryPilot - LLM-Powered Document Analysis

## Description
QueryPilot is a web application that processes PDFs and other documents using LLM technology to provide intelligent analysis and querying capabilities.

## Setup Instructions

### Prerequisites
- Docker and Docker Compose
- Git

### Installation
1. Clone this repository
2. Copy `.env.example` to `.env` and fill in your credentials
3. Run `docker-compose -f docker-compose-prod.yml up -d`
4. Access the application at http://localhost or your domain

### Environment Variables
See `.env.example` for required environment variables.

## Development
For development environment, use `docker-compose up -d` instead.