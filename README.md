# 🔍 AI Data Matching Tool

A powerful Streamlit web application for matching vendor contracts with client opportunities, featuring intelligent fuzzy matching, currency conversion, and comprehensive reporting.

## 🌟 Features

- **Two-Phase Matching Engine**: Exact string matching followed by AI-powered fuzzy matching
- **Multi-Source Data Processing**: Supports Raindrop contracts, EGE customers/opportunities, and BT clients/opportunities
- **Real-Time Currency Conversion**: Automatic conversion to USD with session caching
- **Interactive Visualizations**: Charts for relationship analysis, contract timelines, and spend comparisons
- **Professional Exports**: Generate HTML and Excel reports with branded styling
- **Enterprise UI**: Brand-consistent design with dark mode support

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- OpenAI API key for advanced features

### Docker Deployment (Recommended)

1. **Clone the project**
```bash
git clone https://github.com/cchen362/AI-Data-Matching.git
cd AI-Data-Matching
```

2. **Quick Deploy (Easiest)**
```bash
# Make scripts executable
chmod +x scripts/*.sh

# Run deployment script (will prompt for API key)
./scripts/deploy.sh
```

3. **Alternative: Manual Deploy**
```bash
# Option A: Set environment variable
export OPENAI_API_KEY="your-key-here"
docker-compose up -d

# Option B: Create .env file
echo "OPENAI_API_KEY=your-key-here" > .env
docker-compose up -d

# Option C: Use the interactive deployment
./scripts/deploy.bat  # Windows
./scripts/deploy.sh   # Linux/Mac
```

4. **Access the application**
- Open your browser to `http://localhost:8501`
- For production: `http://your-server-ip:8501`

### Traditional Python Setup (Alternative)

1. **Create and activate virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**
```bash
echo "OPENAI_API_KEY=your-key-here" > .env
```

4. **Start the application**
```bash
streamlit run app.py
```

## 📁 File Format Support

### Vendor Files (Raindrop Contracts)
- **Formats**: CSV, Excel (.xlsx, .xls)
- **Required columns**: Company Name, Total Value, Currency
- **Optional columns**: Contract Terms, End Date
- **Example**: `test_data/test_raindrop_contracts.csv`

### Client Files

#### EGE Active Customers
- **Key columns**: Account Name, Ultimate Parent Account, Contracted Annual Travel Budget
- **Auto-grouping**: By Ultimate Parent Account when available

#### EGE Active Opportunities  
- **Key columns**: Account Name, Ultimate Parent Account, Corporate Gross Bookings Value, Stage
- **Currency**: Already in USD

#### BT Active Clients
- **Key columns**: Account Name, Ultimate Parent Name, Expected Total Travel Volume
- **Auto-grouping**: By Ultimate Parent Name when available

#### BT Opportunity Pipeline
- **Key columns**: Account Name, Ultimate Parent Name, Expected Total Travel Volume, Stage
- **Status**: Opportunity (not active contract)

## 🔧 Usage Guide

### 1. Upload Files
- Use the sidebar to upload your vendor contracts file (required)
- Upload one or more client/opportunity files
- The system automatically detects file types based on column headers

### 2. Process Data
- Click "🚀 Process Files" to load and normalize your data
- Review the data overview showing total counts and spend amounts
- All currencies are automatically converted to USD

### 3. Find Matches
- Click "🔍 Find Matches" to run the matching engine
- View summary metrics showing total matches, exact vs fuzzy matches
- Apply filters to focus on specific match types or value ranges

### 4. Analyze Results
Explore the interactive charts:
- **Top Relationships**: Highest-value vendor-client relationships
- **Match Distribution**: Breakdown of exact vs fuzzy matches  
- **Contract Timeline**: Vendor contract expiry dates with risk analysis
- **Spend Comparison**: Vendor spend vs client spend analysis
- **Opportunity Stages**: Pipeline stage distribution
- **Summary Dashboard**: Key metrics overview

### 5. Export Reports
- Choose between "Current View" (filtered) or "Full Dataset"
- Generate Excel reports with multiple sheets and analysis
- Create branded HTML reports for stakeholder presentations

## 🎯 Matching Logic

### Phase 1: Exact Matching
- Case-insensitive string comparison
- Handles common business suffixes (Inc, Corp, Ltd, etc.)
- Strips extra whitespace and normalizes formatting

### Phase 2: Fuzzy Matching
- Uses RapidFuzz for similarity scoring
- Conservative threshold (85%) to avoid false matches
- Creates company name variants for better matching
- Flags results as "Fuzzy Match" for user awareness

### Data Consolidation
- Groups client data by Ultimate Parent Account/Name
- Sums contract values across multiple sources
- Preserves source attribution and opportunity stages

## 🎨 Customization

### Brand Colors
The application uses your brand color scheme defined in `src/config.py`:
- Primary Blue: #006FCF
- Accent Blue: #23A8D1  
- Secondary Navy: #00175A

### Matching Thresholds
Adjust matching sensitivity in `src/config.py`:
```python
EXACT_MATCH_THRESHOLD = 1.0        # Exact matches only
FUZZY_MATCH_THRESHOLD = 0.85       # Conservative fuzzy matching
```

## 🧪 Testing & Health Checks

### Docker Health Check
```bash
# Check container health
docker-compose ps

# Run health check manually
docker exec ai-data-matching python health_check.py

# View application logs
docker-compose logs -f
```

### Manual Testing
```bash
# Test with sample data (traditional setup)
python health_check.py
streamlit run app.py
```

Health checks cover:
- Dependencies verification
- Environment configuration
- Core module imports
- OpenAI API key validation

## 📊 Sample Data

Test the application with provided sample files in `test_data/`:
- `test_raindrop_contracts.csv` - 18 vendor contracts with variety
- `test_ege_customers.csv` - EGE customer data with parent groupings
- `test_bt_clients.csv` - BT client data with multi-currency examples
- `test_bt_opportunities.csv` - BT opportunities with stages

These samples include realistic scenarios like:
- Same companies with different subsidiary names (Adecco Group vs Adecco Services)
- Multiple currencies requiring conversion
- Parent account groupings for consolidation
- Opportunity pipeline stages

## 🔍 Troubleshooting

### Common Issues

**Currency conversion fails**
- Check internet connection for API access
- Verify unsupported currencies default to USD assumption
- Review fallback rates in `src/currency_converter.py`

**No matches found**
- Company names may be too different for fuzzy matching
- Try adjusting `FUZZY_MATCH_THRESHOLD` in config
- Check that both vendor and client files loaded correctly

**File upload errors** 
- Ensure files are in supported formats (CSV, XLSX, XLS)
- Verify column headers match expected patterns
- Check file size is under 50MB limit

**Charts not displaying**
- Ensure matching was performed successfully
- Check filter settings aren't excluding all data
- Verify Plotly charts have sufficient data points

### Performance Tips

- Use CSV format for faster loading of large files
- Filter results before generating charts for better performance
- Export smaller datasets for faster processing
- Clear browser cache if UI appears corrupted

## 🛠 Development

### Project Structure
```
AI-Data-Matching/
├── app.py                    # Main Streamlit application
├── Dockerfile               # Docker container configuration
├── docker-compose.yml       # Development deployment
├── docker-compose.prod.yml  # Production deployment
├── health_check.py          # Health check script
├── .env.example             # Environment template
├── src/
│   ├── config.py            # Configuration and constants
│   ├── data_processor.py    # File loading and processing
│   ├── currency_converter.py # Currency conversion
│   ├── matching_engine.py   # Two-phase matching logic
│   ├── charts.py            # Interactive visualizations
│   └── export_manager.py    # HTML and Excel exports
├── scripts/
│   ├── deploy.sh            # Deployment automation
│   ├── deploy.bat           # Windows deployment
│   ├── update-api-key.sh    # API key management
│   └── quick-deploy.sh      # Server deployment
├── test_data/               # Sample data files
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

### Docker Management
```bash
# Start application
docker-compose up -d

# Stop application  
docker-compose down

# View logs
docker-compose logs -f

# Restart after changes
docker-compose restart

# Update API key
./scripts/update-api-key.sh

# Production deployment
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Contributing
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality  
4. Run the test suite to ensure compatibility
5. Submit a pull request with description

## 📋 Requirements

### Core Dependencies
- **Streamlit** 1.37+: Web application framework
- **Pandas** 2.3+: Data manipulation and analysis
- **RapidFuzz** 3.13+: Fuzzy string matching
- **Plotly** 5.24+: Interactive charts and visualizations
- **OpenPyXL** 3.1+: Excel file handling
- **Jinja2** 3.1+: HTML template rendering
- **Requests** 2.32+: HTTP requests for currency API

### Optional Dependencies
- **OpenAI** 1.50+: For future LLM-powered features
- **python-dotenv** 1.0+: Environment variable management

## 📄 License

This project is proprietary software. All rights reserved.

## 🤝 Support

For questions or issues:
1. Check this README for common solutions
2. Review the test output for specific error details
3. Examine log output in the Streamlit console
4. Contact the development team for enterprise support

---

**Built with ❤️ for enterprise data analysis**