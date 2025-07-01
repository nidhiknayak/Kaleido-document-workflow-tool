# streamlit_app/helpers.py
import streamlit as st
import requests
import pandas as pd
import json
from io import BytesIO
import base64

# Backend API configuration
BACKEND_URL = "http://localhost:8000"  # Adjust based on your FastAPI server

def upload_file_to_backend(uploaded_file):
    """Upload file to FastAPI backend and return response"""
    try:
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
        response = requests.post(f"{BACKEND_URL}/upload", files=files)
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Upload failed: {response.text}")
            return None
    except requests.exceptions.ConnectionError:
        st.error("Could not connect to backend server. Make sure FastAPI is running on port 8000.")
        return None
    except Exception as e:
        st.error(f"Upload error: {str(e)}")
        return None

def extract_tables_from_backend(file_path):
    """Extract tables from uploaded file via backend API"""
    try:
        data = {"file_path": file_path}
        response = requests.post(f"{BACKEND_URL}/extract", json=data)
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Extraction failed: {response.text}")
            return None
    except Exception as e:
        st.error(f"Extraction error: {str(e)}")
        return None

def download_file_from_backend(file_path, format_type="csv"):
    """Download processed file from backend"""
    try:
        params = {"file_path": file_path, "format": format_type}
        response = requests.get(f"{BACKEND_URL}/download", params=params)
        
        if response.status_code == 200:
            return response.content
        else:
            st.error(f"Download failed: {response.text}")
            return None
    except Exception as e:
        st.error(f"Download error: {str(e)}")
        return None

def create_download_link(data, filename, file_format="csv"):
    """Create a download link for processed data"""
    if file_format == "csv":
        if isinstance(data, pd.DataFrame):
            csv = data.to_csv(index=False)
            b64 = base64.b64encode(csv.encode()).decode()
        else:
            b64 = base64.b64encode(data).decode()
        href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">Download {filename}</a>'
    elif file_format == "json":
        if isinstance(data, pd.DataFrame):
            json_str = data.to_json(orient='records', indent=2)
        else:
            json_str = json.dumps(data, indent=2)
        b64 = base64.b64encode(json_str.encode()).decode()
        href = f'<a href="data:file/json;base64,{b64}" download="{filename}">Download {filename}</a>'
    
    return href

def display_table_preview(tables_data, max_rows=10):
    """Display a preview of extracted tables"""
    if not tables_data or 'tables' not in tables_data:
        st.warning("No tables found in the document.")
        return None
    
    tables = tables_data['tables']
    
    if len(tables) == 0:
        st.warning("No tables extracted from the document.")
        return None
    
    # Display summary
    st.info(f"Found {len(tables)} table(s) in the document")
    
    selected_tables = []
    
    for i, table in enumerate(tables):
        st.subheader(f"Table {i+1}")
        
        # Convert to DataFrame if it's a list of lists
        if isinstance(table, list):
            df = pd.DataFrame(table[1:], columns=table[0] if table else [])
        else:
            df = pd.DataFrame(table)
        
        # Display preview
        if len(df) > max_rows:
            st.write(f"Showing first {max_rows} rows of {len(df)} total rows:")
            st.dataframe(df.head(max_rows))
        else:
            st.dataframe(df)
        
        # Add selection checkbox
        if st.checkbox(f"Include Table {i+1} in export", value=True, key=f"table_{i}"):
            selected_tables.append(df)
        
        st.divider()
    
    return selected_tables

def validate_backend_connection():
    """Check if backend is running and accessible"""
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def format_file_size(size_bytes):
    """Convert bytes to human readable format"""
    if size_bytes == 0:
        return "0B"
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    return f"{size_bytes:.1f}{size_names[i]}"

def save_to_session_state(key, value):
    """Save data to Streamlit session state"""
    st.session_state[key] = value

def get_from_session_state(key, default=None):
    """Get data from Streamlit session state"""
    return st.session_state.get(key, default)

def clear_session_state():
    """Clear all session state data"""
    for key in list(st.session_state.keys()):
        del st.session_state[key]

# Workflow status tracking
def update_workflow_status(step, status="completed"):
    """Update workflow step status"""
    if 'workflow_status' not in st.session_state:
        st.session_state.workflow_status = {}
    st.session_state.workflow_status[step] = status

def get_workflow_status():
    """Get current workflow status"""
    return st.session_state.get('workflow_status', {})

def display_workflow_progress():
    """Display current workflow progress"""
    status = get_workflow_status()
    steps = ["upload", "extract", "review", "export"]
    
    cols = st.columns(len(steps))
    
    for i, step in enumerate(steps):
        with cols[i]:
            if status.get(step) == "completed":
                st.success(f"✅ {step.title()}")
            elif status.get(step) == "in_progress":
                st.warning(f"⏳ {step.title()}")
            else:
                st.info(f"⭕ {step.title()}")