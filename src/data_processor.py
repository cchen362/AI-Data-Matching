"""Data processing module for different file types and sources."""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
import logging
from datetime import datetime
from src.llm_column_mapper import LLMColumnMapper

logger = logging.getLogger(__name__)

class DataProcessor:
    """Handles data processing for different file types (Raindrop, EGE, BT)."""
    
    def __init__(self):
        self.processed_data = {}
        self.column_mappings = {}
        self.llm_mapper = LLMColumnMapper()
    
    def detect_file_type(self, df: pd.DataFrame, filename: str) -> str:
        """Detect file type using LLM-powered analysis."""
        columns = list(df.columns)
        
        # Get sample data for better context
        sample_data = self.llm_mapper.get_sample_data(df)
        
        # Use LLM to detect file type
        file_type = self.llm_mapper.detect_file_type_with_llm(columns, filename, sample_data)
        
        logger.info(f"Detected file type '{file_type}' for {filename}")
        return file_type
    
    def load_and_detect_file(self, file_path: str) -> Tuple[pd.DataFrame, str]:
        """Load file and detect its type."""
        path = Path(file_path)
        
        try:
            # Load based on file extension
            if path.suffix.lower() == '.csv':
                df = pd.read_csv(file_path, encoding='utf-8')
            elif path.suffix.lower() in ['.xlsx', '.xls']:
                # Try to find the sheet with the most data and relevant headers
                excel_file = pd.ExcelFile(file_path)
                best_sheet = None
                max_rows = 0
                
                for sheet_name in excel_file.sheet_names:
                    temp_df = pd.read_excel(file_path, sheet_name=sheet_name)
                    if len(temp_df) > max_rows and len(temp_df.columns) > 3:
                        # Check if it has reasonable column headers
                        if any(isinstance(col, str) and len(col) > 2 for col in temp_df.columns):
                            max_rows = len(temp_df)
                            best_sheet = sheet_name
                
                if best_sheet:
                    df = pd.read_excel(file_path, sheet_name=best_sheet)
                else:
                    df = pd.read_excel(file_path)
            else:
                raise ValueError(f"Unsupported file format: {path.suffix}")
            
            # Clean column names
            df.columns = df.columns.astype(str).str.strip()
            
            # Detect file type
            file_type = self.detect_file_type(df, path.name)
            
            logger.info(f"Loaded file {path.name}: {len(df)} rows, detected as {file_type}")
            return df, file_type
            
        except Exception as e:
            logger.error(f"Error loading file {file_path}: {str(e)}")
            raise
    
    def process_raindrop_contracts(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process Raindrop contract data using LLM column mapping."""
        processed_df = df.copy()
        
        # Use LLM to map columns to standardized schema
        sample_data = self.llm_mapper.get_sample_data(df)
        column_mapping = self.llm_mapper.map_columns_with_llm(
            list(df.columns), 'raindrop_vendors', sample_data
        )
        
        logger.info(f"LLM mapped Raindrop columns: {column_mapping}")
        
        # Check if we found the essential company name column
        if 'company_name' not in column_mapping:
            raise ValueError("Could not identify company name column in Raindrop data")
        
        # Apply the mapping to get standardized columns
        company_col = column_mapping['company_name']
        value_col = column_mapping.get('contract_value')
        currency_col = column_mapping.get('currency')
        terms_col = column_mapping.get('contract_terms') 
        end_date_col = column_mapping.get('end_date')
        
        # Create standardized columns
        processed_df['company_name'] = processed_df[company_col].astype(str).str.strip()
        
        if value_col and value_col in processed_df.columns:
            processed_df['total_value'] = self._extract_numeric(processed_df[value_col])
        else:
            processed_df['total_value'] = 0
            
        if currency_col and currency_col in processed_df.columns:
            processed_df['currency'] = processed_df[currency_col]
        else:
            processed_df['currency'] = 'USD'  # Default assumption
            
        if terms_col and terms_col in processed_df.columns:
            processed_df['terms_months'] = processed_df[terms_col]
        else:
            processed_df['terms_months'] = 'Not specified'
            
        if end_date_col and end_date_col in processed_df.columns:
            processed_df['end_date'] = pd.to_datetime(processed_df[end_date_col], errors='coerce')
        else:
            processed_df['end_date'] = pd.NaT
        
        # Add source identifier
        processed_df['source'] = 'raindrop'
        processed_df['record_type'] = 'vendor'
        
        logger.info(f"Processed {len(processed_df)} Raindrop contracts")
        return processed_df
    
    def process_ege_customers(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process EGE Active Customers data."""
        processed_df = df.copy()
        
        # Find relevant columns
        account_col = self._find_column(df, ['account name', 'account'])
        parent_col = self._find_column(df, ['ultimate parent account', 'parent account', 'ultimate parent'])
        budget_col = self._find_column(df, ['contracted annual travel budget', 'travel budget', 'budget'])
        currency_col = self._find_column(df, ['currency', 'currency code'])
        
        if not account_col:
            raise ValueError("Could not find account name column in EGE Customers data")
        
        # Use parent account if available, otherwise use account name
        if parent_col and not processed_df[parent_col].isna().all():
            processed_df['company_name'] = processed_df[parent_col].fillna(processed_df[account_col])
        else:
            processed_df['company_name'] = processed_df[account_col]
        
        # Clean company names
        processed_df['company_name'] = processed_df['company_name'].astype(str).str.strip()
        
        # Process budget values
        if budget_col:
            processed_df['client_spend'] = self._extract_numeric(processed_df[budget_col])
        else:
            processed_df['client_spend'] = 0
        
        # Handle currency
        if currency_col:
            processed_df['currency'] = processed_df[currency_col]
        else:
            processed_df['currency'] = 'USD'  # Default assumption
        
        # Group by company name and sum budgets
        grouped = processed_df.groupby('company_name').agg({
            'client_spend': 'sum',
            'currency': 'first'  # Take first currency for each group
        }).reset_index()
        
        # Add metadata
        grouped['source'] = 'ege_customers'
        grouped['record_type'] = 'client'
        grouped['contract_type'] = 'active'
        
        return grouped
    
    def process_ege_opportunities(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process EGE Active Opportunities data."""
        processed_df = df.copy()
        
        # Find relevant columns
        account_col = self._find_column(df, ['account name', 'account'])
        parent_col = self._find_column(df, ['ultimate parent account', 'parent account'])
        value_col = self._find_column(df, ['corporate gross bookings value', 'bookings value', 'value'])
        stage_col = self._find_column(df, ['stage'])
        
        if not account_col:
            raise ValueError("Could not find account name column in EGE Opportunities data")
        
        # Use parent account if available
        if parent_col and not processed_df[parent_col].isna().all():
            processed_df['company_name'] = processed_df[parent_col].fillna(processed_df[account_col])
        else:
            processed_df['company_name'] = processed_df[account_col]
        
        processed_df['company_name'] = processed_df['company_name'].astype(str).str.strip()
        
        # Process opportunity values (already in USD)
        if value_col:
            processed_df['client_spend'] = self._extract_numeric(processed_df[value_col])
        else:
            processed_df['client_spend'] = 0
        
        # Group by company name
        agg_dict = {
            'client_spend': 'sum',
        }
        
        if stage_col:
            agg_dict[stage_col] = 'first'  # Use actual column name, not 'stage'
        
        grouped = processed_df.groupby('company_name').agg(agg_dict).reset_index()
        
        # Add metadata
        grouped['source'] = 'ege_opportunities'
        grouped['record_type'] = 'opportunity'
        grouped['currency'] = 'USD'  # EGE opportunities are already in USD
        
        return grouped
    
    def process_bt_clients(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process BT Active Clients data."""
        processed_df = df.copy()
        
        # Find relevant columns based on actual BT data structure
        account_col = self._find_column(df, ['account name', 'account'])
        parent_col = self._find_column(df, ['ultimate parent name', 'parent name'])
        volume_col = self._find_column(df, ['expected total travel volume', 'travel volume'])
        currency_col = self._find_column(df, ['expected total travel volume currency', 'currency'])
        
        if not account_col:
            raise ValueError("Could not find account name column in BT Clients data")
        
        # Use parent name if available, otherwise account name
        if parent_col and not processed_df[parent_col].isna().all():
            processed_df['company_name'] = processed_df[parent_col].fillna(processed_df[account_col])
        else:
            processed_df['company_name'] = processed_df[account_col]
        
        processed_df['company_name'] = processed_df['company_name'].astype(str).str.strip()
        
        # Process volume values
        if volume_col:
            processed_df['client_spend'] = self._extract_numeric(processed_df[volume_col])
        else:
            processed_df['client_spend'] = 0
        
        # Handle currency
        if currency_col:
            processed_df['currency'] = processed_df[currency_col]
        else:
            processed_df['currency'] = 'USD'  # Default for BT data
        
        # Group by company name and sum volumes
        grouped = processed_df.groupby('company_name').agg({
            'client_spend': 'sum',
            'currency': 'first'
        }).reset_index()
        
        # Add metadata
        grouped['source'] = 'bt_clients'
        grouped['record_type'] = 'client'
        grouped['contract_type'] = 'active'
        
        return grouped
    
    def process_bt_opportunities(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process BT Opportunity Pipeline data."""
        processed_df = df.copy()
        
        # Find relevant columns based on actual BT opportunities structure
        account_col = self._find_column(df, ['account name', 'company name'])
        parent_col = self._find_column(df, ['ultimate parent name', 'parent name'])
        volume_col = self._find_column(df, ['expected total travel volume (converted)', 'expected total travel volume', 'travel volume'])
        stage_col = self._find_column(df, ['stage'])
        
        if not account_col:
            raise ValueError("Could not find account name column in BT Opportunities data")
        
        # Use parent name if available, otherwise account/company name
        if parent_col and not processed_df[parent_col].isna().all():
            # Fill missing parent names with account names
            processed_df['company_name'] = processed_df[parent_col].fillna(processed_df[account_col])
        else:
            processed_df['company_name'] = processed_df[account_col]
        
        # Clean company names
        processed_df['company_name'] = processed_df['company_name'].astype(str).str.strip()
        
        # Process volume values (already converted to USD in the Excel)
        if volume_col:
            processed_df['client_spend'] = self._extract_numeric(processed_df[volume_col])
        else:
            processed_df['client_spend'] = 0
        
        # Group by company name and aggregate
        agg_dict = {
            'client_spend': 'sum',
        }
        
        if stage_col:
            agg_dict[stage_col] = 'first'  # Use actual column name
        
        grouped = processed_df.groupby('company_name').agg(agg_dict).reset_index()
        
        # Add metadata
        grouped['source'] = 'bt_opportunities'
        grouped['record_type'] = 'opportunity'
        grouped['currency'] = 'USD'  # BT opportunities are already converted to USD
        
        return grouped
    
    def _find_column(self, df: pd.DataFrame, possible_names: List[str]) -> Optional[str]:
        """Find a column that matches one of the possible names (case-insensitive)."""
        df_columns = [col.lower().strip() for col in df.columns]
        
        for possible_name in possible_names:
            possible_name = possible_name.lower()
            # Exact match first
            for i, col in enumerate(df_columns):
                if col == possible_name:
                    return df.columns[i]
            
            # Partial match
            for i, col in enumerate(df_columns):
                if possible_name in col or any(word in col for word in possible_name.split()):
                    return df.columns[i]
        
        return None
    
    def _extract_numeric(self, series: pd.Series) -> pd.Series:
        """Extract numeric values from a series, handling various formats."""
        def clean_value(val):
            if pd.isna(val):
                return 0
            
            # Convert to string and clean
            val_str = str(val).strip()
            if val_str == '' or val_str.lower() in ['nan', 'null', 'none']:
                return 0
            
            # Remove currency symbols and formatting
            val_str = val_str.replace('$', '').replace('€', '').replace('£', '')
            val_str = val_str.replace(',', '').replace(' ', '')
            
            # Extract numeric part
            import re
            numeric_match = re.search(r'-?\d+\.?\d*', val_str)
            if numeric_match:
                try:
                    return float(numeric_match.group())
                except ValueError:
                    return 0
            
            return 0
        
        return series.apply(clean_value)