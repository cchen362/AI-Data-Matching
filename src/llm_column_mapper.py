"""LLM-powered intelligent column mapping for flexible data processing."""

import openai
import json
import logging
from typing import Dict, List, Optional, Tuple
import pandas as pd
from src.config import OPENAI_API_KEY, OPENAI_MODEL

logger = logging.getLogger(__name__)

class LLMColumnMapper:
    """Uses LLM to intelligently map columns to standardized schema."""
    
    def __init__(self):
        if OPENAI_API_KEY:
            openai.api_key = OPENAI_API_KEY
            self.llm_available = True
        else:
            logger.warning("OpenAI API key not found. LLM column mapping disabled.")
            self.llm_available = False
    
    def get_schema_definitions(self) -> Dict:
        """Define the core schema that we want to map to."""
        return {
            "raindrop_vendors": {
                "company_name": {
                    "description": "The actual vendor/supplier company name (not contract name/title)",
                    "examples": ["Microsoft Corporation", "IBM", "Accenture PLC", "Deloitte Consulting"],
                    "keywords": ["supplier", "vendor", "company", "corporation", "organization"]
                },
                "individual_supplier_name": {
                    "description": "The individual supplier or vendor name for each specific contract",
                    "examples": ["Microsoft Corp - Contract A", "IBM Services", "Accenture Digital", "Individual Vendor Name"],
                    "keywords": ["name", "individual name", "contract name", "specific supplier", "vendor name"]
                },
                "contract_value": {
                    "description": "Total monetary value of the contract",
                    "examples": ["125000", "1500000.50", "$2,500,000"],
                    "keywords": ["total value", "value", "amount", "cost", "price", "contract value"]
                },
                "currency": {
                    "description": "Currency code for the contract value",
                    "examples": ["USD", "EUR", "GBP", "JPY"],
                    "keywords": ["currency", "currency code", "curr"]
                },
                "contract_terms": {
                    "description": "Contract duration in months or other time period",
                    "examples": ["12", "24", "36 months"],
                    "keywords": ["term", "terms", "duration", "months", "period"]
                },
                "end_date": {
                    "description": "Contract expiration or end date",
                    "examples": ["2025-12-31", "December 31, 2025"],
                    "keywords": ["end date", "expiry", "expiration", "expires"]
                }
            },
            "ege_customers": {
                "account_name": {
                    "description": "Individual account or subsidiary name",
                    "examples": ["Microsoft US", "IBM Europe", "Accenture Americas"],
                    "keywords": ["account name", "account", "client", "customer"]
                },
                "parent_company": {
                    "description": "Ultimate parent company or holding company name",
                    "examples": ["Microsoft Corporation - Ultimate Parent", "IBM - Ultimate Parent"],
                    "keywords": ["ultimate parent", "parent account", "parent company", "holding company"]
                },
                "travel_budget": {
                    "description": "Annual travel budget amount",
                    "examples": ["500000", "1200000.00", "$750,000"],
                    "keywords": ["travel budget", "annual budget", "contracted budget", "spend"]
                },
                "currency": {
                    "description": "Currency for the budget amount",
                    "examples": ["USD", "EUR", "GBP"],
                    "keywords": ["currency", "currency code", "curr"]
                }
            },
            "ege_opportunities": {
                "account_name": {
                    "description": "Account or client company name for the opportunity",
                    "examples": ["Microsoft Corp", "IBM Global", "Oracle Inc"],
                    "keywords": ["account name", "company", "client", "opportunity name"]
                },
                "parent_company": {
                    "description": "Ultimate parent or holding company",
                    "examples": ["Microsoft Corporation", "IBM - Ultimate Parent"],
                    "keywords": ["ultimate parent", "parent account", "parent company"]
                },
                "opportunity_value": {
                    "description": "Expected value or bookings value of the opportunity",
                    "examples": ["750000", "$1,500,000", "2500000.00"],
                    "keywords": ["bookings value", "opportunity value", "gross bookings", "value"]
                },
                "stage": {
                    "description": "Sales stage or pipeline stage of the opportunity",
                    "examples": ["Discovery", "Proposal", "Negotiation", "Approach"],
                    "keywords": ["stage", "pipeline stage", "sales stage", "status"]
                }
            },
            "bt_clients": {
                "account_name": {
                    "description": "Client account name",
                    "examples": ["Microsoft Asia", "IBM Canada"],
                    "keywords": ["account name", "client", "customer"]
                },
                "parent_company": {
                    "description": "Ultimate parent company name",
                    "examples": ["Microsoft Corporation - Ultimate Parent", "IBM - Ultimate Parent"],
                    "keywords": ["ultimate parent", "parent name", "parent company"]
                },
                "travel_volume": {
                    "description": "Expected travel volume or spend amount",
                    "examples": ["125000", "$250,000", "500000.00"],
                    "keywords": ["travel volume", "expected volume", "spend", "volume"]
                },
                "currency": {
                    "description": "Currency for the travel volume",
                    "examples": ["USD", "EUR", "GBP", "AUD"],
                    "keywords": ["currency", "volume currency", "curr"]
                }
            },
            "bt_opportunities": {
                "account_name": {
                    "description": "Account or company name for the opportunity",
                    "examples": ["Google EMEA", "Amazon International"],
                    "keywords": ["account name", "company name", "client"]
                },
                "parent_company": {
                    "description": "Ultimate parent company name",
                    "examples": ["Alphabet Inc - Ultimate Parent", "Amazon.com Inc"],
                    "keywords": ["ultimate parent", "parent name", "parent company"]
                },
                "opportunity_value": {
                    "description": "Expected travel volume value (often pre-converted to USD)",
                    "examples": ["1000000", "$750,000", "500000.00"],
                    "keywords": ["travel volume", "expected volume", "converted", "value"]
                },
                "stage": {
                    "description": "Opportunity pipeline stage",
                    "examples": ["1 - Propose", "2 - Negotiate", "Discovery"],
                    "keywords": ["stage", "pipeline", "sales stage"]
                }
            }
        }
    
    def map_columns_with_llm(self, columns: List[str], file_type: str, sample_data: Dict = None) -> Dict[str, str]:
        """Use LLM to map actual columns to schema fields."""
        if not self.llm_available:
            logger.warning("LLM not available, falling back to hardcoded mapping")
            return self._fallback_mapping(columns, file_type)
        
        schema = self.get_schema_definitions().get(file_type, {})
        if not schema:
            logger.error(f"No schema defined for file type: {file_type}")
            return {}
        
        # Prepare the prompt
        prompt = self._create_mapping_prompt(columns, schema, file_type, sample_data)
        
        try:
            client = openai.OpenAI(api_key=OPENAI_API_KEY)
            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are an expert data analyst. Map column headers to standardized schema fields based on semantic meaning. Return only valid JSON."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                max_tokens=1000
            )
            
            mapping_text = response.choices[0].message.content.strip()
            
            # Clean the JSON response (remove markdown formatting if present)
            clean_json = self._clean_llm_json_response(mapping_text)
            
            # Parse the JSON response
            try:
                mapping = json.loads(clean_json)
                logger.info(f"LLM mapped {len(mapping)} columns for {file_type}")
                return mapping
            except json.JSONDecodeError:
                logger.error(f"Failed to parse LLM response as JSON: {clean_json}")
                return self._fallback_mapping(columns, file_type)
                
        except Exception as e:
            logger.error(f"LLM mapping failed: {str(e)}")
            return self._fallback_mapping(columns, file_type)
    
    def _clean_llm_json_response(self, response_text: str) -> str:
        """Clean LLM response to extract valid JSON."""
        # Remove markdown code blocks
        if '```json' in response_text:
            # Extract content between ```json and ```
            start = response_text.find('```json') + 7
            end = response_text.find('```', start)
            if end != -1:
                response_text = response_text[start:end]
        elif '```' in response_text:
            # Handle plain ``` blocks
            start = response_text.find('```') + 3
            end = response_text.find('```', start)
            if end != -1:
                response_text = response_text[start:end]
        
        return response_text.strip()
    
    def _create_mapping_prompt(self, columns: List[str], schema: Dict, file_type: str, sample_data: Dict = None) -> str:
        """Create a detailed prompt for the LLM."""
        prompt = f"""
I need to map column headers from a {file_type.replace('_', ' ')} data file to a standardized schema.

AVAILABLE COLUMNS:
{json.dumps(columns, indent=2)}

SCHEMA TO MAP TO:
"""
        
        for field_name, field_info in schema.items():
            prompt += f"""
{field_name}:
  Description: {field_info['description']}
  Examples: {', '.join(field_info['examples'])}
  Keywords: {', '.join(field_info['keywords'])}
"""
        
        if sample_data:
            prompt += f"""
SAMPLE DATA VALUES:
{json.dumps(sample_data, indent=2)}
"""
        
        prompt += """
INSTRUCTIONS:
1. Map each schema field to the MOST APPROPRIATE column header
2. Use semantic meaning, not exact text matches
3. If no suitable column exists, omit that field from the response
4. Return ONLY a JSON object mapping schema_field -> column_header
5. Use the exact column header names from the AVAILABLE COLUMNS list

EXAMPLE RESPONSE FORMAT:
{
  "company_name": "Supplier",
  "contract_value": "Total Value",
  "currency": "Currency",
  "end_date": "End Date"
}

JSON RESPONSE:
"""
        return prompt
    
    def _fallback_mapping(self, columns: List[str], file_type: str) -> Dict[str, str]:
        """Fallback hardcoded mapping when LLM is not available."""
        columns_lower = [col.lower().strip() for col in columns]
        
        if file_type == 'raindrop_vendors':
            mapping = {}
            
            # Find company name column
            for col in columns:
                if any(keyword in col.lower() for keyword in ['supplier', 'vendor', 'company']):
                    if 'supplier' in col.lower():  # Prefer 'supplier' over generic 'company'
                        mapping['company_name'] = col
                        break
                    elif 'company_name' not in mapping:
                        mapping['company_name'] = col
            
            # Find individual supplier name column
            for col in columns:
                col_lower = col.lower().strip()
                if col_lower == 'name' and 'individual_supplier_name' not in mapping:
                    mapping['individual_supplier_name'] = col
                    break
            
            # Find other columns
            for col in columns:
                col_lower = col.lower().strip()
                if 'total value' in col_lower or (col_lower == 'value' and 'contract_value' not in mapping):
                    mapping['contract_value'] = col
                elif col_lower in ['currency', 'currency code']:
                    mapping['currency'] = col
                elif 'end date' in col_lower or 'expiry' in col_lower:
                    mapping['end_date'] = col
                elif 'term' in col_lower and 'mos' in col_lower:
                    mapping['contract_terms'] = col
            
            return mapping
        
        # Add other fallback mappings for different file types
        return {}
    
    def get_sample_data(self, df: pd.DataFrame, max_samples: int = 3) -> Dict:
        """Get sample data values for LLM context."""
        sample_data = {}
        
        for col in df.columns:
            # Get non-null sample values
            non_null_values = df[col].dropna()
            if len(non_null_values) > 0:
                samples = non_null_values.head(max_samples).astype(str).tolist()
                sample_data[col] = samples
        
        return sample_data
    
    def detect_file_type_with_llm(self, columns: List[str], filename: str, sample_data: Dict = None) -> str:
        """Use LLM to detect file type based on columns and content."""
        if not self.llm_available:
            return self._fallback_detect_file_type(columns, filename)
        
        schema_types = list(self.get_schema_definitions().keys())
        
        prompt = f"""
Analyze this data file and determine its type based on column headers and filename.

FILENAME: {filename}

COLUMNS: {json.dumps(columns, indent=2)}

POSSIBLE FILE TYPES:
- raindrop_vendors: Vendor contract data with supplier info, contract values, terms
- ege_customers: Customer travel budget data with parent companies  
- ege_opportunities: Sales opportunities with bookings values and stages
- bt_clients: Business travel client data with ultimate parents
- bt_opportunities: Business travel opportunity pipeline with stages

Return ONLY the file type (one of the options above) that best matches this data.
"""
        
        if sample_data:
            prompt += f"\nSAMPLE DATA: {json.dumps(sample_data, indent=2)}"
        
        try:
            client = openai.OpenAI(api_key=OPENAI_API_KEY)
            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a data classification expert. Analyze file structure and return only the file type."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                max_tokens=50
            )
            
            file_type = response.choices[0].message.content.strip().lower()
            
            if file_type in schema_types:
                logger.info(f"LLM detected file type: {file_type}")
                return file_type
            else:
                logger.warning(f"LLM returned unknown file type: {file_type}")
                return self._fallback_detect_file_type(columns, filename)
                
        except Exception as e:
            logger.error(f"LLM file type detection failed: {str(e)}")
            return self._fallback_detect_file_type(columns, filename)
    
    def _fallback_detect_file_type(self, columns: List[str], filename: str) -> str:
        """Fallback file type detection."""
        columns_lower = [col.lower().strip() for col in columns]
        column_string = ' '.join(columns_lower)
        filename_lower = filename.lower()
        
        # Use the existing hardcoded logic as fallback
        if ('ultimate parent account (read only)' in columns_lower and 
            'contracted annual travel budget' in column_string):
            return 'ege_customers'
        elif ('corporate gross bookings value' in column_string and 
              'stage' in columns_lower):
            return 'ege_opportunities'
        elif (('ultimate parent name' in columns_lower or 'opportunity name' in columns_lower) and 
              'expected total travel volume' in column_string and
              ('stage' in columns_lower or 'opportunity' in filename_lower or 'pipeline' in filename_lower)):
            return 'bt_opportunities'
        elif ('ultimate parent name' in columns_lower and 
              'expected total travel volume' in column_string and
              'bt type' in columns_lower):
            return 'bt_clients'
        elif (any(keyword in column_string for keyword in ['supplier', 'vendor', 'total value', 'contract']) or
              'raindrop' in filename_lower or 'contract' in filename_lower):
            return 'raindrop_vendors'
        
        return 'unknown'