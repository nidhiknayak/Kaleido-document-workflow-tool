# streamlit_app/pages/2_Edit.py
import streamlit as st
import pandas as pd
import sys
import os

# Add parent directory to path to import helpers
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from helpers import (
    get_from_session_state,
    save_to_session_state,
    update_workflow_status,
    display_workflow_progress
)

def main():
    st.set_page_config(
        page_title="Edit Tables", 
        page_icon="✏️", 
        layout="wide"
    )
    
    st.title("✏️ Edit Extracted Tables")
    st.markdown("Review and modify the extracted tabular data before exporting.")
    
    # Display workflow progress
    display_workflow_progress()
    
    # Check if tables are available
    selected_tables = get_from_session_state('selected_tables')
    
    if not selected_tables:
        st.warning("⚠️ No tables found. Please go back to the Extract page to process a document first.")
        if st.button("🔙 Go to Extract Page"):
            st.switch_page("pages/1_Extract.py")
        return
    
    st.success(f"✅ Found {len(selected_tables)} table(s) to edit")
    
    # Table selection
    st.header("1. Select Table to Edit")
    
    if len(selected_tables) > 1:
        table_options = [f"Table {i+1} ({len(df)} rows × {len(df.columns)} cols)" 
                        for i, df in enumerate(selected_tables)]
        selected_table_idx = st.selectbox(
            "Choose a table to edit:",
            range(len(selected_tables)),
            format_func=lambda i: table_options[i]
        )
    else:
        selected_table_idx = 0
        st.info("Editing the only available table")
    
    # Get selected table
    current_table = selected_tables[selected_table_idx].copy()
    
    # Table editing section
    st.header("2. Edit Table Data")
    
    # Table operations
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("➕ Add Row"):
            new_row = pd.Series([''] * len(current_table.columns), 
                              index=current_table.columns)
            current_table = pd.concat([current_table, new_row.to_frame().T], 
                                    ignore_index=True)
    
    with col2:
        if st.button("➕ Add Column"):
            col_name = f"New_Column_{len(current_table.columns)+1}"
            current_table[col_name] = ''
    
    with col3:
        if st.button("🔄 Reset Changes"):
            current_table = selected_tables[selected_table_idx].copy()
            st.success("Table reset to original state")
    
    with col4:
        if st.button("🧹 Clean Data"):
            # Basic data cleaning
            current_table = current_table.dropna(how='all')  # Remove empty rows
            current_table = current_table.fillna('')  # Fill NaN with empty string
            st.success("Basic cleaning applied")
    
    # Data editor
    st.subheader("Interactive Table Editor")
    
    try:
        edited_df = st.data_editor(
            current_table,
            use_container_width=True,
            hide_index=True,
            num_rows="dynamic",
            column_config={
                col: st.column_config.TextColumn(
                    col,
                    help=f"Edit values in {col}",
                    max_chars=200,
                )
                for col in current_table.columns
            },
            key=f"table_editor_{selected_table_idx}"
        )
        
        # Update the table in session state
        selected_tables[selected_table_idx] = edited_df
        save_to_session_state('selected_tables', selected_tables)
        
    except Exception as e:
        st.error(f"Error in table editor: {str(e)}")
        st.info("Falling back to basic display")
        st.dataframe(current_table)
    
    # Column operations
    st.header("3. Column Operations")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Rename Columns")
        for i, col in enumerate(current_table.columns):
            new_name = st.text_input(
                f"Column {i+1}:",
                value=col,
                key=f"rename_{selected_table_idx}_{i}"
            )
            if new_name != col and new_name.strip():
                current_table = current_table.rename(columns={col: new_name})
                selected_tables[selected_table_idx] = current_table
                save_to_session_state('selected_tables', selected_tables)
    
    with col2:
        st.subheader("Column Actions")
        if len(current_table.columns) > 0:
            col_to_action = st.selectbox(
                "Select column for action:",
                current_table.columns
            )
            
            action_col1, action_col2 = st.columns(2)
            
            with action_col1:
                if st.button("🗑️ Delete Column"):
                    if len(current_table.columns) > 1:
                        current_table = current_table.drop(columns=[col_to_action])
                        selected_tables[selected_table_idx] = current_table
                        save_to_session_state('selected_tables', selected_tables)
                        st.success(f"Deleted column: {col_to_action}")
                        st.rerun()
                    else:
                        st.error("Cannot delete the last column")
            
            with action_col2:
                if st.button("📊 Sort by Column"):
                    try:
                        current_table = current_table.sort_values(by=col_to_action)
                        selected_tables[selected_table_idx] = current_table
                        save_to_session_state('selected_tables', selected_tables)
                        st.success(f"Sorted by: {col_to_action}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Sort failed: {str(e)}")
    
    # Data validation
    st.header("4. Data Validation")
    
    validation_col1, validation_col2 = st.columns(2)
    
    with validation_col1:
        st.subheader("Table Statistics")
        st.metric("Rows", len(edited_df))
        st.metric("Columns", len(edited_df.columns))
        st.metric("Empty Cells", edited_df.isnull().sum().sum())
    
    with validation_col2:
        st.subheader("Data Quality")
        
        # Check for empty rows
        empty_rows = edited_df.isnull().all(axis=1).sum()
        if empty_rows > 0:
            st.warning(f"⚠️ {empty_rows} completely empty row(s) found")
        else:
            st.success("✅ No empty rows")
        
        # Check for duplicate rows
        duplicate_rows = edited_df.duplicated().sum()
        if duplicate_rows > 0:
            st.warning(f"⚠️ {duplicate_rows} duplicate row(s) found")
        else:
            st.success("✅ No duplicate rows")
    
    # Data type conversion
    with st.expander("🔧 Advanced: Data Type Conversion"):
        st.subheader("Convert Column Types")
        
        for col in edited_df.columns:
            col1, col2, col3 = st.columns([2, 2, 1])
            
            with col1:
                st.text(f"Column: {col}")
            
            with col2:
                new_type = st.selectbox(
                    "Type:",
                    ["string", "numeric", "datetime"],
                    key=f"type_{col}_{selected_table_idx}"
                )
            
            with col3:
                if st.button("Convert", key=f"convert_{col}_{selected_table_idx}"):
                    try:
                        if new_type == "numeric":
                            edited_df[col] = pd.to_numeric(edited_df[col], errors='coerce')
                        elif new_type == "datetime":
                            edited_df[col] = pd.to_datetime(edited_df[col], errors='coerce')
                        # string is default, no conversion needed
                        
                        selected_tables[selected_table_idx] = edited_df
                        save_to_session_state('selected_tables', selected_tables)
                        st.success(f"✅ Converted {col} to {new_type}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Conversion failed: {str(e)}")
    
    # Action buttons
    st.header("5. Next Steps")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💾 Save Changes & Export", type="primary"):
            update_workflow_status('review', 'completed')
            st.success("✅ Changes saved!")
            st.switch_page("pages/3_Export.py")
    
    with col2:
        if st.button("🔙 Back to Extract"):
            st.switch_page("pages/1_Extract.py")
    
    with col3:
        if st.button("🔄 View Workflow"):
            st.switch_page("pages/4_Workflow.py")

if __name__ == "__main__":
    main()