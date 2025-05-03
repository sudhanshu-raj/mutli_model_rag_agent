# QueryPilot - LLM-Powered Document Intelligence Platform

![chat_Section](https://github.com/user-attachments/assets/6ec4f3f0-c89a-413f-9412-facbe7852c28)


---

## Table of Contents

* [Introduction](#introduction)
* [Features](#features)
* [Architecture Overview](#architecture-overview)
* [Technology Stack](#technology-stack)
* [Prerequisites](#prerequisites)
* [Installation](#installation)

  * [Development Setup](#development-setup)
  * [Production Deployment](#production-deployment)
* [Configuration](#configuration)
* [Project Structure](#project-structure)
* [API Endpoints](#api-endpoints)
* [Frontend Components](#frontend-components)
* [Vector Storage](#vector-storage)
* [Document Processing Pipeline](#document-processing-pipeline)
* [AI Integration](#ai-integration)
* [Troubleshooting](#troubleshooting)
* [Contributing](#contributing)
* [License](#license)

---

## Introduction

QueryPilot is an advanced document intelligence platform that combines Large Language Models (LLMs) with vector embeddings to enable natural language querying of your documents. The application processes various file formats (PDFs, DOCXs, TXT files, and images), extracting and embedding content for semantic search and AI-powered analysis.

Users can organize documents into workspaces, chat with their content, and receive intelligent responses based on document contexts. The platform supports multi-modal analysis, handling both text and image content seamlessly.

## Features

* **Multi-format Document Processing**: Supports PDF, DOCX, TXT, and image files
* **Workspace Management**: Organize documents into logical workspaces
* **AI-Powered Chat**: Interact with documents using natural language
* **Image Analysis**: Extract and analyze content from images
* **Text Extraction & Analysis**: Process text from various sources
* **Vector-based Semantic Search**: Find information by meaning, not just keywords
* **Multi-modal Document Intelligence**: Combine text and image understanding
* **User-friendly Interface**: Clean, responsive design with dark mode support
* **API-first Architecture**: Well-structured backend with comprehensive API endpoints
* **Containerized Deployment**: Easy setup with Docker and docker-compose

## Workspace Section:
* Can create multiple workspaces , this gives the way to  keep the docs in structured way which can be easy to search later. 
* **Feature Improvement** : Can add the search input from all the workspace
  
  ![workspace](https://github.com/user-attachments/assets/d7eee39c-e301-4b79-bcb8-9de9e46f15fc)

## Upload Section: 
* **Support** : It supports multiple file max 15 mb, supported formats: [".docx", ".doc", ".pdf", ".txt", ".json", ".jpg", ".png", ".jpeg", ".md",".webp"] 
* **Feature Improvement** : Can add many sources like google sources, and much more

![uploads_section](https://github.com/user-attachments/assets/bc17cc23-d70c-470a-9529-6290b8d7a656)

## Chat section :
* It supports images also with the response ,like with pdf it will also give the reference images of the answer.
* Can search from direct images uploaded by toggling to image .
* Can also view the file uploaded very easily .
* Improvements: well there is lot of improvements  there in this while project  , this is just simple approach to query from your data given.

  ![chat_Section](https://github.com/user-attachments/assets/a9465eaa-474b-4b16-94bb-d958e77b2e98)

  ![image_Search](https://github.com/user-attachments/assets/45d97928-c8d6-433b-a1d2-f2eb16bd5033)


## Architecture Overview

```text
                                +----------------+
                                |  Nginx Proxy   |
                                +--------+-------+
                                         |
                 +----------------------+----------------------+
                 |                                             |
        +--------v--------+                         +----------v---------+
        | React Frontend  |                         |   Flask Backend    |
        +-----------------+                         +----------+---------+
                                                               |
                                               +---------------+---------------+
                                               |                               |
                                    +----------v----------+        +-----------v-----------+
                                    |   MySQL Database     |        |   Vector Store (ChromaDB) |
                                    +----------------------+        +-------------------------+
```

## Technology Stack

### Frontend

* React 18+
* Vite
* CSS Modules
* ReactMarkdown
* Axios

### Backend

* Python 3.11
* Flask
* Gunicorn
* MySQL Connector
* Sentence Transformers
* Google Gemini API
* PyPDF

### Infrastructure

* Docker & Docker Compose
* Nginx
* MySQL 8.0
* ChromaDB

## Prerequisites

* Docker & Docker Compose
* Git
* 8GB+ RAM (recommended)
* Google Gemini API key

## Installation

### Development Setup

```bash
git clone https://github.com/sudhanshu-raj/mutli_model_rag_agent.git
cd mutli_model_rag_agent

cp .env.example .env
```

Edit `.env` and configure:

```env
GEMINI_API_KEY=your-gemini-api-key
DB_HOST=mysql
DB_USER=root
DB_PASSWORD=your-password
DB_NAME=pdf_qa
ADMIN_PASSWORD=your-admin-password
FRONTEND_ORIGINS=http://localhost:5173
BASE_URL=http://localhost:5000
MYSQL_ROOT_PASSWORD=your-mysql-root-password
MYSQL_DATABASE=pdf_qa
VITE_BACKEND_URL=http://localhost:5000
```

Start the environment:

```bash
docker-compose up -d
```

Visit: [http://localhost:5173](http://localhost:5173)

### Production Deployment

1. Configure `.env` (production values).
2. Start:

```bash
docker-compose -f docker-compose-prod.yml up -d
```

3. SSL Setup:

```bash
docker-compose -f docker-compose-prod.yml stop nginx
certbot certonly --standalone -d your-domain.com -d www.your-domain.com

mkdir -p nginx/ssl/your-domain.com
cp /etc/letsencrypt/live/your-domain.com/fullchain.pem nginx/ssl/your-domain.com/
cp /etc/letsencrypt/live/your-domain.com/privkey.pem nginx/ssl/your-domain.com/

docker-compose -f docker-compose-prod.yml up -d nginx
```

Visit: [https://your-domain.com](https://your-domain.com)

## Configuration

### Environment Variables

| Variable              | Description           | Default                                        |
| --------------------- | --------------------- | ---------------------------------------------- |
| GEMINI\_API\_KEY      | Google Gemini API key | None                                           |
| DB\_HOST              | DB Hostname           | mysql                                          |
| DB\_USER              | DB Username           | root                                           |
| DB\_PASSWORD          | DB Password           | None                                           |
| DB\_NAME              | DB Name               | pdf\_qa                                        |
| ADMIN\_PASSWORD       | Admin password        | None                                           |
| FRONTEND\_ORIGINS     | CORS origins          | [http://localhost:5173](http://localhost:5173) |
| BASE\_URL             | API base URL          | [http://localhost/api](http://localhost/api)   |
| MYSQL\_ROOT\_PASSWORD | MySQL root password   | None                                           |
| MYSQL\_DATABASE       | MySQL DB              | pdf\_qa                                        |
| VITE\_BACKEND\_URL    | Frontend backend URL  | [http://localhost/api](http://localhost/api)   |
| FLASK\_ENV            | Flask env             | development                                    |

### Nginx Configuration (default.prod.conf)

```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name your-domain.com www.your-domain.com;

    client_max_body_size 50M;

    ssl_certificate /etc/nginx/ssl/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/your-domain.com/privkey.pem;

    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://backend:5000/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Project Structure

```
querypilot/
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── api_calls/
│   │   ├── component/
│   │   ├── pages/
│   │   │   ├── chatsection/
│   │   │   └── landingpage/
│   │   ├── services/
│   │   └── utils/
│   ├── index.html
│   ├── Dockerfile.prod
│   └── vite.config.js
│
├── backend/
│   ├── src/
│   │   ├── flaskAPI/
│   │   │   ├── chatAPI.py
│   │   │   ├── fileProcessingAPI.py
│   │   │   ├── fileManagerAPI.py
│   │   │   ├── workspaceManagerAPI.py
│   │   │   └── index.py
│   │   ├── database.py
│   │   ├── vector_store.py
│   │   ├── process_files.py
│   │   ├── qa_chain.py
│   │   └── config.py
│   └── Dockerfile.prod
│
├── nginx/
│   ├── default.prod.conf
│   └── Dockerfile.nginx
│
├── .env.example
├── docker-compose.yml
├── docker-compose-prod.yml
└── README.md
```

## API Endpoints

### File Management

* `GET /files/download/:filename`
* `POST /files/upload`

### File Processing

* `POST /process_file/process`
* `POST /process_file/generate_image_description`

### Workspace Management

* `GET /workspaces/`
* `GET /workspaces/:workspace_name`
* `GET /workspaces/:workspace_name/files`
* `POST /workspaces/`
* `DELETE /workspaces/:workspace_name`

### Chat Processing

* `POST /chat/process`

### File Access

* `GET /fileAccess/files/:workspace_name/:filename`

## Frontend Components

### Main Pages

* **Landing Page**: Intro to QueryPilot
* **Chat Interface**: Document querying

### Key Components

* `UploadPopUp`: File upload
* `WorkspaceSelector`: Workspace management
* `MarkdownViewer`: AI responses
* `FileItem`: File sidebar listing

## Vector Storage

### ChromaDB Collections

* **Text**:

  * Document ID
  * Text content
  * Metadata
  * Vector embeddings

* **Image**:

  * Document ID
  * Image description
  * Metadata
  * Vector embeddings

## Document Processing Pipeline

1. Upload
2. Text Extraction
3. Chunking
4. Embedding Generation
5. Vector Storage
6. Metadata Extraction

## AI Integration

Uses **Google Gemini API** for:

* Question Answering
* Image Analysis
* Text Summarization
* Context Validation

## Troubleshooting

### Common Issues

* **413 Request Entity Too Large**:

  * Fix: Increase `client_max_body_size`

* **Worker Timeout Errors**:

  * Fix: Increase Gunicorn timeout (`--timeout 900`)

* **Memory Issues**:

  * Fix: Ensure 4GB+ RAM

* **DB Connection Errors**:

  * Fix: Set `DB_HOST=mysql`



## License

MIT © 2024 QueryPilot Team
