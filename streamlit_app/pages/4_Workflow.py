import streamlit as st
import streamlit.components.v1 as components
import requests
import json
import os
from pathlib import Path

# Page configuration
st.set_page_config(
    page_title="Workflow Canvas",
    page_icon="🔄",
    layout="wide"
)

st.title("🔄 Document Processing Workflow")
st.markdown("---")

# Initialize session state for workflow data
if 'workflow_state' not in st.session_state:
    st.session_state.workflow_state = {
        'uploaded_file': None,
        'extraction_result': None,
        'edited_data': None,
        'export_format': 'csv'
    }

# Create two columns for layout
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Interactive Workflow Canvas")
    
    # Read the workflow canvas HTML file
    workflow_html_path = Path("frontend/workflow_canvas.html")
    
    if workflow_html_path.exists():
        with open(workflow_html_path, 'r', encoding='utf-8') as file:
            workflow_html = file.read()
        
        # Inject Streamlit integration JavaScript
        integration_js = """
        <script>
        // Streamlit integration functions
        window.streamlitWorkflow = {
            updateStatus: function(nodeId, status, data) {
                // Send status updates back to Streamlit
                window.parent.postMessage({
                    type: 'workflow_update',
                    nodeId: nodeId,
                    status: status,
                    data: data
                }, '*');
            },
            
            triggerFileUpload: function() {
                window.parent.postMessage({
                    type: 'trigger_upload'
                }, '*');
            },
            
            triggerExtraction: function() {
                window.parent.postMessage({
                    type: 'trigger_extraction'
                }, '*');
            },
            
            triggerExport: function() {
                window.parent.postMessage({
                    type: 'trigger_export'
                }, '*');
            }
        };

        // Listen for workflow events
        document.addEventListener('DOMContentLoaded', function() {
            // Update nodes based on current workflow state
            const workflowState = JSON.parse('""" + json.dumps(st.session_state.workflow_state).replace("'", "\\'") + """');
            
            // Update node statuses based on current state
            if (workflowState.uploaded_file) {
                updateNodeStatus('input-node', 'completed');
            }
            if (workflowState.extraction_result) {
                updateNodeStatus('process-node', 'completed');
            }
            if (workflowState.edited_data) {
                updateNodeStatus('review-node', 'completed');
            }
        });
        </script>
        """
        
        # Inject the integration script into the HTML
        workflow_html = workflow_html.replace('</body>', integration_js + '</body>')
        
        # Display the workflow canvas
        components.html(workflow_html, height=600, scrolling=True)
    else:
        st.error("Workflow canvas HTML file not found. Please ensure 'frontend/workflow_canvas.html' exists.")
        
        # Fallback: Simple workflow representation
        st.info("**Workflow Steps:**")
        
        # Create a simple visual workflow using Streamlit columns
        step_cols = st.columns(4)
        
        with step_cols[0]:
            upload_status = "✅" if st.session_state.workflow_state['uploaded_file'] else "⏳"
            st.metric("1. Upload", upload_status)
            
        with step_cols[1]:
            extract_status = "✅" if st.session_state.workflow_state['extraction_result'] else "⏳"
            st.metric("2. Extract", extract_status)
            
        with step_cols[2]:
            review_status = "✅" if st.session_state.workflow_state['edited_data'] else "⏳"
            st.metric("3. Review", review_status)
            
        with step_cols[3]:
            export_status = "✅" if all([
                st.session_state.workflow_state['uploaded_file'],
                st.session_state.workflow_state['extraction_result']
            ]) else "⏳"
            st.metric("4. Export", export_status)

with col2:
    st.subheader("Workflow Controls")
    
    # File Upload Section
    st.markdown("#### 📁 Step 1: Upload Document")
    uploaded_file = st.file_uploader(
        "Choose a PDF or DOCX file",
        type=['pdf', 'docx'],
        key="workflow_upload"
    )
    
    if uploaded_file:
        st.session_state.workflow_state['uploaded_file'] = uploaded_file
        st.success(f"✅ File uploaded: {uploaded_file.name}")
    
    # Extraction Section
    st.markdown("#### ⚙️ Step 2: Extract Tables")
    if st.button("🔍 Run Extraction", disabled=not uploaded_file):
        if uploaded_file:
            with st.spinner("Extracting tables..."):
                try:
                    # Send file to backend for processing
                    files = {"file": uploaded_file.getvalue()}
                    response = requests.post("http://localhost:8000/extract", files=files)
                    
                    if response.status_code == 200:
                        extraction_result = response.json()
                        st.session_state.workflow_state['extraction_result'] = extraction_result
                        st.success("✅ Extraction completed!")
                        
                        # Show preview of extracted data
                        if extraction_result.get('tables'):
                            st.json(extraction_result['tables'][0][:3])  # Show first 3 rows
                    else:
                        st.error(f"Extraction failed: {response.text}")
                        
                except requests.exceptions.ConnectionError:
                    st.error("❌ Backend server not running. Please start the FastAPI server.")
                except Exception as e:
                    st.error(f"❌ Error during extraction: {str(e)}")
    
    # Review Section  
    st.markdown("#### 📝 Step 3: Review Data")
    if st.session_state.workflow_state.get('extraction_result'):
        if st.button("📊 Open Data Editor"):
            st.switch_page("pages/2_Edit.py")
    else:
        st.info("Complete extraction first")
    
    # Export Section
    st.markdown("#### 📤 Step 4: Export Results")
    export_format = st.selectbox(
        "Choose export format:",
        ["csv", "json", "excel"],
        key="export_format_select"
    )
    st.session_state.workflow_state['export_format'] = export_format
    
    if st.button("💾 Download Results", disabled=not st.session_state.workflow_state.get('extraction_result')):
        if st.session_state.workflow_state.get('extraction_result'):
            try:
                # Request download from backend
                download_response = requests.get(
                    f"http://localhost:8000/download?format={export_format}",
                    params={"session_id": "current"}  # In real app, use actual session ID
                )
                
                if download_response.status_code == 200:
                    # Trigger download
                    st.download_button(
                        label=f"📥 Download {export_format.upper()}",
                        data=download_response.content,
                        file_name=f"extracted_data.{export_format}",
                        mime=f"text/{export_format}" if export_format == "csv" else "application/json"
                    )
                else:
                    st.error("Download failed")
                    
            except requests.exceptions.ConnectionError:
                st.error("❌ Backend server not running")
            except Exception as e:
                st.error(f"❌ Download error: {str(e)}")

# Workflow Status Panel
st.markdown("---")
st.subheader("📊 Workflow Status")

status_cols = st.columns(4)

with status_cols[0]:
    if st.session_state.workflow_state['uploaded_file']:
        st.success("📁 File Ready")
    else:
        st.warning("📁 No File")

with status_cols[1]:
    if st.session_state.workflow_state.get('extraction_result'):
        tables_count = len(st.session_state.workflow_state['extraction_result'].get('tables', []))
        st.success(f"⚙️ {tables_count} Tables Extracted")
    else:
        st.warning("⚙️ Not Extracted")

with status_cols[2]:
    if st.session_state.workflow_state.get('edited_data'):
        st.success("📝 Data Reviewed")
    else:
        st.info("📝 Ready to Review")

with status_cols[3]:
    if all([
        st.session_state.workflow_state.get('uploaded_file'),
        st.session_state.workflow_state.get('extraction_result')
    ]):
        st.success("📤 Ready to Export")
    else:
        st.warning("📤 Not Ready")

# Debug information (optional - remove in production)
if st.checkbox("🐛 Show Debug Info"):
    st.json(st.session_state.workflow_state)

# Instructions
st.markdown("---")
st.markdown("""
### 📋 How to Use This Workflow

1. **Upload**: Choose a PDF or DOCX file containing tables
2. **Extract**: Click 'Run Extraction' to process the document
3. **Review**: Use the Data Editor to verify and modify extracted data
4. **Export**: Download the results in your preferred format

**Note**: Make sure the FastAPI backend server is running on `http://localhost:8000`
""")

# Quick Actions
st.markdown("### 🚀 Quick Actions")
quick_cols = st.columns(3)

with quick_cols[0]:
    if st.button("🔄 Reset Workflow"):
        st.session_state.workflow_state = {
            'uploaded_file': None,
            'extraction_result': None,
            'edited_data': None,
            'export_format': 'csv'
        }
        st.success("Workflow reset!")
        st.rerun()

with quick_cols[1]:
    if st.button("📊 View All Pages"):
        st.info("Available pages: Extract → Edit → Export → Workflow")

with quick_cols[2]:
    if st.button("ℹ️ API Status"):
        try:
            response = requests.get("http://localhost:8000/", timeout=2)
            if response.status_code == 200:
                st.success("✅ Backend Online")
            else:
                st.error("❌ Backend Error")
        except:
            st.error("❌ Backend Offline")