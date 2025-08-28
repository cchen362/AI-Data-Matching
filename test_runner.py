"""
Test runner and validation script for the AI Data Matching Tool.
Validates functionality with test data and provides comprehensive testing.
"""

import sys
import os
import pandas as pd
import logging
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.data_processor import DataProcessor
from src.currency_converter import CurrencyConverter
from src.matching_engine import MatchingEngine
from src.export_manager import create_excel_export, create_html_export

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TestRunner:
    """Comprehensive test runner for the AI Data Matching Tool."""
    
    def __init__(self):
        self.data_processor = DataProcessor()
        self.currency_converter = CurrencyConverter()
        self.matching_engine = MatchingEngine()
        self.test_data_path = Path("test_data")
        self.results = {}
        
    def run_all_tests(self):
        """Run all test suites."""
        logger.info("Starting comprehensive test suite for AI Data Matching Tool")
        
        # Test data loading and processing
        test_results = {}
        
        try:
            test_results['data_loading'] = self.test_data_loading()
            test_results['currency_conversion'] = self.test_currency_conversion()
            test_results['matching_engine'] = self.test_matching_engine()
            test_results['export_functionality'] = self.test_export_functionality()
            test_results['integration_test'] = self.test_full_integration()
            
            # Summary
            passed_tests = sum(1 for result in test_results.values() if result['passed'])
            total_tests = len(test_results)
            
            logger.info(f"Test Summary: {passed_tests}/{total_tests} test suites passed")
            
            if passed_tests == total_tests:
                logger.info("All tests passed! The application is ready for use.")
                return True
            else:
                logger.warning(f"{total_tests - passed_tests} test suite(s) failed. Check logs for details.")
                return False
                
        except Exception as e:
            logger.error(f"Critical error during testing: {str(e)}")
            return False
    
    def test_data_loading(self):
        """Test data loading and processing functionality."""
        logger.info("Testing data loading and processing...")
        
        try:
            # Test file loading
            test_files = [
                ("test_raindrop_contracts.csv", "raindrop"),
                ("test_ege_customers.csv", "ege_customers"),
                ("test_bt_clients.csv", "bt_clients"),
                ("test_bt_opportunities.csv", "bt_opportunities")
            ]
            
            loaded_files = {}
            
            for filename, expected_type in test_files:
                file_path = self.test_data_path / filename
                if file_path.exists():
                    df, detected_type = self.data_processor.load_and_detect_file(str(file_path))
                    loaded_files[expected_type] = df
                    
                    # Validate detection
                    if detected_type != expected_type and expected_type != "raindrop":
                        logger.warning(f"File type detection mismatch for {filename}: expected {expected_type}, got {detected_type}")
                    
                    logger.info(f"✅ Loaded {filename}: {len(df)} rows, detected as {detected_type}")
                else:
                    logger.error(f"❌ Test file not found: {filename}")
                    return {'passed': False, 'error': f'Missing test file: {filename}'}
            
            # Test processing functions
            if 'raindrop' in loaded_files:
                processed_vendors = self.data_processor.process_raindrop_contracts(loaded_files['raindrop'])
                logger.info(f"✅ Processed Raindrop contracts: {len(processed_vendors)} vendors")
            
            if 'ege_customers' in loaded_files:
                processed_ege = self.data_processor.process_ege_customers(loaded_files['ege_customers'])
                logger.info(f"✅ Processed EGE customers: {len(processed_ege)} companies")
            
            if 'bt_clients' in loaded_files:
                processed_bt = self.data_processor.process_bt_clients(loaded_files['bt_clients'])
                logger.info(f"✅ Processed BT clients: {len(processed_bt)} companies")
            
            if 'bt_opportunities' in loaded_files:
                processed_bt_opp = self.data_processor.process_bt_opportunities(loaded_files['bt_opportunities'])
                logger.info(f"✅ Processed BT opportunities: {len(processed_bt_opp)} companies")
            
            return {'passed': True, 'loaded_files': len(loaded_files)}
            
        except Exception as e:
            logger.error(f"❌ Data loading test failed: {str(e)}")
            return {'passed': False, 'error': str(e)}
    
    def test_currency_conversion(self):
        """Test currency conversion functionality."""
        logger.info("🔄 Testing currency conversion...")
        
        try:
            # Test basic conversion
            usd_amount = self.currency_converter.convert_to_usd(100, 'USD')
            if usd_amount != 100.0:
                return {'passed': False, 'error': 'USD to USD conversion failed'}
            
            # Test exchange rate fetching
            rates = self.currency_converter.get_exchange_rates()
            if not rates or 'USD' not in rates:
                return {'passed': False, 'error': 'Failed to fetch exchange rates'}
            
            logger.info(f"✅ Exchange rates fetched: {len(rates)} currencies available")
            
            # Test common conversions
            test_conversions = [
                (1000, 'EUR'),
                (1000, 'GBP'),
                (100000, 'JPY'),
                (1500, 'CAD')
            ]
            
            for amount, currency in test_conversions:
                usd_amount = self.currency_converter.convert_to_usd(amount, currency)
                if usd_amount > 0:
                    logger.info(f"✅ Converted {amount} {currency} to ${usd_amount:.2f} USD")
                else:
                    logger.warning(f"⚠️ Conversion resulted in 0: {amount} {currency}")
            
            # Test cache status
            cache_status = self.currency_converter.get_cache_status()
            logger.info(f"✅ Currency cache status: {cache_status['cached_currencies']} currencies cached")
            
            return {'passed': True, 'currencies_available': len(rates)}
            
        except Exception as e:
            logger.error(f"❌ Currency conversion test failed: {str(e)}")
            return {'passed': False, 'error': str(e)}
    
    def test_matching_engine(self):
        """Test the matching engine functionality."""
        logger.info("🔄 Testing matching engine...")
        
        try:
            # Create test dataframes
            vendors_df = pd.DataFrame({
                'company_name': ['Microsoft Corporation', 'IBM Corp', 'Adecco Group', 'Oracle Inc'],
                'total_value': [100000, 150000, 75000, 200000],
                'currency': ['USD', 'USD', 'USD', 'USD'],
                'source': ['raindrop'] * 4,
                'record_type': ['vendor'] * 4
            })
            
            clients_df = pd.DataFrame({
                'company_name': ['Microsoft Corporation', 'IBM International', 'Adecco Services', 'Google Inc'],
                'client_spend': [250000, 180000, 95000, 300000],
                'currency': ['USD', 'USD', 'USD', 'USD'],
                'source': ['test'] * 4,
                'record_type': ['client'] * 4
            })
            
            # Test matching
            results = self.matching_engine.match_vendors_to_clients(vendors_df, clients_df)
            
            if results is None or len(results) == 0:
                return {'passed': False, 'error': 'No matches found in test data'}
            
            # Validate results
            exact_matches = sum(results['match_type'] == 'exact')
            fuzzy_matches = sum(results['match_type'] == 'fuzzy')
            
            logger.info(f"✅ Matching results: {len(results)} total matches")
            logger.info(f"   - Exact matches: {exact_matches}")
            logger.info(f"   - Fuzzy matches: {fuzzy_matches}")
            
            # Test statistics
            stats = self.matching_engine.get_matching_statistics(vendors_df, results)
            logger.info(f"✅ Match rate: {stats['match_rate']}%")
            
            # Validate specific expected matches
            expected_exact_match = results[results['company_name'] == 'Microsoft Corporation']
            if len(expected_exact_match) > 0 and expected_exact_match.iloc[0]['match_type'] == 'exact':
                logger.info("✅ Microsoft Corporation exact match validated")
            else:
                logger.warning("⚠️ Expected exact match for Microsoft Corporation not found")
            
            return {
                'passed': True, 
                'total_matches': len(results),
                'exact_matches': exact_matches,
                'fuzzy_matches': fuzzy_matches,
                'match_rate': stats['match_rate']
            }
            
        except Exception as e:
            logger.error(f"❌ Matching engine test failed: {str(e)}")
            return {'passed': False, 'error': str(e)}
    
    def test_export_functionality(self):
        """Test export functionality."""
        logger.info("🔄 Testing export functionality...")
        
        try:
            # Create sample results data
            sample_results = pd.DataFrame({
                'company_name': ['Test Company A', 'Test Company B'],
                'vendor_spend_usd': [100000, 150000],
                'client_spend_usd': [200000, 250000],
                'total_relationship_value': [300000, 400000],
                'match_type': ['exact', 'fuzzy'],
                'match_score': [1.0, 0.87],
                'vendor_contract_end_date': ['2025-12-31', '2026-06-30'],
                'vendor_contract_terms_months': [12, 18],
                'client_sources': ['test_source', 'test_source'],
                'opportunity_stages': [None, 'Negotiation']
            })
            
            sample_processed_data = {
                'vendors': pd.DataFrame({
                    'company_name': ['Test Company A', 'Test Company B'],
                    'total_value_usd': [100000, 150000]
                }),
                'clients': pd.DataFrame({
                    'company_name': ['Test Company A', 'Test Company B'],
                    'client_spend': [200000, 250000]
                })
            }
            
            # Test Excel export
            excel_data = create_excel_export(sample_results, sample_processed_data)
            if len(excel_data) > 0:
                logger.info(f"✅ Excel export created: {len(excel_data)} bytes")
            else:
                return {'passed': False, 'error': 'Excel export produced empty data'}
            
            # Test HTML export
            html_data = create_html_export(sample_results, sample_processed_data)
            if len(html_data) > 0 and '<html' in html_data:
                logger.info(f"✅ HTML export created: {len(html_data)} characters")
            else:
                return {'passed': False, 'error': 'HTML export failed or invalid'}
            
            return {
                'passed': True,
                'excel_size': len(excel_data),
                'html_size': len(html_data)
            }
            
        except Exception as e:
            logger.error(f"❌ Export functionality test failed: {str(e)}")
            return {'passed': False, 'error': str(e)}
    
    def test_full_integration(self):
        """Test full integration with real test data."""
        logger.info("🔄 Testing full integration workflow...")
        
        try:
            # Load all test data
            vendor_file = self.test_data_path / "test_raindrop_contracts.csv"
            client_files = [
                self.test_data_path / "test_ege_customers.csv",
                self.test_data_path / "test_bt_clients.csv",
                self.test_data_path / "test_bt_opportunities.csv"
            ]
            
            # Process vendor data
            vendors_df, _ = self.data_processor.load_and_detect_file(str(vendor_file))
            processed_vendors = self.data_processor.process_raindrop_contracts(vendors_df)
            
            # Convert vendor currency
            processed_vendors['total_value_usd'] = self.currency_converter.convert_currency_column(
                processed_vendors, 'total_value', 'currency'
            )
            
            # Process client data
            client_dataframes = []
            for client_file in client_files:
                if client_file.exists():
                    df, detected_type = self.data_processor.load_and_detect_file(str(client_file))
                    
                    if detected_type == 'ege_customers':
                        processed_df = self.data_processor.process_ege_customers(df)
                    elif detected_type == 'bt_clients':
                        processed_df = self.data_processor.process_bt_clients(df)
                    elif detected_type == 'bt_opportunities':
                        processed_df = self.data_processor.process_bt_opportunities(df)
                    else:
                        continue
                    
                    # Convert currency
                    processed_df['client_spend_usd'] = self.currency_converter.convert_currency_column(
                        processed_df, 'client_spend', 'currency'
                    )
                    processed_df['client_spend'] = processed_df['client_spend_usd']
                    
                    client_dataframes.append(processed_df)
            
            # Consolidate client data
            consolidated_clients = self.matching_engine.consolidate_client_data(client_dataframes)
            
            # Perform matching
            matching_results = self.matching_engine.match_vendors_to_clients(
                processed_vendors, consolidated_clients
            )
            
            if matching_results is None or len(matching_results) == 0:
                return {'passed': False, 'error': 'Integration test produced no matches'}
            
            # Test exports with real data
            excel_export = create_excel_export(matching_results, {
                'vendors': processed_vendors,
                'clients': consolidated_clients
            })
            
            html_export = create_html_export(matching_results, {
                'vendors': processed_vendors,
                'clients': consolidated_clients
            })
            
            # Validate key expected matches
            expected_matches = [
                'Microsoft Corporation',
                'IBM',
                'Adecco',
                'Oracle Corporation'
            ]
            
            found_matches = []
            for expected in expected_matches:
                for _, match in matching_results.iterrows():
                    if expected.lower() in match['company_name'].lower():
                        found_matches.append(expected)
                        break
            
            logger.info(f"✅ Integration test completed:")
            logger.info(f"   - Processed vendors: {len(processed_vendors)}")
            logger.info(f"   - Consolidated clients: {len(consolidated_clients)}")
            logger.info(f"   - Total matches: {len(matching_results)}")
            logger.info(f"   - Expected matches found: {len(found_matches)}/{len(expected_matches)}")
            logger.info(f"   - Excel export size: {len(excel_export)} bytes")
            logger.info(f"   - HTML export size: {len(html_export)} characters")
            
            return {
                'passed': True,
                'vendors_processed': len(processed_vendors),
                'clients_consolidated': len(consolidated_clients),
                'total_matches': len(matching_results),
                'expected_matches_found': len(found_matches),
                'excel_export_size': len(excel_export),
                'html_export_size': len(html_export)
            }
            
        except Exception as e:
            logger.error(f"❌ Integration test failed: {str(e)}")
            return {'passed': False, 'error': str(e)}

def main():
    """Run the test suite."""
    print("AI Data Matching Tool - Test Runner")
    print("=" * 50)
    
    runner = TestRunner()
    success = runner.run_all_tests()
    
    if success:
        print("\n🎉 All tests passed! The application is ready for deployment.")
        print("\nTo run the application:")
        print("  streamlit run app.py")
        return 0
    else:
        print("\n❌ Some tests failed. Please check the logs and fix issues before deployment.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)