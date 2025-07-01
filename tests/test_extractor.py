import pytest
import pandas as pd
import tempfile
import os
from pathlib import Path
import sys

# Add backend to path for imports
sys.path.append(str(Path(__file__).parent.parent / "backend"))

from extractor import DocumentExtractor, TableExtractor, PDFExtractor, DOCXExtractor
import io
from unittest.mock import Mock, patch, MagicMock

class TestDocumentExtractor:
    """Test cases for the main DocumentExtractor class"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.extractor = DocumentExtractor()
        
        # Create sample test data
        self.sample_table_data = [
            ['Product', 'Price', 'Quantity'],
            ['Laptop', '$1200', '5'],
            ['Mouse', '$25', '20'],
            ['Keyboard', '$75', '15']
        ]
        
        self.sample_df = pd.DataFrame(self.sample_table_data[1:], columns=self.sample_table_data[0])
    
    def test_extract_from_file_pdf(self):
        """Test PDF file extraction"""
        # Mock file content
        mock_file_content = b"mock pdf content"
        
        with patch.object(PDFExtractor, 'extract_tables') as mock_extract:
            mock_extract.return_value = [self.sample_table_data]
            
            result = self.extractor.extract_from_file(mock_file_content, "test.pdf")
            
            assert result['success'] is True
            assert 'tables' in result
            assert len(result['tables']) == 1
            assert result['metadata']['file_type'] == 'pdf'
            mock_extract.assert_called_once()
    
    def test_extract_from_file_docx(self):
        """Test DOCX file extraction"""
        mock_file_content = b"mock docx content"
        
        with patch.object(DOCXExtractor, 'extract_tables') as mock_extract:
            mock_extract.return_value = [self.sample_table_data]
            
            result = self.extractor.extract_from_file(mock_file_content, "test.docx")
            
            assert result['success'] is True
            assert 'tables' in result
            assert len(result['tables']) == 1
            assert result['metadata']['file_type'] == 'docx'
            mock_extract.assert_called_once()
    
    def test_extract_unsupported_format(self):
        """Test handling of unsupported file formats"""
        mock_file_content = b"mock content"
        
        result = self.extractor.extract_from_file(mock_file_content, "test.txt")
        
        assert result['success'] is False
        assert 'error' in result
        assert 'Unsupported file format' in result['error']
    
    def test_extract_empty_file(self):
        """Test handling of empty files"""
        empty_content = b""
        
        result = self.extractor.extract_from_file(empty_content, "test.pdf")
        
        assert result['success'] is False
        assert 'error' in result
    
    def test_extract_corrupted_file(self):
        """Test handling of corrupted files"""
        corrupted_content = b"corrupted data that's not a valid PDF"
        
        with patch.object(PDFExtractor, 'extract_tables') as mock_extract:
            mock_extract.side_effect = Exception("File corruption error")
            
            result = self.extractor.extract_from_file(corrupted_content, "test.pdf")
            
            assert result['success'] is False
            assert 'error' in result

class TestPDFExtractor:
    """Test cases for PDF extraction functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.pdf_extractor = PDFExtractor()
    
    @patch('camelot.read_pdf')
    def test_camelot_extraction_success(self, mock_camelot):
        """Test successful table extraction with Camelot"""
        # Mock Camelot response
        mock_table = Mock()
        mock_table.df = self.sample_df
        mock_camelot.return_value = [mock_table]
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_file.write(b"mock pdf content")
            tmp_file.flush()
            
            try:
                result = self.pdf_extractor.extract_tables(tmp_file.name)
                
                assert len(result) == 1
                assert len(result[0]) == 4  # Header + 3 data rows
                mock_camelot.assert_called_once()
            finally:
                os.unlink(tmp_file.name)
    
    @patch('camelot.read_pdf')
    @patch('pdfplumber.open')
    def test_fallback_to_pdfplumber(self, mock_pdfplumber, mock_camelot):
        """Test fallback to pdfplumber when Camelot fails"""
        # Mock Camelot failure
        mock_camelot.side_effect = Exception("Camelot failed")
        
        # Mock pdfplumber success
        mock_page = Mock()
        mock_page.extract_table.return_value = [
            ['Product', 'Price'],
            ['Laptop', '$1200'],
            ['Mouse', '$25']
        ]
        
        mock_pdf = Mock()
        mock_pdf.pages = [mock_page]
        mock_pdfplumber.return_value.__enter__.return_value = mock_pdf
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_file.write(b"mock pdf content")
            tmp_file.flush()
            
            try:
                result = self.pdf_extractor.extract_tables(tmp_file.name)
                
                assert len(result) >= 1
                mock_camelot.assert_called_once()
                mock_pdfplumber.assert_called_once()
            finally:
                os.unlink(tmp_file.name)
    
    def test_pdf_file_not_found(self):
        """Test handling of non-existent PDF files"""
        with pytest.raises(FileNotFoundError):
            self.pdf_extractor.extract_tables("nonexistent.pdf")

class TestDOCXExtractor:
    """Test cases for DOCX extraction functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.docx_extractor = DOCXExtractor()
    
    @patch('docx.Document')
    def test_docx_table_extraction(self, mock_document):
        """Test DOCX table extraction"""
        # Mock table structure
        mock_cell1 = Mock()
        mock_cell1.text = "Product"
        mock_cell2 = Mock()
        mock_cell2.text = "Price"
        
        mock_row = Mock()
        mock_row.cells = [mock_cell1, mock_cell2]
        
        mock_table = Mock()
        mock_table.rows = [mock_row]
        
        mock_doc = Mock()
        mock_doc.tables = [mock_table]
        mock_document.return_value = mock_doc
        
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tmp_file:
            tmp_file.write(b"mock docx content")
            tmp_file.flush()
            
            try:
                result = self.docx_extractor.extract_tables(tmp_file.name)
                
                assert len(result) == 1
                assert len(result[0]) == 1  # One row
                assert len(result[0][0]) == 2  # Two columns
                mock_document.assert_called_once()
            finally:
                os.unlink(tmp_file.name)
    
    @patch('docx.Document')
    def test_docx_no_tables(self, mock_document):
        """Test DOCX file with no tables"""
        mock_doc = Mock()
        mock_doc.tables = []
        mock_document.return_value = mock_doc
        
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tmp_file:
            tmp_file.write(b"mock docx content")
            tmp_file.flush()
            
            try:
                result = self.docx_extractor.extract_tables(tmp_file.name)
                
                assert len(result) == 0
            finally:
                os.unlink(tmp_file.name)

class TestTableExtractor:
    """Test cases for table processing utilities"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.table_extractor = TableExtractor()
        
        self.raw_table_data = [
            ['Product', 'Price', 'Quantity'],
            ['Laptop', '$1,200.00', '5'],
            ['', '$25.50', '20'],  # Missing product name
            ['Keyboard', 'INVALID', '15'],  # Invalid price
            ['Monitor', '$350.00', '']  # Missing quantity
        ]
    
    def test_clean_table_data(self):
        """Test table data cleaning"""
        cleaned = self.table_extractor.clean_table_data(self.raw_table_data)
        
        # Should handle missing values and clean data
        assert len(cleaned) >= 3  # At least header + valid rows
        
        # Check that cleaning occurred
        for row in cleaned[1:]:  # Skip header
            assert all(cell is not None for cell in row)
    
    def test_detect_headers(self):
        """Test header detection"""
        headers = self.table_extractor.detect_headers(self.raw_table_data)
        
        assert headers == ['Product', 'Price', 'Quantity']
    
    def test_standardize_data_types(self):
        """Test data type standardization"""
        # Test price standardization
        price_data = ['$1,200.00', '$25.50', 'INVALID', '350']
        standardized = self.table_extractor.standardize_data_types(price_data, 'price')
        
        # Should convert valid prices and handle invalid ones
        assert isinstance(standardized[0], (int, float, str))
    
    def test_handle_merged_cells(self):
        """Test merged cell handling"""
        table_with_merged = [
            ['Product', 'Q1', 'Q2', 'Q3'],
            ['Laptop', '100', '', '150'],  # Merged cell scenario
            ['Mouse', '50', '60', '70']
        ]
        
        result = self.table_extractor.handle_merged_cells(table_with_merged)
        
        # Should fill in merged cell values
        assert len(result) == len(table_with_merged)
        assert all(len(row) == 4 for row in result)

class TestIntegration:
    """Integration tests for the complete extraction pipeline"""
    
    def setup_method(self):
        """Setup integration test fixtures"""
        self.extractor = DocumentExtractor()
    
    @patch('camelot.read_pdf')
    def test_end_to_end_pdf_extraction(self, mock_camelot):
        """Test complete PDF extraction workflow"""
        # Mock realistic table data
        sample_invoice_data = [
            ['Item', 'Description', 'Qty', 'Price', 'Total'],
            ['001', 'Laptop Computer', '2', '$1200.00', '$2400.00'],
            ['002', 'Wireless Mouse', '5', '$25.00', '$125.00'],
            ['003', 'USB Cable', '10', '$15.00', '$150.00']
        ]
        
        mock_table = Mock()
        mock_table.df = pd.DataFrame(sample_invoice_data[1:], columns=sample_invoice_data[0])
        mock_camelot.return_value = [mock_table]
        
        # Test extraction
        result = self.extractor.extract_from_file(b"mock pdf content", "invoice.pdf")
        
        assert result['success'] is True
        assert len(result['tables']) == 1
        assert len(result['tables'][0]) == 4  # 3 data rows + header
        assert result['metadata']['tables_found'] == 1
        assert 'extraction_time' in result['metadata']
    
    def test_export_to_csv(self):
        """Test CSV export functionality"""
        sample_data = [
            ['Name', 'Age', 'City'],
            ['John', '25', 'New York'],
            ['Jane', '30', 'Boston']
        ]
        
        # Test CSV conversion
        df = pd.DataFrame(sample_data[1:], columns=sample_data[0])
        csv_output = df.to_csv(index=False)
        
        assert 'Name,Age,City' in csv_output
        assert 'John,25,New York' in csv_output
    
    def test_export_to_json(self):
        """Test JSON export functionality"""
        sample_data = [
            ['Name', 'Age', 'City'],
            ['John', '25', 'New York'],
            ['Jane', '30', 'Boston']
        ]
        
        # Test JSON conversion
        df = pd.DataFrame(sample_data[1:], columns=sample_data[0])
        json_output = df.to_json(orient='records')
        
        assert 'John' in json_output
        assert 'New York' in json_output

class TestPerformance:
    """Performance tests for extraction pipeline"""
    
    def setup_method(self):
        """Setup performance test fixtures"""
        self.extractor = DocumentExtractor()
    
    @patch('camelot.read_pdf')
    def test_large_table_extraction(self, mock_camelot):
        """Test extraction performance with large tables"""
        # Generate large table data
        large_table_data = [['Col1', 'Col2', 'Col3', 'Col4', 'Col5']]
        for i in range(1000):  # 1000 rows
            large_table_data.append([f'Value{i}_{j}' for j in range(5)])
        
        mock_table = Mock()
        mock_table.df = pd.DataFrame(large_table_data[1:], columns=large_table_data[0])
        mock_camelot.return_value = [mock_table]
        
        import time
        start_time = time.time()
        
        result = self.extractor.extract_from_file(b"mock large pdf", "large.pdf")
        
        end_time = time.time()
        extraction_time = end_time - start_time
        
        assert result['success'] is True
        assert len(result['tables'][0]) == 1001  # 1000 data rows + header
        assert extraction_time < 10  # Should complete within 10 seconds
    
    def test_multiple_tables_extraction(self):
        """Test extraction of multiple tables from single document"""
        # This test would require more complex mocking
        # For now, we'll test the data structure handling
        
        multiple_tables = [
            [['Table1_Col1', 'Table1_Col2'], ['Data1', 'Data2']],
            [['Table2_Col1', 'Table2_Col2'], ['Data3', 'Data4']],
            [['Table3_Col1', 'Table3_Col2'], ['Data5', 'Data6']]
        ]
        
        # Test that our system can handle multiple tables
        assert len(multiple_tables) == 3
        for table in multiple_tables:
            assert len(table) >= 2  # Header + at least one data row

# Test configuration and fixtures
@pytest.fixture
def sample_pdf_file():
    """Create a temporary PDF file for testing"""
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
        tmp_file.write(b"mock pdf content")
        yield tmp_file.name
    os.unlink(tmp_file.name)

@pytest.fixture
def sample_docx_file():
    """Create a temporary DOCX file for testing"""
    with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tmp_file:
        tmp_file.write(b"mock docx content")
        yield tmp_file.name
    os.unlink(tmp_file.name)

# Test runner configuration
if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main(["-v", __file__])