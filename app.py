"""
AI Data Matching Tool - Vendor-Client Matching & Analysis
A Streamlit application for matching vendor contracts with client opportunities.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import logging
from datetime import datetime
import io
import base64
from pathlib import Path

# Import custom modules
from src.data_processor import DataProcessor
from src.currency_converter import CurrencyConverter
from src.matching_engine import MatchingEngine
from src.relationship_mapper import RelationshipMapper
from src.charts import (
    create_top_matches_chart, create_match_type_distribution,
    create_contract_expiry_timeline, create_spend_comparison_chart,
    create_opportunity_stages_chart, create_summary_metrics_chart
)
from src.export_manager import create_excel_export, create_html_export, get_download_link
from src.config import BRAND_COLORS, SUPPORTED_FORMATS, MAX_FILE_SIZE_MB

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="AI Data Matching Tool",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

def inject_custom_css():
    """Inject custom CSS for branding and dark mode support."""
    st.markdown(f"""
    <style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Root variables for light and dark themes */
    :root {{
        --primary-color: {BRAND_COLORS['primary']};
        --primary-70: {BRAND_COLORS['primary_70']};
        --primary-35: {BRAND_COLORS['primary_35']};
        --secondary-color: {BRAND_COLORS['secondary']};
        --accent-color: {BRAND_COLORS['accent']};
        --text-color: {BRAND_COLORS['text']};
        --background-color: {BRAND_COLORS['background']};
        --success-color: {BRAND_COLORS['success']};
        --warning-color: {BRAND_COLORS['warning']};
        --error-color: {BRAND_COLORS['error']};
    }}
    
    /* Dark mode variables */
    @media (prefers-color-scheme: dark) {{
        :root {{
            --text-color: #FFFFFF;
            --background-color: #0E1117;
            --surface-color: #262730;
        }}
    }}
    
    /* Global styles */
    .stApp {{
        font-family: 'Inter', sans-serif;
    }}
    
    /* Header styling */
    .main-header {{
        background: linear-gradient(90deg, var(--primary-color) 0%, var(--accent-color) 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
    }}
    
    .main-header h1 {{
        margin: 0;
        font-size: 2.5rem;
        font-weight: 700;
        text-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }}
    
    .main-header p {{
        margin: 0.5rem 0 0 0;
        font-size: 1.1rem;
        opacity: 0.9;
    }}
    
    /* Metric cards */
    .metric-card {{
        background: var(--background-color);
        border: 2px solid var(--primary-35);
        border-radius: 8px;
        padding: 1.5rem;
        text-align: center;
        box-shadow: 0 2px 10px rgba(0, 111, 207, 0.1);
    }}
    
    .metric-value {{
        font-size: 2rem;
        font-weight: 700;
        color: var(--primary-color);
        margin-bottom: 0.5rem;
    }}
    
    .metric-label {{
        font-size: 0.9rem;
        color: var(--text-color);
        opacity: 0.7;
        text-transform: uppercase;
        letter-spacing: 1px;
    }}
    
    /* File upload area */
    .upload-section {{
        border: 2px dashed var(--primary-35);
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        margin: 1rem 0;
        background: var(--primary-35);
        background-opacity: 0.05;
    }}
    
    /* Status indicators */
    .status-exact {{
        background-color: var(--success-color);
        color: white;
        padding: 0.2rem 0.8rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 500;
    }}
    
    .status-fuzzy {{
        background-color: var(--warning-color);
        color: var(--secondary-color);
        padding: 0.2rem 0.8rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 500;
    }}
    
    /* Button styling */
    .stButton > button {{
        background: linear-gradient(90deg, var(--primary-color), var(--accent-color));
        color: white;
        border: none;
        border-radius: 6px;
        padding: 0.5rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }}
    
    .stButton > button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(0, 111, 207, 0.3);
    }}
    
    /* Sidebar styling */
    .css-1d391kg {{
        background-color: var(--background-color);
    }}
    
    /* Progress bar */
    .stProgress > div > div > div > div {{
        background: linear-gradient(90deg, var(--primary-color), var(--accent-color));
    }}
    
    /* Dataframe styling */
    .dataframe {{
        border: 1px solid var(--primary-35);
        border-radius: 8px;
    }}
    
    /* Dark mode specific adjustments */
    @media (prefers-color-scheme: dark) {{
        .metric-card {{
            background: var(--surface-color, #262730);
            border-color: var(--primary-70);
        }}
        
        .upload-section {{
            background: var(--surface-color, #262730);
            border-color: var(--primary-70);
        }}
    }}
    
    /* Hide streamlit branding */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
    
    </style>
    """, unsafe_allow_html=True)

def show_header():
    """Display the main application header."""
    st.markdown("""
    <div class="main-header">
        <h1>🔍 AI Data Matching Tool</h1>
        <p>Vendor-Client Matching & Analysis Platform</p>
    </div>
    """, unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables."""
    if 'processed_data' not in st.session_state:
        st.session_state.processed_data = {}
    if 'matching_results' not in st.session_state:
        st.session_state.matching_results = None
    if 'currency_converter' not in st.session_state:
        st.session_state.currency_converter = CurrencyConverter()
    if 'data_processor' not in st.session_state:
        st.session_state.data_processor = DataProcessor()
    if 'matching_engine' not in st.session_state:
        st.session_state.matching_engine = MatchingEngine()
    if 'relationship_mapper' not in st.session_state:
        st.session_state.relationship_mapper = RelationshipMapper()

def handle_file_upload():
    """Handle simplified file upload with intelligent detection."""
    st.sidebar.header("📁 Upload Files")
    
    st.sidebar.markdown("""
    🤖 **Smart Upload**: Upload all your files and our AI will automatically 
    detect whether they contain vendor contracts, client data, or opportunities!
    """)
    
    # Single unified upload section
    uploaded_files = st.sidebar.file_uploader(
        "Upload your data files",
        type=['csv', 'xlsx', 'xls'],
        accept_multiple_files=True,
        help="Upload vendor contracts, client data, and opportunity files. The system will automatically detect file types based on column headers."
    )
    
    # Organize files based on detected type
    vendor_file = None
    client_files = {}
    
    if uploaded_files:
        st.sidebar.markdown("### 🔍 File Detection Results")
        
        for uploaded_file in uploaded_files:
            # Here we would use the existing LLM detection logic
            # For now, let's provide a simple manual selection as fallback
            file_type = st.sidebar.selectbox(
                f"File type for '{uploaded_file.name}':",
                ["Auto-detect", "Vendor Contracts", "EGE Customers", "EGE Opportunities", "BT Clients", "BT Opportunities"],
                key=f"type_{uploaded_file.name}"
            )
            
            if file_type == "Vendor Contracts":
                vendor_file = uploaded_file
                st.sidebar.success(f"✓ {uploaded_file.name} → Vendor Contracts")
            elif file_type == "EGE Customers":
                client_files['ege_customers'] = uploaded_file
                st.sidebar.success(f"✓ {uploaded_file.name} → EGE Customers")
            elif file_type == "EGE Opportunities":
                client_files['ege_opportunities'] = uploaded_file
                st.sidebar.success(f"✓ {uploaded_file.name} → EGE Opportunities")
            elif file_type == "BT Clients":
                client_files['bt_clients'] = uploaded_file
                st.sidebar.success(f"✓ {uploaded_file.name} → BT Clients")
            elif file_type == "BT Opportunities":
                client_files['bt_opportunities'] = uploaded_file
                st.sidebar.success(f"✓ {uploaded_file.name} → BT Opportunities")
            elif file_type == "Auto-detect":
                st.sidebar.info(f"🔍 {uploaded_file.name} → Will be auto-detected when processed")
    
    return vendor_file, client_files

def process_uploaded_files(vendor_file, client_files):
    """Process uploaded files and return processed dataframes."""
    processed_data = {}
    
    with st.spinner("Processing files..."):
        progress_bar = st.progress(0)
        total_files = 1 + len(client_files)
        current_file = 0
        
        # Process vendor file
        if vendor_file:
            try:
                # Use BytesIO to avoid temporary files
                import io
                
                # Read file content into BytesIO
                file_buffer = io.BytesIO(vendor_file.getbuffer())
                
                # Get file extension
                file_ext = vendor_file.name.split('.')[-1].lower()
                
                # Load directly from buffer
                if file_ext == 'csv':
                    df = pd.read_csv(file_buffer, encoding='utf-8')
                elif file_ext in ['xlsx', 'xls']:
                    df = pd.read_excel(file_buffer)
                else:
                    st.error(f"Unsupported file format: {file_ext}")
                    return None
                
                # Clean column names
                df.columns = df.columns.astype(str).str.strip()
                
                # Detect and process
                file_type = st.session_state.data_processor.detect_file_type(df, vendor_file.name)
                processed_vendors = st.session_state.data_processor.process_raindrop_contracts(df)
                
                # Convert to USD
                if 'total_value' in processed_vendors.columns and 'currency' in processed_vendors.columns:
                    processed_vendors['total_value_usd'] = st.session_state.currency_converter.convert_currency_column(
                        processed_vendors, 'total_value', 'currency'
                    )
                else:
                    processed_vendors['total_value_usd'] = 0
                
                processed_data['vendors'] = processed_vendors
                
                current_file += 1
                progress_bar.progress(current_file / total_files)
                
            except Exception as e:
                st.error(f"Error processing vendor file: {str(e)}")
                return None
        
        # Process client files
        client_dataframes = []
        
        for file_key, uploaded_file in client_files.items():
            try:
                # Use BytesIO to avoid temporary files
                file_buffer = io.BytesIO(uploaded_file.getbuffer())
                
                # Get file extension
                file_ext = uploaded_file.name.split('.')[-1].lower()
                
                # Load directly from buffer
                if file_ext == 'csv':
                    df = pd.read_csv(file_buffer, encoding='utf-8')
                elif file_ext in ['xlsx', 'xls']:
                    # Try different skip_rows to handle Excel files with header information
                    df = None
                    for skip_rows in [0, 5, 10, 15, 20, 25]:
                        try:
                            temp_df = pd.read_excel(file_buffer, skiprows=skip_rows)
                            # Look for meaningful column headers
                            if any(pd.notna(col) and any(keyword in str(col).lower() 
                                   for keyword in ['ultimate', 'parent', 'account', 'opportunity', 'stage', 'volume']) 
                                   for col in temp_df.columns):
                                df = temp_df
                                st.info(f"Found data headers at row {skip_rows + 1} in {uploaded_file.name}")
                                break
                            file_buffer.seek(0)  # Reset buffer for next attempt
                        except:
                            file_buffer.seek(0)  # Reset buffer
                            continue
                    
                    # If no good headers found, use the first attempt
                    if df is None:
                        file_buffer.seek(0)
                        df = pd.read_excel(file_buffer)
                else:
                    st.warning(f"Unsupported file format for {uploaded_file.name}: {file_ext}")
                    continue
                
                # Clean column names
                df.columns = df.columns.astype(str).str.strip()
                
                # Detect file type
                detected_type = st.session_state.data_processor.detect_file_type(df, uploaded_file.name)
                
                # Process based on file type
                if detected_type == 'ege_customers':
                    processed_df = st.session_state.data_processor.process_ege_customers(df)
                elif detected_type == 'ege_opportunities':
                    processed_df = st.session_state.data_processor.process_ege_opportunities(df)
                elif detected_type == 'bt_clients':
                    processed_df = st.session_state.data_processor.process_bt_clients(df)
                elif detected_type == 'bt_opportunities':
                    processed_df = st.session_state.data_processor.process_bt_opportunities(df)
                else:
                    st.warning(f"Could not detect type for {uploaded_file.name} (detected as: {detected_type}), skipping...")
                    continue
                
                # Convert to USD
                if 'client_spend' in processed_df.columns:
                    processed_df['client_spend_usd'] = st.session_state.currency_converter.convert_currency_column(
                        processed_df, 'client_spend', 'currency'
                    )
                    processed_df['client_spend'] = processed_df['client_spend_usd']  # Replace original with USD
                
                client_dataframes.append(processed_df)
                
                current_file += 1
                progress_bar.progress(current_file / total_files)
                
            except Exception as e:
                st.error(f"Error processing {uploaded_file.name}: {str(e)}")
                continue
        
        # Consolidate client data
        if client_dataframes:
            consolidated_clients = st.session_state.matching_engine.consolidate_client_data(client_dataframes)
            processed_data['clients'] = consolidated_clients
        
        progress_bar.progress(1.0)
    
    return processed_data

def show_data_overview(processed_data):
    """Display overview of processed data with meaningful business metrics."""
    st.subheader("📊 Data Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    if 'vendors' in processed_data:
        vendors_df = processed_data['vendors']
        unique_vendors = vendors_df['company_name'].nunique() if 'company_name' in vendors_df.columns else len(vendors_df)
        total_contracts = len(vendors_df)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{unique_vendors:,}</div>
                <div class="metric-label">Unique Vendors</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{total_contracts:,}</div>
                <div class="metric-label">Total Contracts</div>
            </div>
            """, unsafe_allow_html=True)
    
    if 'clients' in processed_data:
        clients_df = processed_data['clients']
        unique_clients = clients_df['company_name'].nunique() if 'company_name' in clients_df.columns else len(clients_df)
        
        # Count active clients vs opportunities
        active_clients = 0
        opportunities = 0
        if 'record_type' in clients_df.columns:
            active_clients = len(clients_df[clients_df['record_type'] == 'active'])
            opportunities = len(clients_df[clients_df['record_type'] == 'opportunity'])
        
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{unique_clients:,}</div>
                <div class="metric-label">Unique Companies</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            if active_clients + opportunities > 0:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{active_clients:,} / {opportunities:,}</div>
                    <div class="metric-label">Active / Opportunities</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                total_records = len(clients_df)
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{total_records:,}</div>
                    <div class="metric-label">Total Records</div>
                </div>
                """, unsafe_allow_html=True)

def perform_matching(processed_data):
    """Perform vendor-client matching."""
    if 'vendors' not in processed_data or 'clients' not in processed_data:
        st.warning("Please upload both vendor and client files to perform matching.")
        return None
    
    vendors_df = processed_data['vendors']
    clients_df = processed_data['clients']
    
    with st.spinner("Performing vendor-client matching..."):
        progress_bar = st.progress(0)
        
        # Update progress
        progress_bar.progress(0.3)
        
        # Perform matching
        raw_matching_results = st.session_state.matching_engine.match_vendors_to_clients(
            vendors_df, clients_df
        )
        
        progress_bar.progress(0.8)
        
        # Create consolidated relationships
        if raw_matching_results is not None and len(raw_matching_results) > 0:
            consolidated_relationships = st.session_state.relationship_mapper.create_consolidated_relationships(
                raw_matching_results
            )
            
            # Store both raw and consolidated results
            matching_results = {
                'raw_matches': raw_matching_results,
                'consolidated_relationships': consolidated_relationships,
                'summary': st.session_state.relationship_mapper.generate_relationship_summary(consolidated_relationships),
                'breakdowns': st.session_state.relationship_mapper.create_detailed_breakdown(consolidated_relationships)
            }
        else:
            matching_results = None
        
        progress_bar.progress(1.0)
    
    return matching_results

def display_matching_results(matching_results):
    """Display clean, user-focused matching results."""
    if matching_results is None:
        st.warning("No matches found between vendors and clients.")
        return
    
    consolidated_df = matching_results['consolidated_relationships']
    
    if len(consolidated_df) == 0:
        st.warning("No relationships found between vendors and clients.")
        return
    
    st.subheader("🎯 Company Relationships")
    
    # Clean summary metrics - focus on business value
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{len(consolidated_df):,}</div>
            <div class="metric-label">Companies Found</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        companies_with_multiple = len(consolidated_df[consolidated_df['vendor_contract_count'] > 1])
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{companies_with_multiple:,}</div>
            <div class="metric-label">Multi-Contract Companies</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        avg_relationship_value = consolidated_df['total_relationship_value'].mean()
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">${avg_relationship_value:,.0f}</div>
            <div class="metric-label">Avg Relationship Value</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Create high-level overview for drill-down
    st.subheader("📋 Company Matches")
    
    # Create high-level overview table for drill-down
    overview_df = consolidated_df[[
        'company_name', 
        'vendor_contract_count',
        'vendor_total_spend_usd', 
        'vendor_earliest_end_date',
        'client_total_spend_usd',
        'client_sources'
    ]].copy()
    
    # Format for display
    overview_df['vendor_total_spend_usd'] = overview_df['vendor_total_spend_usd'].apply(lambda x: f"${x:,.0f}")
    overview_df['client_total_spend_usd'] = overview_df['client_total_spend_usd'].apply(lambda x: f"${x:,.0f}")
    
    # Rename columns for better display
    overview_df = overview_df.rename(columns={
        'company_name': 'Company Name',
        'vendor_contract_count': 'Contract Count', 
        'vendor_total_spend_usd': 'Vendor Spend (USD)',
        'vendor_earliest_end_date': 'Earliest End Date',
        'client_total_spend_usd': 'Client Spend (USD)',
        'client_sources': 'Client Sources'
    })
    
    # Add simple search
    search_company = st.text_input(
        "🔍 Search Companies", 
        placeholder="Type to search companies..."
    )
    
    # Apply search filter
    filtered_df = overview_df.copy()
    if search_company:
        filtered_df = filtered_df[filtered_df['Company Name'].str.contains(search_company, case=False, na=False)]
    
    # Display overview table
    st.dataframe(filtered_df, width='stretch', height=400)
    
    st.info(f"💡 Click on any company name below to see detailed breakdown")
    
    # Company selection for drill-down
    if not filtered_df.empty:
        selected_company = st.selectbox(
            "Select company for detailed view:",
            options=["Select a company..."] + sorted(consolidated_df['company_name'].unique().tolist()),
            index=0
        )
        
        if selected_company != "Select a company...":
            display_company_details(consolidated_df, selected_company, matching_results.get('raw_matches'))
    
    st.info(f"Showing {len(filtered_results)} of {len(matching_results)} total matches")
    
    # Simplified charts section for summary when company is selected
    if selected_company != "Select a company...":
        st.markdown("---")
        st.subheader(f"📈 {selected_company} Analytics")
        
        # Simple summary chart for selected company
        company_data = consolidated_df[consolidated_df['company_name'] == selected_company].iloc[0]
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Simple bar chart comparing vendor vs client spend
            vendor_spend = company_data['vendor_total_spend_usd']
            client_spend = company_data['client_total_spend_usd']
            
            chart_data = pd.DataFrame({
                'Type': ['Vendor Spend', 'Client Spend'],
                'Amount': [vendor_spend, client_spend]
            })
            
            fig = px.bar(
                chart_data, 
                x='Type', 
                y='Amount', 
                title=f'{selected_company} Spend Comparison',
                color='Type',
                color_discrete_map={
                    'Vendor Spend': '#006FCF',
                    'Client Spend': '#23A8D1'
                }
            )
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, width='stretch')
        
        with col2:
            # Contract timeline if available
            if company_data.get('vendor_earliest_end_date') and company_data['vendor_earliest_end_date'] != 'Not specified':
                try:
                    end_date = pd.to_datetime(company_data['vendor_earliest_end_date'])
                    days_until_expiry = (end_date - datetime.now()).days
                    
                    st.metric(
                        "Days Until Contract Expiry",
                        f"{days_until_expiry} days",
                        delta="Urgent" if days_until_expiry < 90 else "Normal"
                    )
                except:
                    pass
            
            # Relationship strength indicator
            relationship_ratio = vendor_spend / client_spend if client_spend > 0 else float('inf')
            
            if relationship_ratio < 0.5:
                strength = "Client-Heavy 🟢"
            elif relationship_ratio > 2.0:
                strength = "Vendor-Heavy 🟡"
            else:
                strength = "Balanced 🟠"
            
            st.metric("Relationship Type", strength)
    else:
        # Show overall summary charts
        st.markdown("---")
        st.subheader("📈 Overall Summary")
        
        # Simple top companies chart
        top_companies = consolidated_df.nlargest(10, 'total_relationship_value')
        
        fig = px.bar(
            top_companies,
            x='company_name',
            y='total_relationship_value',
            title='Top 10 Company Relationships by Total Value',
            labels={'company_name': 'Company', 'total_relationship_value': 'Total Value (USD)'}  
        )
        fig.update_layout(xaxis_tickangle=45)
        st.plotly_chart(fig, width='stretch')
    
    with chart_tabs[1]:
        st.markdown("### Match Type Distribution")
        chart = create_match_type_distribution(filtered_results)
        if chart:
            col1, col2 = st.columns([2, 1])
            with col1:
                st.plotly_chart(chart, width='stretch')
            with col2:
                st.markdown("#### Match Quality")
                exact_count = sum(filtered_results['match_type'] == 'exact')
                fuzzy_count = sum(filtered_results['match_type'] == 'fuzzy')
                st.metric("Exact Matches", exact_count)
                st.metric("Fuzzy Matches", fuzzy_count)
                if len(filtered_results) > 0:
                    accuracy = exact_count / len(filtered_results) * 100
                    st.metric("Accuracy", f"{accuracy:.1f}%")
        else:
            st.info("No data available for this chart.")
    
    with chart_tabs[2]:
        st.markdown("### Vendor Contract Expiry Timeline")
        chart = create_contract_expiry_timeline(filtered_results)
        if chart:
            st.plotly_chart(chart, width='stretch')
            
            # Add expiry summary
            timeline_data = filtered_results[
                (filtered_results['vendor_contract_end_date'] != 'Not specified') & 
                (filtered_results['vendor_contract_end_date'].notna())
            ]
            if len(timeline_data) > 0:
                timeline_data['end_date'] = pd.to_datetime(timeline_data['vendor_contract_end_date'], errors='coerce')
                timeline_data = timeline_data[timeline_data['end_date'].notna()]
                
                if len(timeline_data) > 0:
                    today = datetime.now()
                    expiring_soon = timeline_data[timeline_data['end_date'] <= today + pd.Timedelta(days=180)]
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Contracts", len(timeline_data))
                    with col2:
                        st.metric("Expiring in 6 months", len(expiring_soon))
                    with col3:
                        if len(expiring_soon) > 0:
                            risk_value = expiring_soon['total_relationship_value'].sum()
                            st.metric("At Risk Value", f"${risk_value:,.0f}")
        else:
            st.info("No contract end dates available for timeline visualization.")
    
    with chart_tabs[3]:
        st.markdown("### Vendor vs Client Spend Analysis")
        chart = create_spend_comparison_chart(filtered_results)
        if chart:
            st.plotly_chart(chart, width='stretch')
            
            # Add spend analysis
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("#### Vendor Spend Analysis")
                vendor_total = filtered_results['vendor_total_spend_usd'].sum()
                vendor_avg = filtered_results['vendor_total_spend_usd'].mean()
                st.metric("Total Vendor Spend", f"${vendor_total:,.0f}")
                st.metric("Average Vendor Spend", f"${vendor_avg:,.0f}")
            
            with col2:
                st.markdown("#### Client Spend Analysis")
                client_total = filtered_results['client_spend_usd'].sum()
                client_avg = filtered_results['client_spend_usd'].mean()
                st.metric("Total Client Spend", f"${client_total:,.0f}")
                st.metric("Average Client Spend", f"${client_avg:,.0f}")
        else:
            st.info("No data available for this chart.")
    
    with chart_tabs[4]:
        st.markdown("### Opportunity Stages Overview")
        chart = create_opportunity_stages_chart(filtered_results)
        if chart:
            st.plotly_chart(chart, width='stretch')
            
            # Add stage analysis
            opportunities = filtered_results[
                (filtered_results['opportunity_stages'].notna()) & 
                (filtered_results['opportunity_stages'] != '')
            ]
            if len(opportunities) > 0:
                stage_values = opportunities.groupby('opportunity_stages').agg({
                    'total_relationship_value': 'sum',
                    'company_name': 'count'
                }).round(0)
                stage_values.columns = ['Total Value ($)', 'Count']
                stage_values['Total Value ($)'] = stage_values['Total Value ($)'].apply(lambda x: f"${x:,.0f}")
                
                st.markdown("#### Opportunity Value by Stage")
                st.dataframe(stage_values, width='stretch')
        else:
            st.info("No opportunity data available for stage analysis.")
    
    with chart_tabs[5]:
        st.markdown("### Summary Dashboard")
        if st.session_state.processed_data:
            chart = create_summary_metrics_chart(filtered_results, st.session_state.processed_data)
            if chart:
                st.plotly_chart(chart, width='stretch')
        else:
            st.info("Process data first to see summary dashboard.")
    
    # Export section
    st.markdown("---")
    st.subheader("📥 Export Results")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        export_type = st.selectbox(
            "Export Type",
            ["Current View", "Full Dataset"],
            help="Choose whether to export filtered results or all matches"
        )
    
    with col2:
        export_format = st.selectbox(
            "Export Format",
            ["Excel", "HTML"],
            help="Choose export format"
        )
    
    with col3:
        st.write("")  # Spacer
        st.write("")  # Spacer
        export_button = st.button("📄 Generate Export", type="secondary")
    
    if export_button:
        with st.spinner("Generating export..."):
            # Determine which data to export
            export_data = filtered_results if export_type == "Current View" else matching_results
            
            if len(export_data) == 0:
                st.error("No data to export!")
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                if export_format == "Excel":
                    excel_data = create_excel_export(export_data, st.session_state.processed_data)
                    filename = f"vendor_client_matches_{timestamp}.xlsx"
                    
                    st.download_button(
                        label="📊 Download Excel Report",
                        data=excel_data,
                        file_name=filename,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        type="primary"
                    )
                    
                elif export_format == "HTML":
                    html_data = create_html_export(export_data, st.session_state.processed_data)
                    filename = f"vendor_client_report_{timestamp}.html"
                    
                    st.download_button(
                        label="🌐 Download HTML Report",
                        data=html_data.encode('utf-8'),
                        file_name=filename,
                        mime="text/html",
                        type="primary"
                    )
                
                st.success(f"✅ {export_format} report generated successfully! ({len(export_data)} matches included)")

def main():
    """Main application function."""
    # Initialize
    inject_custom_css()
    show_header()
    initialize_session_state()
    
    # Sidebar for file uploads
    vendor_file, client_files = handle_file_upload()
    
    # Process files button
    if st.sidebar.button("🚀 Process Files", type="primary", width='stretch'):
        if vendor_file and client_files:
            processed_data = process_uploaded_files(vendor_file, client_files)
            if processed_data:
                st.session_state.processed_data = processed_data
                st.success("Files processed successfully!")
        else:
            st.error("Please upload at least one vendor file and one client file.")
    
    # Show data overview if data is processed
    if st.session_state.processed_data:
        show_data_overview(st.session_state.processed_data)
        
        # Perform matching button
        if st.button("🔍 Find Matches", type="primary", width='content'):
            matching_results = perform_matching(st.session_state.processed_data)
            if matching_results is not None:
                st.session_state.matching_results = matching_results
                st.success("Matching completed successfully!")
    
    # Display results if available
    if st.session_state.matching_results is not None:
        display_matching_results(st.session_state.matching_results)
    
    # Sidebar info
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ℹ️ Information")
    st.sidebar.info(
        "This tool uses two-phase matching:\\n"
        "1. **Exact Match**: Case-insensitive exact matches\\n"
        "2. **Fuzzy Match**: AI-powered similarity matching\\n\\n"
        "All amounts are converted to USD using current exchange rates."
    )
    
    # Show currency cache status
    if st.sidebar.checkbox("Show Currency Status"):
        cache_status = st.session_state.currency_converter.get_cache_status()
        st.sidebar.json(cache_status)

def display_company_details(consolidated_df, company_name, raw_matches_df):
    """Display detailed breakdown for a selected company."""
    st.markdown("---")
    st.subheader(f"🏢 Detailed View: {company_name}")
    
    # Get company data
    company_data = consolidated_df[consolidated_df['company_name'] == company_name].iloc[0]
    
    # Display summary cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Vendor Contracts",
            f"{company_data['vendor_contract_count']}"
        )
    
    with col2:
        st.metric(
            "Vendor Spend",
            f"${company_data['vendor_total_spend_usd']:,.0f}"
        )
    
    with col3:
        st.metric(
            "Contract End Date",
            company_data['vendor_earliest_end_date']
        )
    
    with col4:
        st.metric(
            "Client Spend",
            f"${company_data['client_total_spend_usd']:,.0f}"
        )
    
    # Display vendor contracts breakdown
    if raw_matches_df is not None:
        vendor_contracts = raw_matches_df[raw_matches_df['company_name'] == company_name]
        
        if len(vendor_contracts) > 0:
            st.markdown("### 💼 Vendor Contract Details")
            
            # Show individual contracts
            contract_display = []
            for _, contract in vendor_contracts.iterrows():
                vendor_data = contract['vendor_data'] if isinstance(contract['vendor_data'], dict) else {}
                contract_display.append({
                    'Supplier/Vendor': vendor_data.get('company_name', company_name),
                    'Contract Value (USD)': f"${vendor_data.get('total_value', 0):,.0f}",
                    'End Date': vendor_data.get('end_date', 'Not specified'),
                    'Contract Terms': vendor_data.get('terms_months', 'Not specified'),
                    'Currency': vendor_data.get('currency', 'USD')
                })
            
            contract_df = pd.DataFrame(contract_display)
            st.dataframe(contract_df, width='stretch')
    
    # Display client information
    st.markdown("### 🎯 Client Information")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**Total Client Spend:** ${company_data['client_total_spend_usd']:,.0f}")
        st.write(f"**Data Sources:** {company_data.get('client_sources', 'N/A')}")
    
    with col2:
        if pd.notna(company_data.get('opportunity_stages')):
            st.write(f"**Opportunity Stages:** {company_data.get('opportunity_stages')}")
        
        relationship_value = company_data['total_relationship_value']
        st.write(f"**Total Relationship Value:** ${relationship_value:,.0f}")

if __name__ == "__main__":
    main()