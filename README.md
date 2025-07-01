# KALEIDO - A Document Workflow Tool
## 🚀 Full Stack + NLP Solution for Intelligent Document Processing

### 📋 Project Overview
KALEIDO is a comprehensive document workflow tool that processes tabular data from PDF and DOCX documents, structures it intelligently, and provides an interactive drag-and-drop workflow interface. The system combines advanced NLP table extraction with a modern web-based UI.

**Core Workflow**: Upload → Extract → Review → Export

## 🏗️ Architecture

```
┌─────────────────────┐    ┌──────────────────┐    ┌─────────────────────┐
│   Frontend          │    │   FastAPI        │    │   NLP Engine        │
│   (Workflow Canvas) │◄──►│   Backend        │◄──►│   (Table Extraction)│
│                     │    │                  │    │                     │
│ • Drag-Drop UI      │    │ • /upload        │    │ • camelot-py        │
│ • File Upload       │    │ • /extract       │    │ • pdfplumber        │
│ • Table Preview     │    │ • /download      │    │ • python-docx       │
│ • Export Controls   │    │ • /health        │    │ • pandas            │
└─────────────────────┘    └──────────────────┘    └─────────────────────┘
```

## 📁 Project Structure
```
KALEIDO/
├── backend/
│   ├── __pycache__/                  # Python cache files
│   ├── app.py                        # FastAPI application (main backend)
│   └── extractor.py                  # Table extraction logic (PDF/DOCX)
├── docs/
│   ├── api_docs.md                   # API usage documentation
│   ├── deployment.md                 # Deployment instructions
│   ├── flow_diagram.svg              # Workflow diagram
│   └── test_run.gif                  # Demo run capture
├── frontend/
│   ├── mockup.png                    # Visual mockup of canvas UI
│   └── workflow_canvas.html          # Interactive drag-and-drop UI
├── sample docs/
│   ├── sample-invoice.pdf            # PDF sample with tables
│   └── school-timetable-template.docx # DOCX sample with tables
├── sample run/
│   ├── extracted_tables.csv          # CSV output sample
│   ├── extracted_tables.json         # JSON output sample
│   ├── screenshot 1.png              # Screenshot of workflow in action
│   ├── screenshot 2.png
│   ├── screenshot 3.png
│   └── screenshot 4.png
├── streamlit_app/
│   ├── __pycache__/                  # Python cache files
│   ├── app.py                        # Main Streamlit UI entry
│   ├── helpers.py                    # Utility/helper functions
│   └── pages/                        # Multi-page Streamlit structure
│       ├── 1_Extract.py              # Extract tables
│       ├── 2_Edit.py                 # Inline table editing
│       ├── 3_Export.py               # Export section
│       └── 4_Workflow.py             # Visual workflow
├── tests/
│   ├── test_api.py                   # Unit tests for backend API
│   └── test_extractor.py            # Unit tests for table extraction logic
├── kaleido.zip                       # Submission zip archive
├── README.md                         # Project overview and documentation
└── requirements.txt                  # Python dependencies

```

## 🛠️ Technology Stack

### Backend (FastAPI)
- **Framework**: FastAPI with async support
- **NLP Libraries**: camelot-py, pdfplumber, python-docx
- **Data Processing**: pandas, numpy
- **File Handling**: tempfile, pathlib

### Frontend (Interactive Canvas)
- **UI Framework**: Vanilla HTML5/CSS3/JavaScript
- **Design**: Modern gradient-based UI with drag-drop functionality
- **Notifications**: Real-time status updates
- **Responsive**: Mobile-friendly design

### Streamlit App (Optional UI)
- **Framework**: Streamlit for rapid prototyping
- **Components**: Multi-page app structure
- **Integration**: Connects to FastAPI backend

## 🚀 Quick Start

### 1. Install Dependencies
```bash
# Clone the repository
git clone <your-repo-url>
cd KALEIDO

# Install required packages
pip install -r requirements.txt
```

### 2. Start the Backend Server
```bash
# Navigate to backend directory
cd backend

# Start FastAPI server
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### 3. Launch the Frontend
```bash
# Option 1: Open HTML file directly
open frontend/workflow_canvas.html

# Option 2: Use Streamlit interface
cd streamlit_app
streamlit run app.py
```

### 4. Access the Application
- **Workflow Canvas**: `frontend/workflow_canvas.html` (primary interface)
- **API Documentation**: http://localhost:8000/docs
- **Streamlit UI**: http://localhost:8501 (if using Streamlit)

## 📊 API Endpoints

| Method | Endpoint | Description | Request Body |
|--------|----------|-------------|--------------|
| GET | `/` | Health check and API info | None |
| GET | `/health` | Health status | None |
| POST | `/upload` | Upload PDF/DOCX files | `multipart/form-data` |
| POST | `/extract` | Extract tables from uploaded file | `{"file_id": "uuid"}` |
| POST | `/download` | Download processed data | `{"extraction_id": "uuid", "format": "csv/json"}` |
| GET | `/extractions` | List all cached extractions | None |
| DELETE | `/cleanup` | Clean temporary files | None |

## 🔍 NLP Table Extraction Features

### Multi-Strategy Extraction
1. **PDF Processing**:
   - Primary: camelot-py (lattice-based detection)
   - Fallback: pdfplumber (text-based extraction)
   - Handles complex layouts and merged cells

2. **DOCX Processing**:
   - python-docx for native table parsing
   - Preserves formatting and structure
   - Handles nested tables and complex layouts

### Data Processing Pipeline
```python
# Example extraction workflow
file_upload → format_detection → extraction_strategy → 
data_cleaning → structure_validation → export_preparation
```

## 🎨 Workflow Canvas Features

### Interactive Nodes
- **Input Node**: File upload with format validation
- **Extract Node**: AI-powered table detection
- **Review Node**: Data validation and editing
- **Export Node**: Multi-format download options

### Drag-and-Drop Functionality
- Rearrange workflow nodes
- Visual connections between steps
- Real-time status indicators
- Responsive design for mobile devices

### Visual Feedback
- Animated node interactions
- Progress notifications
- Error handling with user-friendly messages
- Success confirmations

## 🧪 Testing

### Run Test Suite
```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_extractor.py -v

# Run with coverage report
python -m pytest tests/ --cov=backend --cov-report=html
```

### Test Coverage
- API endpoint testing
- Table extraction accuracy
- File format validation
- Error handling scenarios

## 📈 Usage Workflow

### 1. Document Upload
- Drag and drop or select files
- Support for PDF and DOCX formats
- File size validation and format checking

### 2. Table Extraction
- Automatic table detection
- Multiple extraction strategies
- Preview of extracted data

### 3. Data Review
- Interactive table preview
- Row/column validation
- Data type inference

### 4. Export Options
- CSV format for spreadsheet integration
- JSON format for programmatic use
- Batch download of multiple tables

## 🔧 Configuration

### Environment Variables
```bash
# Backend Configuration
BACKEND_HOST=localhost
BACKEND_PORT=8000
MAX_FILE_SIZE=10MB
TEMP_DIR=./temp

# Frontend Configuration
API_BASE_URL=http://localhost:8000
UPLOAD_TIMEOUT=30000
```

### Supported File Formats
- **PDF**: Native and scanned documents
- **DOCX**: Microsoft Word documents
- **DOC**: Legacy Word format (limited support)

## 🚢 Deployment

### Local Development
```bash
# Start backend
cd backend && uvicorn app:app --reload

# Serve frontend
cd frontend && python -m http.server 8080
```

### Production Deployment
See `docs/deployment.md` for detailed production setup instructions.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit changes: `git commit -am 'Add feature'`
4. Push to branch: `git push origin feature-name`
5. Submit a Pull Request

## 📄 License

This project is licensed under the MIT License.

## 🔍 Troubleshooting

### Common Issues

1. **"Cannot connect to API"**
   - Ensure backend server is running on port 8000
   - Check if `uvicorn app:app --reload` is running

2. **"File upload failed"**
   - Verify file format (PDF/DOCX only)
   - Check file size limits
   - Ensure proper file permissions

3. **"No tables found"**
   - Verify document contains structured tables
   - Try different extraction strategies
   - Check document quality and layout

### Performance Tips
- Use high-quality PDF documents for best results
- Ensure tables have clear borders and structure
- Consider file compression for large documents
- Monitor memory usage for batch processing

## 📞 Support

For issues and questions:
- Create an issue on GitHub
- Check API documentation at `/docs`
- Review test files for usage examples

---

### 🏆 Project Highlights

- **Modern UI**: Gradient-based design with smooth animations
- **Robust NLP**: Multi-strategy table extraction with fallback options
- **RESTful API**: Well-documented FastAPI backend
- **Responsive Design**: Works on desktop and mobile devices
- **Error Handling**: Comprehensive error management and user feedback
- **Testing**: Unit tests for critical components
- **Documentation**: Detailed setup and usage instructions

Built with ❤️ for intelligent document processing.