# streamlit_app/pages/3_Export.py
import streamlit as st
import pandas as pd
import json
import sys
import os
from datetime import datetime
import zipfile
from io import BytesIO

# Add parent directory to path to import helpers
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from helpers import (
    get_from_session_state,
    save_to_session_state,
    update_workflow_status,
    display_workflow_progress,
    create_download_link
)

def create_export_summary(tables):
    """Create a summary of the exported data"""
    summary = {
        "export_timestamp": datetime.now().isoformat(),
        "total_tables": len(tables),
        "table_details": []
    }
    
    for i, table in enumerate(tables):
        table_info = {
            "table_number": i + 1,
            "rows": len(table),
            "columns": len(table.columns),
            "column_names": list(table.columns)
        }
        summary["table_details"].append(table_info)
    
    return summary

def create_combined_excel(tables):
    """Create an Excel file with multiple sheets"""
    output = BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        for i, table in enumerate(tables):
            sheet_name = f"Table_{i+1}"
            table.to_excel(writer, sheet_name=sheet_name, index=False)
    
    output.seek(0)
    return output.getvalue()

def create_zip_download(tables, format_type="csv"):
    """Create a ZIP file containing all tables"""
    zip_buffer = BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Add summary file
        summary = create_export_summary(tables)
        zip_file.writestr("export_summary.json", json.dumps(summary, indent=2))
        
        # Add individual table files
        for i, table in enumerate(tables):
            if format_type == "csv":
                csv_data = table.to_csv(index=False)
                zip_file.writestr(f"table_{i+1}.csv", csv_data)
            elif format_type == "json":
                json_data = table.to_json(orient='records', indent=2)
                zip_file.writestr(f"table_{i+1}.json", json_data)
            elif format_type == "excel":
                excel_buffer = BytesIO()
                table.to_excel(excel_buffer, index=False, engine='openpyxl')
                zip_file.writestr(f"table_{i+1}.xlsx", excel_buffer.getvalue())
    
    zip_buffer.seek(0)
    return zip_buffer.getvalue()

def main():
    st.set_page_config(
        page_title="Export Data", 
        page_icon="💾", 
        layout="wide"
    )
    
    st.title("💾 Export Processed Tables")
    st.markdown("Download your processed tables in various formats.")
    
    # Display workflow progress
    display_workflow_progress()
    
    # Check if tables are available
    selected_tables = get_from_session_state('selected_tables')
    
    if not selected_tables:
        st.warning("⚠️ No tables found. Please process a document first.")
        if st.button("🔙 Go to Extract Page"):
            st.switch_page("pages/1_Extract.py")
        return
    
    # Export summary
    st.header("1. Export Summary")
    
    summary = create_export_summary(selected_tables)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Tables", summary["total_tables"])
    
    with col2:
        total_rows = sum(table["rows"] for table in summary["table_details"])
        st.metric("Total Rows", total_rows)
    
    with col3:
        avg_cols = sum(table["columns"] for table in summary["table_details"]) / len(summary["table_details"])
        st.metric("Avg Columns", f"{avg_cols:.1f}")
    
    # Table details
    with st.expander("📊 Detailed Table Information"):
        for detail in summary["table_details"]:
            st.subheader(f"Table {detail['table_number']}")
            
            info_col1, info_col2 = st.columns(2)
            
            with info_col1:
                st.write(f"**Rows:** {detail['rows']}")
                st.write(f"**Columns:** {detail['columns']}")
            
            with info_col2:
                st.write("**Column Names:**")
                st.write(", ".join(detail['column_names']))
            
            # Preview
            if st.checkbox(f"Show preview for Table {detail['table_number']}", 
                          key=f"preview_{detail['table_number']}"):
                table_idx = detail['table_number'] - 1
                st.dataframe(selected_tables[table_idx].head(), use_container_width=True)
    
    # Export options
    st.header("2. Export Options")