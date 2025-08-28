"""Currency conversion module with session caching."""

import requests
import time
import logging
from typing import Dict, Optional
from src.config import CURRENCY_API_URL, CURRENCY_BACKUP_URL, CURRENCY_CACHE_DURATION

logger = logging.getLogger(__name__)

class CurrencyConverter:
    """Handles currency conversion with session-based caching."""
    
    def __init__(self):
        self.exchange_rates: Dict[str, float] = {}
        self.last_updated: Optional[float] = None
        self.base_currency = 'USD'
    
    def get_exchange_rates(self, force_refresh: bool = False) -> Dict[str, float]:
        """Fetch current exchange rates with caching."""
        current_time = time.time()
        
        # Check if cache is still valid
        if (not force_refresh and 
            self.exchange_rates and 
            self.last_updated and 
            current_time - self.last_updated < CURRENCY_CACHE_DURATION):
            return self.exchange_rates
        
        # Try primary API first
        try:
            logger.info("Fetching fresh exchange rates from primary API...")
            response = requests.get(CURRENCY_API_URL, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            
            # For exchangerate-api.com format
            if 'rates' in data:
                self.exchange_rates = data['rates']
                self.exchange_rates[self.base_currency] = 1.0  # Ensure base currency
                self.last_updated = current_time
                
                logger.info(f"Successfully fetched rates for {len(self.exchange_rates)} currencies")
                return self.exchange_rates
                
        except requests.RequestException as e:
            logger.warning(f"Primary API failed: {str(e)}, trying backup...")
            
            # Try backup API
            try:
                response = requests.get(CURRENCY_BACKUP_URL, timeout=15)
                response.raise_for_status()
                
                data = response.json()
                
                # For exchangerate.host format
                if data.get('success', True) and 'rates' in data:
                    self.exchange_rates = data['rates']
                    self.exchange_rates[self.base_currency] = 1.0
                    self.last_updated = current_time
                    
                    logger.info(f"Successfully fetched rates from backup API for {len(self.exchange_rates)} currencies")
                    return self.exchange_rates
                    
            except requests.RequestException as backup_e:
                logger.error(f"Backup API also failed: {str(backup_e)}")
        
        # Return cached rates if available
        if self.exchange_rates:
            logger.warning("Using cached exchange rates due to API failures")
            return self.exchange_rates
        
        # Use fallback rates with warning
        logger.error("Both APIs failed and no cache available. Using fallback rates!")
        fallback_rates = {
            'USD': 1.0,
            'EUR': 0.85,     # Approximate rates - should be updated regularly
            'GBP': 0.78,
            'JPY': 150.0,
            'CAD': 1.35,
            'AUD': 1.55,
            'CHF': 0.88,
            'CNY': 7.20,
            'INR': 83.0,
            'SGD': 1.34,
            'MXN': 17.5,
            'BRL': 5.8,
            'KRW': 1340.0,
            'ZAR': 18.5,
            'SEK': 10.8,
            'NOK': 10.9,
            'DKK': 6.9
        }
        
        self.exchange_rates = fallback_rates
        self.last_updated = current_time
        return fallback_rates
    
    def convert_to_usd(self, amount: float, from_currency: str) -> float:
        """Convert amount from given currency to USD."""
        if not amount or amount == 0:
            return 0.0
        
        # Normalize currency code
        from_currency = from_currency.upper().strip() if from_currency else 'USD'
        
        if from_currency == 'USD':
            return float(amount)
        
        # Get current rates
        rates = self.get_exchange_rates()
        
        if from_currency not in rates:
            logger.error(f"CRITICAL: Currency {from_currency} not found in rates!")
            logger.error(f"This could result in MAJOR financial discrepancies!")
            logger.error(f"Available currencies: {list(rates.keys())[:10]}...")  # Show first 10 only
            logger.error(f"ASSUMING {amount} {from_currency} = {amount} USD - THIS MAY BE WRONG!")
            return float(amount)  # This is dangerous but better than crashing
        
        # Convert to USD
        rate = rates[from_currency]
        if rate <= 0:
            logger.error(f"🚨 Invalid exchange rate for {from_currency}: {rate}")
            return float(amount)
        
        usd_amount = float(amount) / rate
        
        logger.debug(f"Converted {amount} {from_currency} to {usd_amount:.2f} USD (rate: {rate})")
        return round(usd_amount, 2)
    
    def convert_currency_column(self, df, amount_column: str, currency_column: str) -> list:
        """Convert a dataframe column from various currencies to USD."""
        converted_amounts = []
        
        for idx, row in df.iterrows():
            amount = row.get(amount_column, 0)
            currency = row.get(currency_column, 'USD')
            
            try:
                usd_amount = self.convert_to_usd(amount, currency)
                converted_amounts.append(usd_amount)
            except Exception as e:
                logger.error(f"Error converting row {idx}: {amount} {currency} - {str(e)}")
                converted_amounts.append(0.0)
        
        return converted_amounts
    
    def get_supported_currencies(self) -> list:
        """Get list of supported currency codes."""
        rates = self.get_exchange_rates()
        return sorted(rates.keys())
    
    def get_cache_status(self) -> dict:
        """Get information about the current cache status."""
        current_time = time.time()
        
        return {
            'cached_currencies': len(self.exchange_rates),
            'last_updated': self.last_updated,
            'cache_age_seconds': current_time - self.last_updated if self.last_updated else None,
            'cache_valid': (
                self.last_updated and 
                current_time - self.last_updated < CURRENCY_CACHE_DURATION
            ) if self.last_updated else False
        }