import streamlit as st
import pandas as pd
import requests
import json
import io
from typing import Dict, List, Any, Optional
from pathlib import Path
import tempfile
import os

# Configuration
BACKEND_URL = "http://localhost:8000"

class WorkflowState:
    """Manages workflow state across Streamlit pages"""
    
    @staticmethod
    def initialize():
        """Initialize workflow state if not exists"""
        if 'workflow_state' not in st.session_state:
            st.session_state.workflow_state = {
                'uploaded_file': None,
                'file_info': None,
                'extraction_result': None,
                'edited_data': None,
                'export_format': 'csv',
                'current_step': 'upload',
                'errors': [],
                'processing_logs': []
            }
    
    @staticmethod
    def get_state() -> Dict[str, Any]:
        """Get current workflow state"""
        WorkflowState.initialize()
        return st.session_state.workflow_state
    
    @staticmethod
    def update_state(key: str, value: Any):
        """Update specific workflow state"""
        WorkflowState.initialize()
        st.session_state.workflow_state[key] = value
    
    @staticmethod
    def add_log(message: str, log_type: str = "info"):
        """Add processing log"""
        WorkflowState.initialize()
        log_entry = {
            'message': message,
            'type': log_type,
            'timestamp': pd.Timestamp.now().isoformat()
        }
        st.session_state.workflow_state['processing_logs'].append(log_entry)
    
    @staticmethod
    def clear_errors():
        """Clear error list"""
        WorkflowState.initialize()
        st.session_state.workflow_state['errors'] = []
    
    @staticmethod
    def add_error(error: str):
        """Add error to state"""
        WorkflowState.initialize()
        st.session_state.workflow_state['errors'].append(error)
    
    @staticmethod
    def reset():
        """Reset entire workflow state"""
        st.session_state.workflow_state = {
            'uploaded_file': None,
            'file_info': None,
            'extraction_result': None,
            'edited_data': None,
            'export_format': 'csv',
            'current_step': 'upload',
            'errors': [],
            'processing_logs': []
        }

class BackendAPI:
    """Handles communication with FastAPI backend"""
    
    @staticmethod
    def is_backend_running() -> bool:
        """Check if backend server is running"""
        try:
            response = requests.get(f"{BACKEND_URL}/", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    @staticmethod
    def upload_file(file_data: bytes, filename: str) -> Dict[str, Any]:
        """Upload file to backend"""
        try:
            files = {"file": (filename, file_data)}
            response = requests.post(f"{BACKEND_URL}/upload", files=files, timeout=30)
            
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                return {"success": False, "error": f"Upload failed: {response.text}"}
                
        except requests.exceptions.ConnectionError:
            return {"success": False, "error": "Backend server not running"}
        except Exception as e:
            return {"success": False, "error": f"Upload error: {str(e)}"}
    
    @staticmethod
    def extract_tables(file_data: bytes, filename: str) -> Dict[str, Any]:
        """Extract tables from uploaded file"""
        try:
            files = {"file": (filename, file_data)}
            response = requests.post(f"{BACKEND_URL}/extract", files=files, timeout=60)
            
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                return {"success": False, "error": f"Extraction failed: {response.text}"}
                
        except requests.exceptions.ConnectionError:
            return {"success": False, "error": "Backend server not running"}
        except Exception as e:
            return {"success": False, "error": f"Extraction error: {str(e)}"}
    
    @staticmethod
    def download_data(format_type: str = "csv", session_id: str = "current") -> Dict[str, Any]:
        """Download processed data from backend"""
        try:
            params = {"format": format_type, "session_id": session_id}
            response = requests.get(f"{BACKEND_URL}/download", params=params, timeout=30)
            
            if response.status_code == 200:
                return {"success": True, "data": response.content, "headers": response.headers}
            else:
                return {"success": False, "error": f"Download failed: {response.text}"}
                
        except requests.exceptions.ConnectionError:
            return {"success": False, "error": "Backend server not running"}
        except Exception as e:
            return {"success": False, "error": f"Download error: {str(e)}"}

class DataProcessor:
    """Handles data processing and manipulation"""
    
    @staticmethod
    def tables_to_dataframes(tables_data: List[Dict]) -> List[pd.DataFrame]:
        """Convert table data to pandas DataFrames"""
        dataframes = []
        for table in tables_data:
            try:
                if isinstance(table, list) and len(table) > 0:
                    # Handle list of rows
                    df = pd.DataFrame(table)
                elif isinstance(table, dict):
                    # Handle dictionary format
                    df = pd.DataFrame(table)
                else:
                    continue
                
                dataframes.append(df)
            except Exception as e:
                st.warning(f"Could not convert table to DataFrame: {str(e)}")
                continue
        
        return dataframes
    
    @staticmethod
    def dataframes_to_export_format(dataframes: List[pd.DataFrame], format_type: str) -> bytes:
        """Convert DataFrames to export format"""
        if not dataframes:
            raise ValueError("No data to export")
        
        if format_type == "csv":
            if len(dataframes) == 1:
                return dataframes[0].to_csv(index=False).encode('utf-8')
            else:
                # Combine multiple tables
                combined_df = pd.concat(dataframes, ignore_index=True)
                return combined_df.to_csv(index=False).encode('utf-8')
        
        elif format_type == "json":
            if len(dataframes) == 1:
                return dataframes[0].to_json(orient='records', indent=2).encode('utf-8')
            else:
                # Export as list of tables
                tables_json = [df.to_dict('records') for df in dataframes]
                return json.dumps(tables_json, indent=2).encode('utf-8')
        
        elif format_type == "excel":
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                for i, df in enumerate(dataframes):
                    sheet_name = f"Table_{i+1}"
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
            return output.getvalue()
        
        else:
            raise ValueError(f"Unsupported format: {format_type}")

class UIHelpers:
    """UI helper functions for Streamlit components"""
    
    @staticmethod
    def show_workflow_progress():
        """Display workflow progress bar"""
        state = WorkflowState.get_state()
        
        progress_steps = [
            ("Upload", state.get('uploaded_file') is not None),
            ("Extract", state.get('extraction_result') is not None),
            ("Review", state.get('edited_data') is not None),
            ("Export", state.get('extraction_result') is not None)
        ]
        
        completed_steps = sum(1 for _, completed in progress_steps if completed)
        progress_percentage = completed_steps / len(progress_steps)
        
        st.progress(progress_percentage)
        
        # Show step status
        cols = st.columns(len(progress_steps))
        for i, (step_name, completed) in enumerate(progress_steps):
            with cols[i]:
                icon = "✅" if completed else "⏳"
                st.metric(f"{i+1}. {step_name}", icon)
    
    @staticmethod
    def show_backend_status():
        """Display backend server status"""
        if BackendAPI.is_backend_running():
            st.success("🟢 Backend server is running")
        else:
            st.error("🔴 Backend server is not running. Please start the FastAPI server.")
            st.code("cd backend && uvicorn app:app --reload", language="bash")
    
    @staticmethod
    def show_file_info(file_info: Dict[str, Any]):
        """Display uploaded file information"""
        if file_info:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("File Name", file_info.get('name', 'Unknown'))
            with col2:
                size_mb = file_info.get('size', 0) / (1024 * 1024)
                st.metric("File Size", f"{size_mb:.2f} MB")
            with col3:
                st.metric("File Type", file_info.get('type', 'Unknown'))
    
    @staticmethod
    def show_extraction_summary(extraction_result: Dict[str, Any]):
        """Display extraction results summary"""
        if extraction_result and 'tables' in extraction_result:
            tables = extraction_result['tables']
            
            st.subheader("📊 Extraction Summary")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Tables Found", len(tables))
            with col2:
                total_rows = sum(len(table) for table in tables if isinstance(table, list))
                st.metric("Total Rows", total_rows)
            
            # Show table previews
            for i, table in enumerate(tables[:3]):  # Show first 3 tables
                with st.expander(f"Table {i+1} Preview"):
                    if isinstance(table, list) and len(table) > 0:
                        df = pd.DataFrame(table)
                        st.dataframe(df.head(), use_container_width=True)
                    else:
                        st.write("No data or invalid format")
    
    @staticmethod
    def show_processing_logs():
        """Display processing logs"""
        state = WorkflowState.get_state()
        logs = state.get('processing_logs', [])
        
        if logs:
            with st.expander("📝 Processing Logs"):
                for log in logs[-10:]:  # Show last 10 logs
                    timestamp = log.get('timestamp', '')
                    message = log.get('message', '')
                    log_type = log.get('type', 'info')
                    
                    if log_type == "error":
                        st.error(f"{timestamp}: {message}")
                    elif log_type == "warning":
                        st.warning(f"{timestamp}: {message}")
                    else:
                        st.info(f"{timestamp}: {message}")
    
    @staticmethod
    def show_errors():
        """Display current errors"""
        state = WorkflowState.get_state()
        errors = state.get('errors', [])
        
        if errors:
            st.error("❌ **Current Errors:**")
            for error in errors:
                st.error(f"• {error}")
            
            if st.button("Clear Errors"):
                WorkflowState.clear_errors()
                st.rerun()

class FileValidator:
    """File validation utilities"""
    
    SUPPORTED_EXTENSIONS = ['.pdf', '.docx', '.doc']
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
    
    @staticmethod
    def validate_file(uploaded_file) -> Dict[str, Any]:
        """Validate uploaded file"""
        if uploaded_file is None:
            return {"valid": False, "error": "No file uploaded"}
        
        # Check file extension
        file_extension = Path(uploaded_file.name).suffix.lower()
        if file_extension not in FileValidator.SUPPORTED_EXTENSIONS:
            return {
                "valid": False, 
                "error": f"Unsupported file type. Supported: {', '.join(FileValidator.SUPPORTED_EXTENSIONS)}"
            }
        
        # Check file size
        if uploaded_file.size > FileValidator.MAX_FILE_SIZE:
            return {
                "valid": False,
                "error": f"File too large. Maximum size: {FileValidator.MAX_FILE_SIZE / (1024*1024):.1f} MB"
            }
        
        return {
            "valid": True,
            "info": {
                "name": uploaded_file.name,
                "size": uploaded_file.size,
                "type": uploaded_file.type,
                "extension": file_extension
            }
        }

# Utility functions for common operations
def safe_api_call(func, *args, **kwargs):
    """Safely execute API call with error handling"""
    try:
        result = func(*args, **kwargs)
        if result.get('success'):
            WorkflowState.add_log(f"API call successful: {func.__name__}", "info")
            return result
        else:
            error_msg = result.get('error', 'Unknown error')
            WorkflowState.add_log(f"API call failed: {error_msg}", "error")
            WorkflowState.add_error(error_msg)
            return result
    except Exception as e:
        error_msg = f"Exception in {func.__name__}: {str(e)}"
        WorkflowState.add_log(error_msg, "error")
        WorkflowState.add_error(error_msg)
        return {"success": False, "error": error_msg}

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024**2:
        return f"{size_bytes/1024:.1f} KB"
    elif size_bytes < 1024**3:
        return f"{size_bytes/(1024**2):.1f} MB"
    else:
        return f"{size_bytes/(1024**3):.1f} GB"