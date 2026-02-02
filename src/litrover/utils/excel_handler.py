"""
Excel handler for LitRover
Handles reading/writing Excel files with flexible column mapping
"""

import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional
import re


class ExcelHandler:
    """Handle Excel file operations with flexible column mapping"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Excel handler
        
        Args:
            config: Configuration dictionary with column mappings
        """
        self.config = config
        self.df = None
        self.identifier_col = config['columns']['identifier']
        self.paper_cols = config['columns']['paper_refs']
        self.preserve_cols = config['columns'].get('preserve_columns', [])
        
    def load_excel(self, file_path: str) -> pd.DataFrame:
        """
        Load Excel file
        
        Args:
            file_path: Path to Excel file
            
        Returns:
            Pandas DataFrame
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If required columns are missing
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Excel file not found: {file_path}")
        
        # Load Excel
        self.df = pd.read_excel(file_path)
        
        # Validate required columns exist
        missing_cols = []
        
        if self.identifier_col not in self.df.columns:
            missing_cols.append(self.identifier_col)
        
        for col in self.paper_cols:
            if col not in self.df.columns:
                missing_cols.append(col)
        
        if missing_cols:
            raise ValueError(
                f"Required columns not found in Excel file: {missing_cols}\n"
                f"Available columns: {list(self.df.columns)}"
            )
        
        return self.df
    
    def create_template(self, output_path: str, schema: List[Dict[str, Any]]):
        """
        Create Excel template based on schema
        
        Args:
            output_path: Path to save template
            schema: Extraction schema with field definitions
        """
        # Create columns
        columns = [self.identifier_col] + self.paper_cols
        
        # Add schema fields as columns
        for field in schema:
            field_name = field['field']
            if field_name not in columns:
                columns.append(field_name)
        
        # Add metadata columns
        columns.extend(['extraction_timestamp', 'extraction_source', 'confidence'])
        
        # Create empty DataFrame
        df = pd.DataFrame(columns=columns)
        
        # Add example row with instructions
        example_row = {self.identifier_col: "EXAMPLE_ID"}
        example_row[self.paper_cols[0]] = "https://doi.org/10.xxxx/xxxxx OR Smith et al., 2020"
        
        for field in schema:
            field_name = field['field']
            field_type = field['type']
            example_row[field_name] = f"<{field_type}>"
        
        df = pd.concat([df, pd.DataFrame([example_row])], ignore_index=True)
        
        # Save with formatting
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Data')
            
            # Auto-adjust column widths
            worksheet = writer.sheets['Data']
            for idx, col in enumerate(df.columns, 1):
                max_length = max(
                    df[col].astype(str).apply(len).max(),
                    len(col)
                ) + 2
                worksheet.column_dimensions[chr(64 + idx)].width = min(max_length, 50)
    
    def add_extraction_columns(self, schema: List[Dict[str, Any]]):
        """
        Add columns for extracted data if they don't exist
        
        Args:
            schema: Extraction schema
        """
        if self.df is None:
            raise ValueError("No DataFrame loaded. Call load_excel() first.")
        
        for field in schema:
            field_name = field['field']
            if field_name not in self.df.columns:
                self.df[field_name] = None
        
        # Add metadata columns
        for col in ['extraction_timestamp', 'extraction_source', 'confidence']:
            if col not in self.df.columns:
                self.df[col] = None
    
    def update_row(self, row_idx: int, extracted_data: Dict[str, Any],
                   metadata: Optional[Dict[str, Any]] = None):
        """
        Update a row with extracted data
        
        Args:
            row_idx: Row index
            extracted_data: Extracted field values
            metadata: Optional metadata (timestamp, source, confidence)
        """
        if self.df is None:
            raise ValueError("No DataFrame loaded")
        
        # Update extracted fields (only if current value is null)
        for field, value in extracted_data.items():
            if field in self.df.columns:
                current_value = self.df.at[row_idx, field]
                if pd.isna(current_value):
                    self.df.at[row_idx, field] = value
        
        # Update metadata
        if metadata:
            for key, value in metadata.items():
                if key in self.df.columns:
                    self.df.at[row_idx, key] = value
    
    def insert_rows_after(self, row_idx: int, rows_data: List[Dict[str, Any]], 
                         metadata: Optional[Dict[str, Any]] = None):
        """
        Insert multiple new rows after a given row index (for multi-core extraction)
        
        Args:
            row_idx: Index of the original row
            rows_data: List of dictionaries with extracted data for each core
            metadata: Optional metadata to apply to all new rows
        """
        if self.df is None:
            raise ValueError("No DataFrame loaded")
        
        if not rows_data:
            return
        
        # Get the original row to copy paper reference and identifier
        original_row = self.df.iloc[row_idx].copy()
        
        # Create new rows
        new_rows = []
        for core_data in rows_data:
            # Start with a copy of the original row (to preserve paper refs)
            new_row = original_row.copy()
            
            # Update with extracted data
            for field, value in core_data.items():
                if field in self.df.columns:
                    new_row[field] = value
            
            # Add metadata
            if metadata:
                for key, value in metadata.items():
                    if key in self.df.columns:
                        new_row[key] = value
            
            new_rows.append(new_row)
        
        # Insert new rows after the original row
        # Split dataframe at insertion point
        df_before = self.df.iloc[:row_idx + 1]
        df_after = self.df.iloc[row_idx + 1:]
        
        # Create DataFrame from new rows
        new_df = pd.DataFrame(new_rows)
        
        # Concatenate
        self.df = pd.concat([df_before, new_df, df_after], ignore_index=True)

    def get_papers_for_row(self, row_idx: int) -> List[Dict[str, Any]]:
        """
        Get all paper references for a specific row
        
        Args:
            row_idx: Row index
            
        Returns:
            List of paper info dictionaries
        """
        if self.df is None:
            raise ValueError("No DataFrame loaded")
        
        row = self.df.iloc[row_idx]
        papers = []
        
        for col_idx, col in enumerate(self.paper_cols):
            value = row.get(col)
            
            if pd.notna(value) and str(value).strip():
                value_str = str(value).strip()
                
                papers.append({
                    'column': col,
                    'column_index': col_idx,
                    'value': value_str,
                    'is_url': value_str.startswith('http'),
                    'is_doi': 'doi.org' in value_str or value_str.startswith('10.'),
                })
        
        return papers
    
    def save_excel(self, output_path: str, create_backup: bool = True):
        """
        Save DataFrame to Excel
        
        Args:
            output_path: Output file path
            create_backup: Whether to create backup of existing file
        """
        if self.df is None:
            raise ValueError("No DataFrame to save")
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create backup if file exists
        if create_backup and output_path.exists():
            backup_path = output_path.parent / f"{output_path.stem}_backup{output_path.suffix}"
            import shutil
            shutil.copy2(output_path, backup_path)
        
        # Save
        self.df.to_excel(output_path, index=False, engine='openpyxl')
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """
        Get summary statistics
        
        Returns:
            Dictionary of summary statistics
        """
        if self.df is None:
            return {}
        
        stats = {
            'total_rows': len(self.df),
            'total_papers': sum(
                self.df[col].notna().sum() for col in self.paper_cols
            ),
        }
        
        # Count nulls for each extracted field
        schema_fields = [col for col in self.df.columns 
                        if col not in [self.identifier_col] + self.paper_cols + self.preserve_cols]
        
        for field in schema_fields:
            if field in self.df.columns:
                null_count = self.df[field].isna().sum()
                filled_count = len(self.df) - null_count
                stats[f'{field}_filled'] = filled_count
                stats[f'{field}_null'] = null_count
        
        return stats
    
    @staticmethod
    def sanitize_filename(text: str, max_length: int = 100) -> str:
        """
        Create safe filename from text
        
        Args:
            text: Input text
            max_length: Maximum filename length
            
        Returns:
            Sanitized filename
        """
        # Remove invalid characters
        text = re.sub(r'[<>:"/\\|?*]', '_', str(text))
        text = re.sub(r'\s+', '_', text)
        return text[:max_length]
    
    @staticmethod
    def clean_doi(doi_or_url: str) -> Optional[str]:
        """
        Extract clean DOI from URL or text
        
        Args:
            doi_or_url: DOI URL or DOI string
            
        Returns:
            Clean DOI or None
        """
        if not isinstance(doi_or_url, str):
            return None
        
        match = re.search(r'(10\.\d{4,9}/[-._;()/:A-Z0-9]+)', doi_or_url, re.IGNORECASE)
        return match.group(1) if match else None
