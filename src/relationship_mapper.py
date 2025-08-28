"""
Advanced relationship mapping for vendor-client relationships.
Handles many-to-one and one-to-many relationships properly.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class RelationshipMapper:
    """Maps complex vendor-client relationships with proper aggregation."""
    
    def __init__(self):
        self.relationship_cache = {}
    
    def create_consolidated_relationships(self, matching_results: pd.DataFrame) -> pd.DataFrame:
        """
        Create a consolidated view of vendor-client relationships.
        
        Key insight: 
        - Multiple vendor contracts per company (different services/regions)
        - Single client spend per ultimate parent company
        - Need many-to-one mapping display
        """
        if matching_results is None or len(matching_results) == 0:
            return pd.DataFrame()
        
        logger.info(f"Consolidating {len(matching_results)} individual matches")
        
        # Group by company name to create consolidated relationships
        consolidated = []
        
        for company_name, company_matches in matching_results.groupby('company_name'):
            
            # Consolidate vendor information (sum all contracts)
            vendor_contracts = []
            total_vendor_spend = 0
            vendor_currencies = set()
            earliest_end_date = None
            contract_terms = []
            
            for _, match in company_matches.iterrows():
                vendor_spend = float(match.get('vendor_spend_usd', 0))
                total_vendor_spend += vendor_spend
                
                if pd.notna(match.get('vendor_currency')):
                    vendor_currencies.add(str(match['vendor_currency']))
                
                # Track individual contracts for details
                if vendor_spend > 0:
                    contract_info = {
                        'spend': vendor_spend,
                        'currency': match.get('vendor_currency', 'USD'),
                        'end_date': match.get('vendor_contract_end_date'),
                        'terms': match.get('vendor_contract_terms_months', 'Not specified')
                    }
                    vendor_contracts.append(contract_info)
                
                # Find earliest contract end date
                if pd.notna(match.get('vendor_contract_end_date')):
                    try:
                        if isinstance(match['vendor_contract_end_date'], str):
                            end_date = pd.to_datetime(match['vendor_contract_end_date'])
                        else:
                            end_date = match['vendor_contract_end_date']
                        
                        if earliest_end_date is None or end_date < earliest_end_date:
                            earliest_end_date = end_date
                    except:
                        pass
                
                if pd.notna(match.get('vendor_contract_terms_months')):
                    contract_terms.append(str(match['vendor_contract_terms_months']))
            
            # Get client information (should be consistent across matches)
            first_match = company_matches.iloc[0]
            client_spend = float(first_match.get('client_spend_usd', 0))
            client_currency = first_match.get('client_currency', 'USD')
            client_sources = first_match.get('client_sources', 'N/A')
            opportunity_stages = first_match.get('opportunity_stages', None)
            
            # Determine relationship strength and type
            match_types = company_matches['match_type'].unique()
            match_quality = 'Exact' if 'exact' in match_types else 'Fuzzy'
            
            # Create consolidated relationship
            relationship = {
                'company_name': company_name,
                
                # Vendor side (aggregated)
                'vendor_contract_count': len(vendor_contracts),
                'vendor_total_spend_usd': total_vendor_spend,
                'vendor_currencies_used': ', '.join(sorted(vendor_currencies)) if vendor_currencies else 'USD',
                'vendor_earliest_end_date': earliest_end_date.strftime('%Y-%m-%d') if earliest_end_date else 'Not specified',
                'vendor_contract_terms': ', '.join(sorted(set(contract_terms))) if contract_terms else 'Not specified',
                'vendor_contracts_detail': vendor_contracts,
                
                # Client side (consolidated)
                'client_total_spend_usd': client_spend,
                'client_currency': client_currency,
                'client_sources': client_sources,
                'opportunity_stages': opportunity_stages,
                
                # Relationship metrics
                'total_relationship_value': total_vendor_spend + client_spend,
                'vendor_client_ratio': (total_vendor_spend / client_spend) if client_spend > 0 else float('inf'),
                'match_quality': match_quality,
                'relationship_type': self._classify_relationship(total_vendor_spend, client_spend, len(vendor_contracts))
            }
            
            consolidated.append(relationship)
        
        result_df = pd.DataFrame(consolidated)
        
        # Sort by total relationship value
        result_df = result_df.sort_values('total_relationship_value', ascending=False)
        
        logger.info(f"Created {len(result_df)} consolidated relationships")
        return result_df
    
    def _classify_relationship(self, vendor_spend: float, client_spend: float, contract_count: int) -> str:
        """Classify the type of vendor-client relationship."""
        
        if vendor_spend == 0 and client_spend > 0:
            return "Client Only"
        elif vendor_spend > 0 and client_spend == 0:
            return "Vendor Only"
        elif vendor_spend > 0 and client_spend > 0:
            ratio = vendor_spend / client_spend
            if ratio > 2:
                return "Major Vendor"
            elif ratio > 0.5:
                return "Balanced Partner"
            else:
                return "Major Client"
        else:
            return "Unknown"
    
    def create_detailed_breakdown(self, consolidated_df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """Create detailed breakdowns for drill-down analysis."""
        
        breakdowns = {}
        
        # Top relationships by value
        breakdowns['top_relationships'] = consolidated_df.head(20)[
            ['company_name', 'vendor_total_spend_usd', 'client_total_spend_usd', 
             'total_relationship_value', 'vendor_contract_count', 'match_quality']
        ].copy()
        
        # Vendor contract details (for companies with multiple contracts)
        multi_contract_companies = consolidated_df[consolidated_df['vendor_contract_count'] > 1]
        
        if len(multi_contract_companies) > 0:
            vendor_details = []
            
            for _, company in multi_contract_companies.iterrows():
                company_name = company['company_name']
                
                for i, contract in enumerate(company['vendor_contracts_detail']):
                    detail = {
                        'company_name': company_name,
                        'contract_number': i + 1,
                        'contract_spend_usd': contract['spend'],
                        'contract_currency': contract['currency'],
                        'contract_end_date': contract['end_date'],
                        'contract_terms': contract['terms']
                    }
                    vendor_details.append(detail)
            
            breakdowns['vendor_contract_details'] = pd.DataFrame(vendor_details)
        
        # Relationship type analysis
        relationship_summary = consolidated_df.groupby('relationship_type').agg({
            'company_name': 'count',
            'vendor_total_spend_usd': 'sum',
            'client_total_spend_usd': 'sum',
            'total_relationship_value': 'sum'
        }).round(2)
        relationship_summary.columns = ['Count', 'Total Vendor Spend', 'Total Client Spend', 'Total Value']
        breakdowns['relationship_types'] = relationship_summary
        
        # Currency analysis
        currency_issues = consolidated_df[
            consolidated_df['vendor_currencies_used'].str.contains(',|NOK|EUR|GBP', na=False)
        ][['company_name', 'vendor_currencies_used', 'vendor_total_spend_usd']].copy()
        
        if len(currency_issues) > 0:
            breakdowns['currency_conversion_issues'] = currency_issues
        
        return breakdowns
    
    def generate_relationship_summary(self, consolidated_df: pd.DataFrame) -> Dict:
        """Generate executive summary of relationships."""
        
        if len(consolidated_df) == 0:
            return {}
        
        total_companies = len(consolidated_df)
        total_vendor_spend = consolidated_df['vendor_total_spend_usd'].sum()
        total_client_spend = consolidated_df['client_total_spend_usd'].sum()
        total_relationship_value = consolidated_df['total_relationship_value'].sum()
        
        # Contract analysis
        total_contracts = consolidated_df['vendor_contract_count'].sum()
        companies_with_multiple_contracts = len(consolidated_df[consolidated_df['vendor_contract_count'] > 1])
        
        # Match quality
        exact_matches = len(consolidated_df[consolidated_df['match_quality'] == 'Exact'])
        fuzzy_matches = len(consolidated_df[consolidated_df['match_quality'] == 'Fuzzy'])
        
        # Relationship types
        relationship_breakdown = consolidated_df['relationship_type'].value_counts().to_dict()
        
        # Top relationships
        top_5_relationships = consolidated_df.head(5)[
            ['company_name', 'total_relationship_value']
        ].to_dict('records')
        
        summary = {
            'overview': {
                'total_companies': total_companies,
                'total_vendor_contracts': int(total_contracts),
                'companies_with_multiple_contracts': companies_with_multiple_contracts,
                'total_vendor_spend_usd': total_vendor_spend,
                'total_client_spend_usd': total_client_spend,
                'total_relationship_value_usd': total_relationship_value
            },
            'match_quality': {
                'exact_matches': exact_matches,
                'fuzzy_matches': fuzzy_matches,
                'match_accuracy': round(exact_matches / total_companies * 100, 1) if total_companies > 0 else 0
            },
            'relationship_types': relationship_breakdown,
            'top_relationships': top_5_relationships,
            'insights': self._generate_insights(consolidated_df)
        }
        
        return summary
    
    def _generate_insights(self, consolidated_df: pd.DataFrame) -> List[str]:
        """Generate business insights from the relationship data."""
        
        insights = []
        
        # Multi-contract insights
        multi_contract = consolidated_df[consolidated_df['vendor_contract_count'] > 1]
        if len(multi_contract) > 0:
            avg_contracts = multi_contract['vendor_contract_count'].mean()
            insights.append(
                f"{len(multi_contract)} companies have multiple vendor contracts "
                f"(avg {avg_contracts:.1f} contracts per company)"
            )
        
        # Spend ratio insights
        balanced_partners = consolidated_df[
            (consolidated_df['vendor_client_ratio'] >= 0.5) & 
            (consolidated_df['vendor_client_ratio'] <= 2.0)
        ]
        if len(balanced_partners) > 0:
            insights.append(f"{len(balanced_partners)} companies show balanced vendor-client relationships")
        
        # Currency conversion issues
        currency_issues = consolidated_df[
            consolidated_df['vendor_currencies_used'].str.contains(',|NOK|EUR|GBP', na=False)
        ]
        if len(currency_issues) > 0:
            insights.append(f"{len(currency_issues)} companies have currency conversion issues requiring attention")
        
        # High-value relationships
        high_value = consolidated_df[consolidated_df['total_relationship_value'] >= 1000000]
        if len(high_value) > 0:
            insights.append(f"{len(high_value)} relationships exceed $1M in total value")
        
        return insights