# Deployment Guide

## Overview
This guide covers different deployment options for the Document Workflow Tool, from local development to production environments.

## Table of Contents
1. [Local Development](#local-development)
2. [Docker Deployment](#docker-deployment)
3. [Cloud Deployment](#cloud-deployment)
4. [Production Considerations](#production-considerations)
5. [Monitoring & Logging](#monitoring--logging)

## Local Development

### Prerequisites
- Python 3.8+
- pip package manager
- Git

### Setup Steps
```bash
# Clone repository
git clone <repository-url>
cd document-workflow-tool

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start backend
cd backend
uvicorn app:app --reload --host 0.0.0.0 --port 8000

# Start frontend (new terminal)
cd streamlit_app
streamlit run app.py --server.port 8501
```

### Environment Variables
Create a `.env` file in the root directory:
```env
# Backend Configuration
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=10485760  # 10MB in bytes

# Streamlit Configuration
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Development Settings
DEBUG=True
LOG_LEVEL=INFO
```

## Docker Deployment

### Prerequisites
- Docker
- Docker Compose

### Docker Configuration

#### Backend Dockerfile
```dockerfile
# backend/Dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Frontend Dockerfile
```dockerfile
# streamlit_app/Dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY ../requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8501

# Run Streamlit
CMD ["streamlit", "run", "app.py", "--server.address", "0.0.0.0"]
```

#### Docker Compose
```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - UPLOAD_DIR=/app/uploads
      - MAX_FILE_SIZE=10485760
    volumes:
      - ./uploads:/app/uploads
      - ./logs:/app/logs
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    build: ./streamlit_app
    ports:
      - "8501:8501"
    environment:
      - BACKEND_URL=http://backend:8000
    depends_on:
      - backend
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - backend
      - frontend
```

#### Nginx Configuration
```nginx
# nginx.conf
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:8000;
    }
    
    upstream frontend {
        server frontend:8501;
    }
    
    server {
        listen 80;
        
        location /api/ {
            proxy_pass http://backend/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
        
        location / {
            proxy_pass http://frontend/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
```

### Deploy with Docker
```bash
# Build and start services
docker-compose up --build -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Cloud Deployment

### AWS Deployment

#### Using AWS ECS
```yaml
# ecs-task-definition.json
{
  "family": "document-workflow-tool",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "backend",
      "image": "your-registry/document-workflow-backend:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "UPLOAD_DIR",
          "value": "/app/uploads"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/document-workflow-tool",
          "awslogs-region": "us-west-2",
          "awslogs-stream-prefix": "backend"
        }
      }
    }
  ]
}
```

#### Using AWS Lambda (Serverless)
```yaml
# serverless.yml
service: document-workflow-tool

provider:
  name: aws
  runtime: python3.9
  region: us-west-2
  
functions:
  extract:
    handler: lambda_handler.extract_handler
    timeout: 300
    memorySize: 1024
    events:
      - http:
          path: extract
          method: post
          cors: true
```

### Google Cloud Platform

#### App Engine Deployment
```yaml
# app.yaml
runtime: python39

env_variables:
  UPLOAD_DIR: /tmp/uploads
  MAX_FILE_SIZE: 10485760

resources:
  cpu: 1
  memory_gb: 2
  disk_size_gb: 10

automatic_scaling:
  min_instances: 1
  max_instances: 10
```

### Heroku Deployment

#### Procfile
```
web: uvicorn backend.app:app --host 0.0.0.0 --port $PORT
streamlit: streamlit run streamlit_app/app.py --server.port $PORT --server.address 0.0.0.0
```

#### heroku.yml
```yaml
build:
  docker:
    web: backend/Dockerfile
    streamlit: streamlit_app/Dockerfile
```

## Production Considerations

### Security
1. **API Security**
   ```python
   # Add authentication middleware
   from fastapi import Depends, HTTPException, status
   from fastapi.security import HTTPBearer
   
   security = HTTPBearer()
   
   def authenticate(credentials: HTTPAuthorizationCredentials = Depends(security)):
       # Implement your authentication logic
       pass
   ```

2. **File Upload Security**
   - Implement file type validation
   - Scan uploads for viruses
   - Limit file sizes
   - Use secure file storage

3. **HTTPS Configuration**
   ```nginx
   server {
       listen 443 ssl;
       ssl_certificate /path/to/certificate.crt;
       ssl_certificate_key /path/to/private.key;
   }
   ```

### Performance Optimization

1. **Database Connection Pooling**
   ```python
   from sqlalchemy import create_engine
   from sqlalchemy.pool import QueuePool
   
   engine = create_engine(
       DATABASE_URL,
       poolclass=QueuePool,
       pool_size=20,
       max_overflow=0
   )
   ```

2. **Caching**
   ```python
   from redis import Redis
   
   redis_client = Redis(host='redis', port=6379, db=0)
   ```

3. **Resource Limits**
   ```yaml
   # docker-compose.yml
   services:
     backend:
       deploy:
         resources:
           limits:
             cpus: '1.0'
             memory: 2G
           reservations:
             cpus: '0.5'
             memory: 1G
   ```

### Scaling Strategies

1. **Horizontal Scaling**
   ```yaml
   # kubernetes deployment
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: document-workflow-backend
   spec:
     replicas: 3
     selector:
       matchLabels:
         app: backend
     template:
       spec:
         containers:
         - name: backend
           image: document-workflow-backend:latest
           resources:
             requests:
               memory: "1Gi"
               cpu: "500m"
             limits:
               memory: "2Gi"
               cpu: "1000m"
   ```

2. **Load Balancing**
   ```yaml
   apiVersion: v1
   kind: Service
   metadata:
     name: backend-service
   spec:
     selector:
       app: backend
     ports:
       - port: 8000
         targetPort: 8000
     type: LoadBalancer
   ```

## Monitoring & Logging

### Application Monitoring
```python
# Add to your FastAPI app
from prometheus_client import Counter, Histogram, generate_latest

REQUEST_COUNT = Counter('requests_total', 'Total requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('request_duration_seconds', 'Request duration')

@app.middleware("http")
async def monitor_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path).inc()
    REQUEST_DURATION.observe(duration)
    
    return response
```

### Logging Configuration
```python
# logging_config.py
import logging
from logging.handlers import RotatingFileHandler

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            RotatingFileHandler('app.log', maxBytes=10000000, backupCount=5),
            logging.StreamHandler()
        ]
    )
```

### Health Checks
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "checks": {
            "database": "healthy",
            "storage": "healthy",
            "memory_usage": f"{psutil.virtual_memory().percent}%"
        }
    }
```

## Troubleshooting

### Common Issues

1. **Port Conflicts**
   ```bash
   # Check what's running on port
   lsof -i :8000
   
   # Kill process
   kill -9 <PID>
   ```

2. **Memory Issues**
   ```bash
   # Monitor memory usage
   docker stats
   
   # Increase container memory
   docker run -m 2g your-image
   ```

3. **File Permission Issues**
   ```bash
   # Fix file permissions
   sudo chown -R $USER:$USER ./uploads
   chmod 755 ./uploads
   ```

### Performance Tuning

1. **Optimize PDF Processing**
   ```python
   # Use faster extraction methods
   tables = camelot.read_pdf(
       pdf_path,
       flavor='stream',  # Faster than 'lattice'
       pages='1-3'       # Limit pages
   )
   ```

2. **Database Optimization**
   ```sql
   -- Add indexes for frequently queried columns
   CREATE INDEX idx_file_id ON extractions(file_id);
   CREATE INDEX idx_created_at ON files(created_at);
   ```

## Maintenance

### Backup Strategy
```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
tar -czf backup_${DATE}.tar.gz ./uploads ./logs
aws s3 cp backup_${DATE}.tar.gz s3://your-backup-bucket/
```

### Update Procedure
1. Pull latest changes
2. Build new containers
3. Run database migrations
4. Deploy with zero downtime
5. Verify functionality
6. Rollback if issues occur

### Security Updates
```bash
# Update dependencies regularly
pip list --outdated
pip install --upgrade package-name

# Security scanning
safety check
bandit -r ./backend
```