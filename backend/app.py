"""
FastAPI Backend for Document Workflow Tool
Handles file uploads, table extraction, and downloads
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import tempfile
import shutil
import os
import json
import uuid
from pathlib import Path
import logging

# Import our table extractor - FIXED IMPORT
from extractor import TableExtractor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Document Workflow API",
    description="API for extracting tables from PDF and DOCX documents",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize table extractor
extractor = TableExtractor()

# Pydantic models for request/response
class ExtractionResponse(BaseModel):
    extraction_id: str
    tables: List[Dict]
    file_name: str
    status: str
    extraction_method: Optional[str] = None
    error: Optional[str] = None

class DownloadRequest(BaseModel):
    extraction_id: str
    format: str  # 'csv' or 'json'
    table_id: Optional[str] = None  # For specific table download

class ExtractRequest(BaseModel):
    file_id: str

# In-memory storage for demo (use Redis/DB in production)
extraction_cache = {}
temp_files = {}

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Document Workflow API is running",
        "version": "1.0.0",
        "endpoints": ["/upload", "/extract", "/download", "/docs"]
    }

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload document file (PDF or DOCX)
    Returns upload confirmation with file ID
    """
    try:
        # Validate file type
        allowed_extensions = {'.pdf', '.docx', '.doc'}
        file_extension = Path(file.filename).suffix.lower()

        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type: {file_extension}. Allowed: {', '.join(allowed_extensions)}"
            )

        # Generate unique file ID
        file_id = str(uuid.uuid4())

        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(
            delete=False, 
            suffix=file_extension,
            prefix=f"upload_{file_id}_"
        )

        # Copy uploaded file content to temporary file
        shutil.copyfileobj(file.file, temp_file)
        temp_file.close()

        # Store file info
        temp_files[file_id] = {
            "path": temp_file.name,
            "original_name": file.filename,
            "size": os.path.getsize(temp_file.name),
            "extension": file_extension
        }

        logger.info(f"File uploaded successfully: {file.filename} -> {file_id}")

        return {
            "file_id": file_id,
            "filename": file.filename,
            "size": temp_files[file_id]['size'],  # Return as integer
            "status": "uploaded"
        }

    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

@app.post("/extract", response_model=ExtractionResponse)
async def extract_tables(request: ExtractRequest):
    """Extract tables from uploaded document"""
    file_id = request.file_id

    try:
        if file_id not in temp_files:
            raise HTTPException(status_code=404, detail="File not found. Please upload file first.")

        file_info = temp_files[file_id]
        file_path = file_info["path"]

        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File no longer exists on server.")

        logger.info(f"Starting extraction for file: {file_info['original_name']}")

        extraction_result = extractor.extract_tables(file_path)
        extraction_id = str(uuid.uuid4())

        extraction_cache[extraction_id] = {
            **extraction_result,
            "file_id": file_id,
            "extraction_id": extraction_id
        }

        logger.info(f"Extraction completed. Found {len(extraction_result.get('tables', []))} tables")

        return ExtractionResponse(
            extraction_id=extraction_id,
            tables=extraction_result.get("tables", []),
            file_name=extraction_result.get("file_name", file_info["original_name"]),
            status=extraction_result.get("status", "unknown"),
            extraction_method=extraction_result.get("extraction_method"),
            error=extraction_result.get("error")
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Extraction error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Table extraction failed: {str(e)}")

@app.get("/extract/{file_id}")
async def extract_tables_get(file_id: str):
    """
    Alternative GET endpoint for extraction (for easier testing)
    """
    request = ExtractRequest(file_id=file_id)
    return await extract_tables(request)

@app.post("/download")
async def download_tables(request: DownloadRequest):
    """
    Download extracted tables as CSV or JSON
    """
    try:
        # Validate extraction ID
        if request.extraction_id not in extraction_cache:
            raise HTTPException(status_code=404, detail="Extraction not found.")
        
        extraction_data = extraction_cache[request.extraction_id]
        tables = extraction_data.get("tables", [])
        
        if not tables:
            raise HTTPException(status_code=404, detail="No tables found in extraction.")
        
        # Create temporary directory for downloads
        download_dir = tempfile.mkdtemp(prefix="download_")
        
        try:
            if request.format.lower() == "csv":
                # Export specific table or all tables to CSV
                if request.table_id:
                    # Find specific table
                    target_table = next((t for t in tables if t.get("table_id") == request.table_id), None)
                    if not target_table:
                        raise HTTPException(status_code=404, detail=f"Table {request.table_id} not found.")
                    tables_to_export = [target_table]
                else:
                    tables_to_export = tables
                
                csv_files = extractor.export_to_csv(tables_to_export, download_dir)
                
                if len(csv_files) == 1:
                    # Single file download
                    return FileResponse(
                        csv_files[0],
                        media_type="text/csv",
                        filename=Path(csv_files[0]).name
                    )
                else:
                    # Multiple files - create ZIP (simplified: return first file for demo)
                    return FileResponse(
                        csv_files[0],
                        media_type="text/csv",
                        filename="extracted_tables.csv"
                    )
                    
            elif request.format.lower() == "json":
                # Export to JSON
                json_path = Path(download_dir) / "extraction_result.json"
                extractor.export_to_json(extraction_data, json_path)
                
                return FileResponse(
                    json_path,
                    media_type="application/json",
                    filename="extraction_result.json"
                )
                
            else:
                raise HTTPException(status_code=400, detail="Invalid format. Use 'csv' or 'json'.")
                
        except Exception as e:
            # Clean up download directory
            shutil.rmtree(download_dir, ignore_errors=True)
            raise
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")

@app.get("/download/{extraction_id}/{format}")
async def download_tables_get(extraction_id: str, format: str, table_id: Optional[str] = None):
    """
    Alternative GET endpoint for downloads
    """
    request = DownloadRequest(
        extraction_id=extraction_id,
        format=format,
        table_id=table_id
    )
    return await download_tables(request)

@app.get("/extractions")
async def list_extractions():
    """
    List all cached extractions (for debugging)
    """
    return {
        "extractions": [
            {
                "extraction_id": eid,
                "file_name": data.get("file_name", "unknown"),
                "status": data.get("status", "unknown"),
                "table_count": len(data.get("tables", []))
            }
            for eid, data in extraction_cache.items()
        ]
    }

@app.get("/extractions/{extraction_id}")
async def get_extraction(extraction_id: str):
    """
    Get specific extraction details
    """
    if extraction_id not in extraction_cache:
        raise HTTPException(status_code=404, detail="Extraction not found.")
    
    return extraction_cache[extraction_id]

@app.delete("/cleanup")
async def cleanup_temp_files():
    """
    Clean up temporary files (for maintenance)
    """
    cleaned_files = 0
    
    for file_id, file_info in list(temp_files.items()):
        try:
            if os.path.exists(file_info["path"]):
                os.unlink(file_info["path"])
                cleaned_files += 1
            del temp_files[file_id]
        except Exception as e:
            logger.error(f"Error cleaning up {file_id}: {e}")
    
    # Clear extraction cache
    extraction_cache.clear()
    
    return {"message": f"Cleaned up {cleaned_files} temporary files and all cached extractions."}

# Background task to clean up old files periodically
def cleanup_old_files():
    """Background task to clean up files older than 1 hour"""
    import time
    
    for file_id, file_info in list(temp_files.items()):
        try:
            file_path = file_info["path"]
            if os.path.exists(file_path):
                # Check if file is older than 1 hour
                if time.time() - os.path.getctime(file_path) > 3600:
                    os.unlink(file_path)
                    del temp_files[file_id]
                    logger.info(f"Cleaned up old file: {file_id}")
        except Exception as e:
            logger.error(f"Error in background cleanup: {e}")

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"detail": "Resource not found", "path": str(request.url)}
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "message": str(exc)}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)