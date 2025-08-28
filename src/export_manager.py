"""Export functionality for HTML and Excel reports."""

import pandas as pd
import io
import base64
from datetime import datetime
from pathlib import Path
from jinja2 import Template
from src.config import BRAND_COLORS

def create_excel_export(matching_results: pd.DataFrame, processed_data: dict) -> bytes:
    """Create Excel export with multiple sheets."""
    
    # Create Excel writer object
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Main results sheet
        if matching_results is not None and len(matching_results) > 0:
            # Prepare main results
            export_df = matching_results.copy()
            
            # Format currency columns for Excel
            currency_columns = ['vendor_total_spend_usd', 'client_total_spend_usd', 'total_relationship_value']
            for col in currency_columns:
                if col in export_df.columns:
                    export_df[col] = export_df[col].round(2)
            
            # Write main results
            export_df.to_excel(writer, sheet_name='Matches', index=False)
            
            # Summary sheet
            summary_data = create_summary_data(matching_results, processed_data)
            summary_df = pd.DataFrame(list(summary_data.items()), columns=['Metric', 'Value'])
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # Match type breakdown - handle both match_type and match_quality
            match_column = 'match_type' if 'match_type' in matching_results.columns else 'match_quality'
            if match_column in matching_results.columns:
                match_breakdown = matching_results.groupby(match_column).agg({
                    'company_name': 'count',
                    'vendor_total_spend_usd': 'sum',
                    'client_total_spend_usd': 'sum',
                    'total_relationship_value': 'sum'
                }).round(2)
                match_breakdown.columns = ['Count', 'Vendor Spend (USD)', 'Client Spend (USD)', 'Total Value (USD)']
                match_breakdown.to_excel(writer, sheet_name='Match Analysis')
            
            # Top relationships - handle different column structures
            top_cols = ['company_name', 'vendor_total_spend_usd', 'client_total_spend_usd', 'total_relationship_value']
            
            # Add match type column if available
            if 'match_type' in matching_results.columns:
                top_cols.extend(['match_type', 'match_score'])
            elif 'match_quality' in matching_results.columns:
                top_cols.append('match_quality')
            
            # Only include columns that actually exist
            available_cols = [col for col in top_cols if col in matching_results.columns]
            
            top_relationships = matching_results.nlargest(20, 'total_relationship_value')[available_cols]
            top_relationships.to_excel(writer, sheet_name='Top Relationships', index=False)
            
        # Raw data sheets (if available)
        if 'vendors' in processed_data:
            vendors_df = processed_data['vendors'].copy()
            if 'total_value_usd' in vendors_df.columns:
                vendors_df['total_value_usd'] = vendors_df['total_value_usd'].round(2)
            vendors_df.to_excel(writer, sheet_name='Vendor Data', index=False)
        
        if 'clients' in processed_data:
            clients_df = processed_data['clients'].copy()
            if 'client_spend' in clients_df.columns:
                clients_df['client_spend'] = clients_df['client_spend'].round(2)
            clients_df.to_excel(writer, sheet_name='Client Data', index=False)
    
    output.seek(0)
    return output.getvalue()

def create_html_export(matching_results: pd.DataFrame, processed_data: dict) -> str:
    """Create HTML export with styled report."""
    
    # HTML template
    html_template = Template("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AI Data Matching Report - {{ report_date }}</title>
        <style>
            /* CSS Variables for brand colors */
            :root {
                --primary-color: {{ colors.primary }};
                --primary-70: {{ colors.primary_70 }};
                --primary-35: {{ colors.primary_35 }};
                --secondary-color: {{ colors.secondary }};
                --accent-color: {{ colors.accent }};
                --success-color: {{ colors.success }};
                --warning-color: {{ colors.warning }};
                --text-color: {{ colors.text }};
                --background-color: {{ colors.background }};
            }
            
            /* Global Styles */
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: var(--background-color);
                color: var(--text-color);
                line-height: 1.6;
                margin: 0;
                padding: 20px;
            }
            
            .container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 0 20px;
            }
            
            /* Header */
            .header {
                background: linear-gradient(135deg, var(--primary-color), var(--accent-color));
                color: white;
                padding: 40px 0;
                margin: -20px -20px 40px -20px;
                text-align: center;
                box-shadow: 0 4px 15px rgba(0, 111, 207, 0.2);
            }
            
            .header h1 {
                font-size: 2.5rem;
                margin-bottom: 10px;
                font-weight: 700;
            }
            
            .header p {
                font-size: 1.1rem;
                opacity: 0.9;
                margin: 0;
            }
            
            /* Summary Cards */
            .summary-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin-bottom: 40px;
            }
            
            .summary-card {
                background: white;
                border-radius: 12px;
                padding: 25px;
                text-align: center;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
                border-left: 5px solid var(--primary-color);
                transition: transform 0.3s ease;
            }
            
            .summary-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
            }
            
            .summary-card .value {
                font-size: 2.5rem;
                font-weight: 700;
                color: var(--primary-color);
                margin-bottom: 5px;
            }
            
            .summary-card .label {
                font-size: 0.9rem;
                color: var(--text-color);
                opacity: 0.7;
                text-transform: uppercase;
                letter-spacing: 1px;
            }
            
            /* Section Headers */
            .section {
                margin-bottom: 40px;
            }
            
            .section h2 {
                color: var(--secondary-color);
                font-size: 1.8rem;
                margin-bottom: 20px;
                padding-bottom: 10px;
                border-bottom: 3px solid var(--primary-35);
            }
            
            /* Tables */
            .table-container {
                background: white;
                border-radius: 12px;
                overflow: hidden;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
            }
            
            table {
                width: 100%;
                border-collapse: collapse;
                margin: 0;
            }
            
            th {
                background: var(--primary-color);
                color: white;
                padding: 15px 12px;
                text-align: left;
                font-weight: 600;
                font-size: 0.9rem;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            
            td {
                padding: 12px;
                border-bottom: 1px solid #eee;
                font-size: 0.9rem;
            }
            
            tr:nth-child(even) {
                background-color: #f8f9fa;
            }
            
            tr:hover {
                background-color: var(--primary-35);
                background-color: rgba(0, 111, 207, 0.05);
            }
            
            /* Match Type Badges */
            .match-exact {
                background: var(--success-color);
                color: white;
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 0.8rem;
                font-weight: 600;
                text-transform: uppercase;
            }
            
            .match-fuzzy {
                background: var(--warning-color);
                color: var(--secondary-color);
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 0.8rem;
                font-weight: 600;
                text-transform: uppercase;
            }
            
            /* Currency formatting */
            .currency {
                font-weight: 600;
                color: var(--primary-color);
            }
            
            /* Footer */
            .footer {
                margin-top: 60px;
                padding: 20px 0;
                border-top: 2px solid var(--primary-35);
                text-align: center;
                color: var(--text-color);
                opacity: 0.7;
                font-size: 0.9rem;
            }
            
            /* Print styles */
            @media print {
                body {
                    padding: 0;
                }
                
                .header {
                    margin: 0;
                    padding: 20px 0;
                }
                
                .summary-card {
                    break-inside: avoid;
                }
                
                table {
                    break-inside: auto;
                }
                
                tr {
                    break-inside: avoid;
                    break-after: auto;
                }
            }
            
            /* Responsive design */
            @media (max-width: 768px) {
                .header h1 {
                    font-size: 2rem;
                }
                
                .summary-grid {
                    grid-template-columns: 1fr;
                }
                
                .table-container {
                    overflow-x: auto;
                }
                
                table {
                    min-width: 600px;
                }
            }
        </style>
    </head>
    <body>
        <div class="header">
            <div class="container">
                <h1>🔍 AI Data Matching Report</h1>
                <p>Vendor-Client Relationship Analysis | Generated on {{ report_date }}</p>
            </div>
        </div>
        
        <div class="container">
            <!-- Summary Section -->
            <div class="summary-grid">
                <div class="summary-card">
                    <div class="value">{{ summary.total_matches }}</div>
                    <div class="label">Total Matches</div>
                </div>
                <div class="summary-card">
                    <div class="value">{{ summary.exact_matches }}</div>
                    <div class="label">Exact Matches</div>
                </div>
                <div class="summary-card">
                    <div class="value">{{ summary.fuzzy_matches }}</div>
                    <div class="label">Fuzzy Matches</div>
                </div>
                <div class="summary-card">
                    <div class="value">${{ summary.total_value }}</div>
                    <div class="label">Total Relationship Value</div>
                </div>
            </div>
            
            <!-- Main Results Section -->
            <div class="section">
                <h2>📊 Detailed Matching Results</h2>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Company Name</th>
                                <th>Vendor Spend (USD)</th>
                                <th>Client Spend (USD)</th>
                                <th>Total Value (USD)</th>
                                <th>Match Type</th>
                                <th>Match Score</th>
                                <th>Contract End Date</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for row in matches %}
                            <tr>
                                <td><strong>{{ row.company_name }}</strong></td>
                                <td class="currency">${{ "%.0f"|format(row.vendor_total_spend_usd) }}</td>
                                <td class="currency">${{ "%.0f"|format(row.client_total_spend_usd) }}</td>
                                <td class="currency"><strong>${{ "%.0f"|format(row.total_relationship_value) }}</strong></td>
                                <td>
                                    {% if row.match_type is defined %}
                                        {% if row.match_type == 'exact' %}
                                            <span class="match-exact">EXACT</span>
                                        {% else %}
                                            <span class="match-fuzzy">FUZZY</span>
                                        {% endif %}
                                    {% elif row.match_quality is defined %}
                                        {% if row.match_quality == 'Exact' %}
                                            <span class="match-exact">EXACT</span>
                                        {% else %}
                                            <span class="match-fuzzy">FUZZY</span>
                                        {% endif %}
                                    {% else %}
                                        <span class="match-fuzzy">MATCHED</span>
                                    {% endif %}
                                </td>
                                <td>
                                    {% if row.match_score is defined %}
                                        {{ "%.1f"|format(row.match_score * 100) }}%
                                    {% else %}
                                        N/A
                                    {% endif %}
                                </td>
                                <td>{{ row.vendor_contract_end_date }}</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
            
            <!-- Analysis Summary -->
            {% if analysis %}
            <div class="section">
                <h2>📈 Analysis Summary</h2>
                <div class="summary-grid">
                    <div class="summary-card">
                        <div class="value">{{ analysis.match_rate }}%</div>
                        <div class="label">Match Success Rate</div>
                    </div>
                    <div class="summary-card">
                        <div class="value">${{ analysis.avg_vendor_spend }}</div>
                        <div class="label">Avg Vendor Spend</div>
                    </div>
                    <div class="summary-card">
                        <div class="value">${{ analysis.avg_client_spend }}</div>
                        <div class="label">Avg Client Spend</div>
                    </div>
                    <div class="summary-card">
                        <div class="value">{{ analysis.total_vendors }}</div>
                        <div class="label">Total Vendors Processed</div>
                    </div>
                </div>
            </div>
            {% endif %}
        </div>
        
        <div class="footer">
            <div class="container">
                <p>Report generated by AI Data Matching Tool | {{ report_date }}</p>
                <p>This report contains confidential business information</p>
            </div>
        </div>
    </body>
    </html>
    """)
    
    # Prepare data for template
    report_data = {
        'report_date': datetime.now().strftime('%B %d, %Y at %I:%M %p'),
        'colors': BRAND_COLORS,
        'summary': create_summary_data(matching_results, processed_data),
        'matches': matching_results.to_dict('records') if matching_results is not None else [],
        'analysis': create_analysis_data(matching_results, processed_data) if matching_results is not None else None
    }
    
    return html_template.render(**report_data)

def create_summary_data(matching_results: pd.DataFrame, processed_data: dict) -> dict:
    """Create summary data for exports."""
    
    if matching_results is None or len(matching_results) == 0:
        return {
            'total_matches': 0,
            'exact_matches': 0,
            'fuzzy_matches': 0,
            'total_value': '0'
        }
    
    # Handle both raw matches (with match_type) and consolidated data (with match_quality)
    if 'match_type' in matching_results.columns:
        exact_matches = sum(matching_results['match_type'] == 'exact')
        fuzzy_matches = sum(matching_results['match_type'] == 'fuzzy')
    elif 'match_quality' in matching_results.columns:
        exact_matches = sum(matching_results['match_quality'] == 'Exact')
        fuzzy_matches = sum(matching_results['match_quality'] == 'Fuzzy')
    else:
        exact_matches = 0
        fuzzy_matches = 0
    
    total_value = matching_results['total_relationship_value'].sum()
    
    return {
        'total_matches': f"{len(matching_results):,}",
        'exact_matches': f"{exact_matches:,}",
        'fuzzy_matches': f"{fuzzy_matches:,}",
        'total_value': f"{total_value:,.0f}"
    }

def create_analysis_data(matching_results: pd.DataFrame, processed_data: dict) -> dict:
    """Create analysis data for exports."""
    
    if matching_results is None or len(matching_results) == 0:
        return None
    
    total_vendors = len(processed_data.get('vendors', []))
    match_rate = (len(matching_results) / total_vendors * 100) if total_vendors > 0 else 0
    
    avg_vendor_spend = matching_results['vendor_total_spend_usd'].mean()
    avg_client_spend = matching_results['client_total_spend_usd'].mean()
    
    return {
        'match_rate': f"{match_rate:.1f}",
        'avg_vendor_spend': f"{avg_vendor_spend:,.0f}",
        'avg_client_spend': f"{avg_client_spend:,.0f}",
        'total_vendors': f"{total_vendors:,}"
    }

def get_download_link(data: bytes, filename: str, link_text: str) -> str:
    """Generate download link for data."""
    b64_data = base64.b64encode(data).decode()
    
    if filename.endswith('.xlsx'):
        media_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    elif filename.endswith('.html'):
        media_type = 'text/html'
    else:
        media_type = 'application/octet-stream'
    
    href = f'<a href="data:{media_type};base64,{b64_data}" download="{filename}">{link_text}</a>'
    return href