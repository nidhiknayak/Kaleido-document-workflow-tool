# API Documentation

## Base URL
```
http://localhost:8000
```

## Authentication
Currently, no authentication is required for API endpoints.

## Endpoints

### 1. Health Check
**GET** `/health`

Check if the API is running.

#### Response
```json
{
  "status": "healthy",
  "timestamp": "2025-06-30T10:30:00Z"
}
```

### 2. Upload File
**POST** `/upload`

Upload a PDF or DOCX file for processing.

#### Request
- **Content-Type**: `multipart/form-data`
- **Body**: File upload with key `file`

#### Supported File Types
- PDF (`.pdf`)
- Microsoft Word (`.docx`)

#### Response
```json
{
  "file_id": "abc123def456",
  "filename": "document.pdf",
  "file_size": 1024576,
  "upload_time": "2025-06-30T10:30:00Z",
  "status": "uploaded"
}
```

#### Error Responses
```json
{
  "error": "File type not supported",
  "supported_types": [".pdf", ".docx"]
}
```

### 3. Extract Tables
**POST** `/extract`

Extract tables from an uploaded file.

#### Request
```json
{
  "file_id": "abc123def456",
  "extraction_options": {
    "pages": "all",
    "table_areas": null,
    "flavor": "camelot"
  }
}
```

#### Parameters
- `file_id` (required): File ID from upload response
- `extraction_options` (optional):
  - `pages`: Page numbers to process ("all", "1", "1,2,3", "1-5")
  - `table_areas`: Specific areas to extract from (array of coordinates)
  - `flavor`: Extraction method ("camelot", "pdfplumber")

#### Response
```json
{
  "file_id": "abc123def456",
  "extraction_id": "ext789ghi012",
  "tables_found": 2,
  "tables": [
    {
      "table_id": 0,
      "page": 1,
      "shape": [5, 3],
      "headers": ["Name", "Age", "City"],
      "data": [
        ["John Doe", "25", "New York"],
        ["Jane Smith", "30", "Los Angeles"],
        ["Bob Johnson", "35", "Chicago"]
      ],
      "confidence": 0.95
    }
  ],
  "processing_time": 2.3,
  "status": "completed"
}
```

#### Error Responses
```json
{
  "error": "File not found",
  "file_id": "abc123def456"
}
```

```json
{
  "error": "No tables found in document",
  "suggestions": [
    "Try different extraction method",
    "Check if document contains actual tables",
    "Verify page range"
  ]
}
```

### 4. Download Processed Data
**GET** `/download/{extraction_id}`

Download extracted data in specified format.

#### Parameters
- `extraction_id` (path): Extraction ID from extract response
- `format` (query): Output format ("csv", "json", "excel")
- `table_id` (query, optional): Specific table to download

#### Examples
```
GET /download/ext789ghi012?format=csv
GET /download/ext789ghi012?format=json&table_id=0
```

#### Response
Returns file download with appropriate headers:
- **CSV**: `text/csv`
- **JSON**: `application/json`
- **Excel**: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`

### 5. List Processed Files
**GET** `/files`

Get list of all processed files.

#### Query Parameters
- `limit` (optional): Number of files to return (default: 50)
- `offset` (optional): Skip number of files (default: 0)
- `status` (optional): Filter by status ("uploaded", "processing", "completed", "failed")

#### Response
```json
{
  "files": [
    {
      "file_id": "abc123def456",
      "filename": "document.pdf",
      "upload_time": "2025-06-30T10:30:00Z",
      "status": "completed",
      "tables_count": 2
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

### 6. Delete File
**DELETE** `/files/{file_id}`

Delete uploaded file and associated data.

#### Response
```json
{
  "message": "File deleted successfully",
  "file_id": "abc123def456"
}
```

## Data Models

### File Upload Response
```typescript
interface FileUploadResponse {
  file_id: string;
  filename: string;
  file_size: number;
  upload_time: string;
  status: "uploaded" | "processing" | "completed" | "failed";
}
```

### Table Data
```typescript
interface TableData {
  table_id: number;
  page: number;
  shape: [number, number];  // [rows, columns]
  headers: string[];
  data: string[][];
  confidence: number;  // 0.0 to 1.0
}
```

### Extraction Response
```typescript
interface ExtractionResponse {
  file_id: string;
  extraction_id: string;
  tables_found: number;
  tables: TableData[];
  processing_time: number;
  status: "processing" | "completed" | "failed";
}
```

## Error Handling

### HTTP Status Codes
- `200`: Success
- `201`: Created (file uploaded)
- `400`: Bad Request (invalid parameters)
- `404`: Not Found (file/extraction not found)
- `415`: Unsupported Media Type (invalid file format)
- `422`: Unprocessable Entity (file processing failed)
- `500`: Internal Server Error

### Error Response Format
```json
{
  "error": "Error message",
  "details": "Additional details about the error",
  "code": "ERROR_CODE",
  "timestamp": "2025-06-30T10:30:00Z"
}
```

## Rate Limiting
- Maximum 100 requests per minute per IP
- Maximum file size: 10MB
- Maximum 10 concurrent extractions per IP

## Examples

### Python Client Example
```python
import requests

# Upload file
with open('document.pdf', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/upload',
        files={'file': f}
    )
    file_data = response.json()

# Extract tables
extract_response = requests.post(
    'http://localhost:8000/extract',
    json={'file_id': file_data['file_id']}
)
extraction_data = extract_response.json()

# Download CSV
csv_response = requests.get(
    f'http://localhost:8000/download/{extraction_data["extraction_id"]}?format=csv'
)
with open('extracted_data.csv', 'wb') as f:
    f.write(csv_response.content)
```

### JavaScript/Fetch Example
```javascript
// Upload file
const formData = new FormData();
formData.append('file', fileInput.files[0]);

const uploadResponse = await fetch('http://localhost:8000/upload', {
    method: 'POST',
    body: formData
});
const fileData = await uploadResponse.json();

// Extract tables
const extractResponse = await fetch('http://localhost:8000/extract', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({file_id: fileData.file_id})
});
const extractionData = await extractResponse.json();
```

## WebSocket Support (Future)
Real-time processing updates will be available through WebSocket connections:
```
ws://localhost:8000/ws/extraction/{extraction_id}
```

## Changelog

### v1.0.0
- Initial API release
- Basic file upload and extraction
- CSV/JSON export support

### v1.1.0 (Planned)
- Excel export format
- WebSocket real-time updates
- Batch processing endpoints
- Advanced extraction options