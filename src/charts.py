"""Interactive charts and visualizations using Plotly."""

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime, timedelta
from src.config import BRAND_COLORS

def create_top_matches_chart(matching_results: pd.DataFrame, top_n: int = 10):
    """Create a horizontal bar chart of top matches by relationship value."""
    
    if matching_results is None or len(matching_results) == 0:
        return None
    
    # Get top N matches
    top_matches = matching_results.nlargest(top_n, 'total_relationship_value')
    
    # Create the chart
    fig = go.Figure()
    
    # Add vendor spend bars
    fig.add_trace(go.Bar(
        y=top_matches['company_name'],
        x=top_matches['vendor_total_spend_usd'],
        name='Vendor Spend',
        orientation='h',
        marker_color=BRAND_COLORS['primary'],
        text=[f"${x:,.0f}" for x in top_matches['vendor_total_spend_usd']],
        textposition='inside'
    ))
    
    # Add client spend bars
    fig.add_trace(go.Bar(
        y=top_matches['company_name'],
        x=top_matches['client_total_spend_usd'],
        name='Client Spend', 
        orientation='h',
        marker_color=BRAND_COLORS['accent'],
        text=[f"${x:,.0f}" for x in top_matches['client_total_spend_usd']],
        textposition='inside'
    ))
    
    fig.update_layout(
        title=f'Top {top_n} Company Relationships by Value',
        xaxis_title='Amount (USD)',
        yaxis_title='Company Name',
        barmode='stack',
        height=max(400, top_n * 40),
        template='plotly_white',
        font=dict(family="Inter, sans-serif"),
        title_font_size=18,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig

def create_match_type_distribution(matching_results: pd.DataFrame):
    """Create a pie chart showing distribution of match types."""
    
    if matching_results is None or len(matching_results) == 0:
        return None
    
    # Count match types - handle both match_type and match_quality columns
    if 'match_type' in matching_results.columns:
        match_counts = matching_results['match_type'].value_counts()
    elif 'match_quality' in matching_results.columns:
        match_counts = matching_results['match_quality'].value_counts()
    else:
        return None
    
    # Create pie chart
    fig = go.Figure(data=[go.Pie(
        labels=[label.title() + ' Match' for label in match_counts.index],
        values=match_counts.values,
        hole=.3,
        marker_colors=[BRAND_COLORS['primary'], BRAND_COLORS['warning']]
    )])
    
    fig.update_layout(
        title='Match Type Distribution',
        template='plotly_white',
        font=dict(family="Inter, sans-serif"),
        title_font_size=18,
        height=400
    )
    
    fig.update_traces(
        textposition='inside',
        textinfo='percent+label',
        textfont_size=12
    )
    
    return fig

def create_contract_expiry_timeline(matching_results: pd.DataFrame):
    """Create a timeline chart of vendor contract expiry dates."""
    
    if matching_results is None or len(matching_results) == 0:
        return None
    
    # Filter out rows with no end date
    timeline_data = matching_results[
        (matching_results['vendor_contract_end_date'] != 'Not specified') & 
        (matching_results['vendor_contract_end_date'].notna())
    ].copy()
    
    if len(timeline_data) == 0:
        return None
    
    # Convert end dates to datetime
    timeline_data['end_date'] = pd.to_datetime(timeline_data['vendor_contract_end_date'], errors='coerce')
    timeline_data = timeline_data[timeline_data['end_date'].notna()]
    
    if len(timeline_data) == 0:
        return None
    
    # Sort by end date
    timeline_data = timeline_data.sort_values('end_date')
    
    # Create scatter plot
    fig = go.Figure()
    
    # Add scatter points
    fig.add_trace(go.Scatter(
        x=timeline_data['end_date'],
        y=timeline_data['total_relationship_value'],
        mode='markers',
        marker=dict(
            size=[min(20, max(8, val/50000)) for val in timeline_data['total_relationship_value']],
            color=timeline_data['total_relationship_value'],
            colorscale='Blues',
            showscale=True,
            colorbar=dict(title="Relationship Value (USD)")
        ),
        text=timeline_data['company_name'],
        hovertemplate='<b>%{text}</b><br>' +
                      'Contract Ends: %{x}<br>' +
                      'Relationship Value: $%{y:,.0f}<br>' +
                      '<extra></extra>',
        name='Contracts'
    ))
    
    # Add today line
    today = datetime.now().date()
    fig.add_vline(x=today, line_dash="dash", line_color="red", annotation_text="Today")
    
    fig.update_layout(
        title='Vendor Contract Expiry Timeline',
        xaxis_title='Contract End Date',
        yaxis_title='Total Relationship Value (USD)',
        template='plotly_white',
        font=dict(family="Inter, sans-serif"),
        title_font_size=18,
        height=500
    )
    
    return fig

def create_spend_comparison_chart(matching_results: pd.DataFrame):
    """Create a scatter plot comparing vendor vs client spend."""
    
    if matching_results is None or len(matching_results) == 0:
        return None
    
    # Create scatter plot
    fig = go.Figure()
    
    # Color by match type
    colors = {
        'exact': BRAND_COLORS['primary'],
        'fuzzy': BRAND_COLORS['warning']
    }
    
    for match_type in matching_results['match_type'].unique():
        subset = matching_results[matching_results['match_type'] == match_type]
        
        fig.add_trace(go.Scatter(
            x=subset['vendor_total_spend_usd'],
            y=subset['client_total_spend_usd'],
            mode='markers',
            marker=dict(
                color=colors.get(match_type, BRAND_COLORS['accent']),
                size=10,
                opacity=0.7
            ),
            name=f'{match_type.title()} Match',
            text=subset['company_name'],
            hovertemplate='<b>%{text}</b><br>' +
                          'Vendor Spend: $%{x:,.0f}<br>' +
                          'Client Spend: $%{y:,.0f}<br>' +
                          f'Match Type: {match_type.title()}<br>' +
                          '<extra></extra>'
        ))
    
    # Add diagonal line for reference
    max_val = max(matching_results['vendor_total_spend_usd'].max(), matching_results['client_total_spend_usd'].max())
    fig.add_trace(go.Scatter(
        x=[0, max_val],
        y=[0, max_val],
        mode='lines',
        line=dict(dash='dash', color='gray'),
        name='Equal Spend Line',
        hoverinfo='skip'
    ))
    
    fig.update_layout(
        title='Vendor Spend vs Client Spend Comparison',
        xaxis_title='Vendor Spend (USD)',
        yaxis_title='Client Spend (USD)',
        template='plotly_white',
        font=dict(family="Inter, sans-serif"),
        title_font_size=18,
        height=500,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig

def create_opportunity_stages_chart(matching_results: pd.DataFrame):
    """Create a bar chart of opportunity stages."""
    
    if matching_results is None or len(matching_results) == 0:
        return None
    
    # Filter for opportunities with stages
    opportunities = matching_results[
        (matching_results['opportunity_stages'].notna()) & 
        (matching_results['opportunity_stages'] != '')
    ].copy()
    
    if len(opportunities) == 0:
        return None
    
    # Count by stage
    stage_counts = opportunities['opportunity_stages'].value_counts()
    
    # Create bar chart
    fig = go.Figure(data=[go.Bar(
        x=stage_counts.index,
        y=stage_counts.values,
        marker_color=BRAND_COLORS['accent'],
        text=stage_counts.values,
        textposition='auto'
    )])
    
    fig.update_layout(
        title='Opportunity Distribution by Stage',
        xaxis_title='Stage',
        yaxis_title='Number of Opportunities',
        template='plotly_white',
        font=dict(family="Inter, sans-serif"),
        title_font_size=18,
        height=400
    )
    
    return fig

def create_summary_metrics_chart(matching_results: pd.DataFrame, processed_data: dict):
    """Create a summary metrics dashboard."""
    
    # Create subplots
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Match Success Rate', 'Total Value Breakdown', 
                       'Currency Distribution', 'Match Quality'),
        specs=[[{"type": "indicator"}, {"type": "pie"}],
               [{"type": "bar"}, {"type": "bar"}]]
    )
    
    if matching_results is not None and len(matching_results) > 0:
        # Match success rate (indicator)
        total_vendors = len(processed_data.get('vendors', []))
        matched_vendors = len(matching_results)
        success_rate = (matched_vendors / total_vendors * 100) if total_vendors > 0 else 0
        
        fig.add_trace(go.Indicator(
            mode = "gauge+number+delta",
            value = success_rate,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Success Rate (%)"},
            gauge = {'axis': {'range': [None, 100]},
                     'bar': {'color': BRAND_COLORS['primary']},
                     'steps': [
                         {'range': [0, 50], 'color': "lightgray"},
                         {'range': [50, 80], 'color': "gray"}],
                     'threshold': {'line': {'color': "red", 'width': 4},
                                   'thickness': 0.75, 'value': 90}}
        ), row=1, col=1)
        
        # Total value breakdown (pie)
        total_vendor = matching_results['vendor_total_spend_usd'].sum()
        total_client = matching_results['client_total_spend_usd'].sum()
        
        fig.add_trace(go.Pie(
            labels=['Vendor Spend', 'Client Spend'],
            values=[total_vendor, total_client],
            marker_colors=[BRAND_COLORS['primary'], BRAND_COLORS['accent']]
        ), row=1, col=2)
        
        # Match quality distribution
        match_scores = matching_results.groupby('match_type')['match_score'].mean()
        
        fig.add_trace(go.Bar(
            x=match_scores.index,
            y=match_scores.values,
            marker_color=[BRAND_COLORS['primary'] if x == 'exact' else BRAND_COLORS['warning'] 
                         for x in match_scores.index],
            text=[f"{x:.2f}" for x in match_scores.values],
            textposition='auto'
        ), row=2, col=2)
    
    fig.update_layout(
        height=800,
        showlegend=False,
        template='plotly_white',
        font=dict(family="Inter, sans-serif"),
        title_text="Summary Dashboard",
        title_font_size=20
    )
    
    return fig