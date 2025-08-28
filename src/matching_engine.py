"""Two-phase company matching engine with exact and fuzzy matching."""

import pandas as pd
import numpy as np
from rapidfuzz import fuzz, process
from typing import Dict, List, Tuple, Optional, Set
import logging
from src.config import EXACT_MATCH_THRESHOLD, FUZZY_MATCH_THRESHOLD, MIN_MATCH_LENGTH

logger = logging.getLogger(__name__)

class MatchingEngine:
    """Handles two-phase company name matching between vendors and clients."""
    
    def __init__(self):
        self.exact_matches = {}
        self.fuzzy_matches = {}
        self.unmatched_vendors = []
        self.match_results = []
    
    def normalize_company_name(self, name: str) -> str:
        """Normalize company name for better matching."""
        if pd.isna(name) or not isinstance(name, str):
            return ""
        
        # Basic normalization
        normalized = name.strip().lower()
        
        # Remove common business suffixes for matching purposes
        suffixes_to_remove = [
            'inc', 'inc.', 'corp', 'corp.', 'ltd', 'ltd.', 'llc', 'llc.',
            'limited', 'corporation', 'incorporated', 'company', 'co.',
            'gmbh', 'ag', 'sa', 'nv', 'bv', 'srl', 'spa', 'plc'
        ]
        
        for suffix in suffixes_to_remove:
            if normalized.endswith(f' {suffix}'):
                normalized = normalized[:-len(suffix)-1].strip()
            elif normalized.endswith(f'.{suffix}'):
                normalized = normalized[:-len(suffix)-1].strip()
        
        # Remove extra whitespace
        normalized = ' '.join(normalized.split())
        
        return normalized
    
    def create_matching_variants(self, name: str) -> List[str]:
        """Create different variants of company name for matching."""
        if not name or len(name) < MIN_MATCH_LENGTH:
            return []
        
        variants = [name]  # Original name
        normalized = self.normalize_company_name(name)
        
        if normalized and normalized != name.lower():
            variants.append(normalized)
        
        # Add variant without common words
        common_words = ['the', 'and', '&', 'group', 'international', 'global', 'services']
        words = normalized.split()
        filtered_words = [w for w in words if w not in common_words]
        
        if len(filtered_words) > 0 and filtered_words != words:
            variants.append(' '.join(filtered_words))
        
        return list(set(variants))  # Remove duplicates
    
    def phase1_exact_matching(self, vendors_df: pd.DataFrame, clients_df: pd.DataFrame) -> Tuple[List[Dict], pd.DataFrame]:
        """Phase 1: Exact string matching (case-insensitive)."""
        logger.info("Starting Phase 1: Exact matching...")
        
        exact_matches = []
        unmatched_vendor_indices = []
        
        # Create lookup dictionary for clients
        client_lookup = {}
        for idx, client_row in clients_df.iterrows():
            client_name = client_row['company_name']
            variants = self.create_matching_variants(client_name)
            
            for variant in variants:
                if variant and len(variant) >= MIN_MATCH_LENGTH:
                    if variant not in client_lookup:
                        client_lookup[variant] = []
                    client_lookup[variant].append({
                        'original_name': client_name,
                        'data': client_row.to_dict()
                    })
        
        # Match vendors against clients
        for vendor_idx, vendor_row in vendors_df.iterrows():
            vendor_name = vendor_row['company_name']
            vendor_variants = self.create_matching_variants(vendor_name)
            
            match_found = False
            for variant in vendor_variants:
                if variant in client_lookup:
                    # Found exact match
                    for client_match in client_lookup[variant]:
                        match = {
                            'vendor_name': vendor_name,
                            'client_name': client_match['original_name'],
                            'vendor_data': vendor_row.to_dict(),
                            'client_data': client_match['data'],
                            'match_type': 'exact',
                            'match_score': 1.0,
                            'match_variant': variant
                        }
                        exact_matches.append(match)
                        match_found = True
                        break
                
                if match_found:
                    break
            
            if not match_found:
                unmatched_vendor_indices.append(vendor_idx)
        
        # Create DataFrame of unmatched vendors for Phase 2
        unmatched_vendors_df = vendors_df.iloc[unmatched_vendor_indices].copy()
        
        logger.info(f"Phase 1 complete: {len(exact_matches)} exact matches found, {len(unmatched_vendors_df)} vendors remaining")
        
        return exact_matches, unmatched_vendors_df
    
    def phase2_fuzzy_matching(self, unmatched_vendors_df: pd.DataFrame, clients_df: pd.DataFrame) -> List[Dict]:
        """Phase 2: Fuzzy matching for remaining vendors."""
        logger.info("Starting Phase 2: Fuzzy matching...")
        
        if len(unmatched_vendors_df) == 0:
            logger.info("No unmatched vendors for Phase 2")
            return []
        
        fuzzy_matches = []
        
        # Prepare client names for fuzzy matching
        client_names = []
        client_lookup = {}
        
        for idx, client_row in clients_df.iterrows():
            client_name = client_row['company_name']
            variants = self.create_matching_variants(client_name)
            
            for variant in variants:
                if variant and len(variant) >= MIN_MATCH_LENGTH:
                    client_names.append(variant)
                    client_lookup[variant] = {
                        'original_name': client_name,
                        'data': client_row.to_dict()
                    }
        
        # Remove duplicates while preserving order
        unique_client_names = list(dict.fromkeys(client_names))
        
        logger.info(f"Fuzzy matching {len(unmatched_vendors_df)} vendors against {len(unique_client_names)} client variants")
        
        # Fuzzy match each unmatched vendor
        for vendor_idx, vendor_row in unmatched_vendors_df.iterrows():
            vendor_name = vendor_row['company_name']
            
            if not vendor_name or len(vendor_name) < MIN_MATCH_LENGTH:
                continue
            
            vendor_variants = self.create_matching_variants(vendor_name)
            
            best_match = None
            best_score = 0
            
            for vendor_variant in vendor_variants:
                if not vendor_variant:
                    continue
                
                # Use rapidfuzz to find best matches
                matches = process.extract(
                    vendor_variant,
                    unique_client_names,
                    scorer=fuzz.ratio,
                    limit=3
                )
                
                for match_name, score, _ in matches:
                    score_normalized = score / 100.0  # Convert to 0-1 scale
                    
                    if score_normalized >= FUZZY_MATCH_THRESHOLD and score_normalized > best_score:
                        best_match = match_name
                        best_score = score_normalized
            
            # If we found a good match, add it
            if best_match and best_score >= FUZZY_MATCH_THRESHOLD:
                client_info = client_lookup[best_match]
                
                match = {
                    'vendor_name': vendor_name,
                    'client_name': client_info['original_name'],
                    'vendor_data': vendor_row.to_dict(),
                    'client_data': client_info['data'],
                    'match_type': 'fuzzy',
                    'match_score': best_score,
                    'match_variant': best_match
                }
                fuzzy_matches.append(match)
        
        logger.info(f"Phase 2 complete: {len(fuzzy_matches)} fuzzy matches found")
        
        return fuzzy_matches
    
    def consolidate_client_data(self, clients_dfs: List[pd.DataFrame]) -> pd.DataFrame:
        """Consolidate multiple client dataframes, summing values for same companies."""
        logger.info(f"Consolidating {len(clients_dfs)} client datasets...")
        
        if not clients_dfs:
            return pd.DataFrame()
        
        # Combine all client dataframes
        all_clients = pd.concat(clients_dfs, ignore_index=True)
        
        # Group by company name and consolidate
        consolidated = []
        
        for company_name, group in all_clients.groupby('company_name'):
            # Sum client spend across all sources
            total_spend = group['client_spend'].sum()
            
            # Collect all currencies (should be USD after conversion)
            currencies = group['currency'].unique()
            currency = currencies[0] if len(currencies) == 1 else 'USD'
            
            # Collect sources
            sources = group['source'].unique().tolist()
            
            # Collect record types
            record_types = group['record_type'].unique().tolist()
            
            # Handle opportunity stages
            stages = group['stage'].dropna().unique().tolist() if 'stage' in group.columns else []
            
            # Handle contract types
            contract_types = group['contract_type'].dropna().unique().tolist() if 'contract_type' in group.columns else []
            
            consolidated_record = {
                'company_name': company_name,
                'client_spend': total_spend,
                'currency': currency,
                'sources': ', '.join(sources),
                'record_types': ', '.join(record_types),
                'stages': ', '.join(stages) if stages else None,
                'contract_types': ', '.join(contract_types) if contract_types else None,
                'source_count': len(sources)
            }
            
            consolidated.append(consolidated_record)
        
        consolidated_df = pd.DataFrame(consolidated)
        logger.info(f"Consolidated to {len(consolidated_df)} unique client companies")
        
        return consolidated_df
    
    def match_vendors_to_clients(self, vendors_df: pd.DataFrame, clients_df: pd.DataFrame) -> pd.DataFrame:
        """Main matching function that combines both phases."""
        logger.info(f"Starting vendor-client matching: {len(vendors_df)} vendors vs {len(clients_df)} clients")
        
        # Phase 1: Exact matching
        exact_matches, unmatched_vendors = self.phase1_exact_matching(vendors_df, clients_df)
        
        # Phase 2: Fuzzy matching
        fuzzy_matches = self.phase2_fuzzy_matching(unmatched_vendors, clients_df)
        
        # Combine all matches
        all_matches = exact_matches + fuzzy_matches
        
        if not all_matches:
            logger.info("No matches found")
            return pd.DataFrame()
        
        # Convert to DataFrame
        matches_df = pd.DataFrame(all_matches)
        
        # Create consolidated output
        consolidated_matches = []
        
        for _, match in matches_df.iterrows():
            vendor_data = match['vendor_data']
            client_data = match['client_data']
            
            consolidated_match = {
                'company_name': match['vendor_name'],
                'vendor_spend_usd': vendor_data.get('total_value', 0),
                'vendor_currency': vendor_data.get('currency', 'N/A'),
                'vendor_contract_end_date': vendor_data.get('end_date', 'Not specified'),
                'vendor_contract_terms_months': vendor_data.get('terms_months', 'Not specified'),
                'client_spend_usd': client_data.get('client_spend', 0),
                'client_currency': client_data.get('currency', 'USD'),
                'client_sources': client_data.get('sources', client_data.get('source', 'N/A')),
                'client_record_types': client_data.get('record_types', client_data.get('record_type', 'N/A')),
                'opportunity_stages': client_data.get('stages', client_data.get('stage', None)),
                'match_type': match['match_type'],
                'match_score': round(match['match_score'], 3),
                'total_relationship_value': (
                    float(vendor_data.get('total_value', 0)) + 
                    float(client_data.get('client_spend', 0))
                )
            }
            
            consolidated_matches.append(consolidated_match)
        
        result_df = pd.DataFrame(consolidated_matches)
        
        # Sort by total relationship value descending
        result_df = result_df.sort_values('total_relationship_value', ascending=False)
        
        logger.info(f"Matching complete: {len(result_df)} total matches found")
        logger.info(f"Exact matches: {sum(result_df['match_type'] == 'exact')}")
        logger.info(f"Fuzzy matches: {sum(result_df['match_type'] == 'fuzzy')}")
        
        return result_df
    
    def get_matching_statistics(self, vendors_df: pd.DataFrame, result_df: pd.DataFrame) -> Dict:
        """Generate matching statistics."""
        total_vendors = len(vendors_df)
        matched_vendors = len(result_df)
        unmatched_vendors = total_vendors - matched_vendors
        
        exact_matches = sum(result_df['match_type'] == 'exact') if len(result_df) > 0 else 0
        fuzzy_matches = sum(result_df['match_type'] == 'fuzzy') if len(result_df) > 0 else 0
        
        total_vendor_spend = result_df['vendor_spend_usd'].sum() if len(result_df) > 0 else 0
        total_client_spend = result_df['client_spend_usd'].sum() if len(result_df) > 0 else 0
        
        return {
            'total_vendors': total_vendors,
            'matched_vendors': matched_vendors,
            'unmatched_vendors': unmatched_vendors,
            'match_rate': round(matched_vendors / total_vendors * 100, 1) if total_vendors > 0 else 0,
            'exact_matches': exact_matches,
            'fuzzy_matches': fuzzy_matches,
            'total_vendor_spend_usd': total_vendor_spend,
            'total_client_spend_usd': total_client_spend,
            'total_relationship_value_usd': total_vendor_spend + total_client_spend
        }