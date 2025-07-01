# streamlit_app/pages/1_Extract.py
import streamlit as st
import sys
import os

# Add parent directory to path to import helpers
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from helpers import (
    upload_file_to_backend, 
    extract_tables_from_backend,
    display_table_preview,
    validate_backend_connection,
    format_file_size,
    save_to_session_state,
    get_from_session_state,
    update_workflow_status,
    display_workflow_progress
)

def main():
    st.set_page_config(
        page_title="Extract Tables", 
        page_icon="📊", 
        layout="wide"
    )
    
    st.title("📊 Extract Tables from Documents")
    st.markdown("Upload your PDF or Word document to extract tabular data.")
    
    # Display workflow progress
    display_workflow_progress()
    
    # Check backend connection
    if not validate_backend_connection():
        st.error("⚠️ Backend server is not running. Please start the FastAPI server on port 8000.")
        st.code("cd backend && uvicorn app:app --reload --port 8000")
        return
    
    # File upload section
    st.header("1. Upload Document")
    
    uploaded_file = st.file_uploader(
        "Choose a file",
        type=['pdf', 'docx'],
        help="Upload PDF or Word documents containing tables"
    )
    
    if uploaded_file is not None:
        # Display file info
        file_details = {
            "Filename": uploaded_file.name,
            "File size": format_file_size(uploaded_file.size),
            "File type": uploaded_file.type
        }
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.json(file_details)
        
        with col2:
            if st.button("🚀 Upload & Process", type="primary"):
                with st.spinner("Uploading file..."):
                    upload_response = upload_file_to_backend(uploaded_file)
                    
                    if upload_response:
                        st.success("✅ File uploaded successfully!")
                        save_to_session_state('upload_response', upload_response)
                        save_to_session_state('uploaded_filename', uploaded_file.name)
                        update_workflow_status('upload', 'completed')
                        st.rerun()
    
    # Table extraction section
    upload_response = get_from_session_state('upload_response')
    
    if upload_response:
        st.header("2. Extract Tables")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.success(f"✅ File uploaded: {get_from_session_state('uploaded_filename')}")
        
        with col2:
            if st.button("🔍 Extract Tables", type="primary"):
                update_workflow_status('extract', 'in_progress')
                
                with st.spinner("Extracting tables... This may take a moment."):
                    file_path = upload_response.get('file_path')
                    extraction_response = extract_tables_from_backend(file_path)
                    
                    if extraction_response:
                        save_to_session_state('extraction_response', extraction_response)
                        update_workflow_status('extract', 'completed')
                        st.success("✅ Tables extracted successfully!")
                        st.rerun()
    
    # Display extracted tables
    extraction_response = get_from_session_state('extraction_response')
    
    if extraction_response:
        st.header("3. Preview Extracted Tables")
        
        # Display extraction summary
        if 'message' in extraction_response:
            st.info(extraction_response['message'])
        
        # Display tables
        selected_tables = display_table_preview(extraction_response)
        
        if selected_tables:
            save_to_session_state('selected_tables', selected_tables)
            update_workflow_status('review', 'completed')
            
            # Action buttons
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col1:
                if st.button("📝 Edit Tables", type="secondary"):
                    st.switch_page("pages/2_Edit.py")
            
            with col2:
                if st.button("💾 Export Data", type="secondary"):
                    st.switch_page("pages/3_Export.py")
            
            with col3:
                if st.button("🔄 View Workflow", type="secondary"):
                    st.switch_page("pages/4_Workflow.py")
        
        # Advanced options
        with st.expander("🔧 Advanced Options"):
            st.subheader("Extraction Settings")
            
            col1, col2 = st.columns(2)
            
            with col1:
                lattice_mode = st.checkbox(
                    "Use Lattice Mode", 
                    value=True,
                    help="Better for tables with clear borders"
                )
                
                skip_empty = st.checkbox(
                    "Skip Empty Rows",
                    value=True,
                    help="Remove rows with all empty cells"
                )
            
            with col2:
                pages = st.text_input(
                    "Pages to Process",
                    placeholder="e.g., 1,2,3 or all",
                    help="Specify which pages to extract tables from"
                )
                
                table_areas = st.text_input(
                    "Table Areas",
                    placeholder="x1,y1,x2,y2",
                    help="Specify coordinates for table areas (optional)"
                )
            
            if st.button("🔄 Re-extract with Settings"):
                st.info("Re-extraction with custom settings will be implemented in the next update.")
    
    # Help section
    with st.expander("ℹ️ Need Help?"):
        st.markdown("""
        ### Supported File Types
        - **PDF**: Documents with tabular data
        - **Word (DOCX)**: Documents containing tables
        
        ### Tips for Better Extraction
        - Ensure tables have clear borders and structure
        - Avoid scanned documents (OCR support coming soon)
        - Check that table headers are clearly defined
        
        ### Troubleshooting
        - If extraction fails, try with a different file
        - Ensure the backend server is running
        - Check file permissions and size limits
        """)

if __name__ == "__main__":
    main()