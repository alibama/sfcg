import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import re
from collections import defaultdict

# Configure page layout to be wider
st.set_page_config(layout="wide")

# State coordinates for mapping
STATE_COORDS = {
    'AL': (32.7794, -86.8287), 'AK': (64.0685, -152.2782), 'AZ': (34.2744, -111.6602),
    'AR': (34.8938, -92.4426), 'CA': (36.1700, -119.7462), 'CO': (39.0646, -105.3272),
    'CT': (41.6219, -72.7273), 'DE': (38.9896, -75.5050), 'FL': (28.6305, -82.4497),
    'GA': (32.6415, -83.4426), 'HI': (20.2927, -156.3737), 'ID': (44.3509, -114.6130),
    'IL': (40.0417, -89.1965), 'IN': (39.8942, -86.2816), 'IA': (42.0751, -93.4960),
    'KS': (38.4937, -98.3804), 'KY': (37.5347, -85.3021), 'LA': (31.0689, -91.9968),
    'ME': (45.3695, -69.2428), 'MD': (39.0550, -76.7909), 'MA': (42.2596, -71.8083),
    'MI': (44.3467, -85.4102), 'MN': (46.2807, -94.3053), 'MS': (32.7364, -89.6678),
    'MO': (38.3566, -92.4580), 'MT': (47.0527, -109.6333), 'NE': (41.5378, -99.7951),
    'NV': (39.3289, -116.6312), 'NH': (43.6805, -71.5811), 'NJ': (40.1907, -74.6728),
    'NM': (34.4071, -106.1126), 'NY': (42.9538, -75.5268), 'NC': (35.5557, -79.3877),
    'ND': (47.4501, -100.4659), 'OH': (40.2862, -82.7937), 'OK': (35.5889, -97.4943),
    'OR': (43.9336, -120.5583), 'PA': (40.8781, -77.7996), 'RI': (41.6762, -71.5562),
    'SC': (33.9169, -80.8964), 'SD': (44.4443, -100.2263), 'TN': (35.8580, -86.3505),
    'TX': (31.4757, -99.3312), 'UT': (39.3055, -111.6703), 'VT': (44.0687, -72.6658),
    'VA': (37.5215, -78.8537), 'WA': (47.3826, -120.4472), 'WV': (38.6409, -80.6227),
    'WI': (44.6243, -89.9941), 'WY': (42.9957, -107.5512)
}

def find_states_in_text(text):
    """Find all state abbreviations in text."""
    pattern = r'\b(AL|AK|AZ|AR|CA|CO|CT|DE|FL|GA|HI|ID|IL|IN|IA|KS|KY|LA|ME|MD|MA|MI|MN|MS|MO|MT|NE|NV|NH|NJ|NM|NY|NC|ND|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VT|VA|WA|WV|WI|WY)\b'
    return re.findall(pattern, text)

def extract_organization_and_states(text):
    """Extract organization name and states from a line of text."""
    # Clean the text
    text = text.strip('* \t')
    
    # Find all states
    states = find_states_in_text(text)
    
    # Extract organization name - look for text before the first parenthesis or action verb
    org_pattern = r'^([^()]+?)(?=\s*[\(]|\s+(?:is|has|have|works|working|connects|recruiting|mobilized|organized))'
    org_match = re.search(org_pattern, text)
    
    if org_match and states:
        return {
            'Organization': org_match.group(1).strip(),
            'States': ', '.join(sorted(set(states))),
            'Description': text
        }
    return None

def process_text(text):
    """Process raw text into structured data."""
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    data = []
    
    for line in lines:
        result = extract_organization_and_states(line)
        if result:
            data.append(result)
    
    return pd.DataFrame(data)

def create_visualization(df, selected_state='All States'):
    """Create the map visualization."""
    fig = go.Figure()
    
    # Add base US map
    fig.add_trace(go.Scattergeo(
        locationmode='USA-states',
        lon=[coord[1] for coord in STATE_COORDS.values()],
        lat=[coord[0] for coord in STATE_COORDS.values()],
        mode='markers',
        marker=dict(size=1, color='gray'),
        showlegend=False
    ))
    
    # Prepare data for visualization
    plot_data = []
    for _, row in df.iterrows():
        states = [s.strip() for s in row['States'].split(',')]
        for state in states:
            if state in STATE_COORDS:
                plot_data.append({
                    'Organization': row['Organization'],
                    'State': state,
                    'Description': row['Description'],
                    'Coords': STATE_COORDS[state]
                })
    
    # Group by state for point spreading
    state_groups = defaultdict(list)
    for item in plot_data:
        state_groups[item['State']].append(item)
    
    # Create color mapping for organizations
    unique_orgs = sorted(df['Organization'].unique())
    colors = px.colors.qualitative.Set3[:len(unique_orgs)]
    color_map = dict(zip(unique_orgs, colors))
    
    # Track organizations already in legend
    legend_entries = set()
    
    # Plot points with spread for overlapping locations
    for state, items in state_groups.items():
        if selected_state != 'All States' and state != selected_state:
            continue
            
        n_items = len(items)
        for i, item in enumerate(items):
            # Calculate spread position
            angle = (2 * np.pi * i) / n_items
            spread = 0.7  # Increased spread
            base_lat, base_lon = item['Coords']
            adj_lat = base_lat + spread * np.sin(angle)
            adj_lon = base_lon + spread * np.cos(angle)
            
            # Determine if this organization should be in legend
            show_in_legend = item['Organization'] not in legend_entries
            if show_in_legend:
                legend_entries.add(item['Organization'])
            
            # Add point to map
            fig.add_trace(go.Scattergeo(
                lon=[adj_lon],
                lat=[adj_lat],
                mode='markers+text',
                text=item['Organization'],
                textposition='top center',
                marker=dict(
                    size=12,
                    color=color_map[item['Organization']],
                    line=dict(width=1, color='black')
                ),
                name=item['Organization'],
                hovertext=f"{item['Organization']}<br>{item['State']}<br>{item['Description']}",
                hoverinfo='text',
                showlegend=show_in_legend
            ))
    
    # Update layout
    fig.update_layout(
        geo=dict(
            scope='usa',
            projection_type='albers usa',
            showland=True,
            landcolor='rgb(240, 240, 240)',
            countrycolor='rgb(204, 204, 204)',
            center=dict(lat=39.5, lon=-98.35),
            projection_scale=1.2
        ),
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="right",
            x=0.99,
            bgcolor="rgba(255, 255, 255, 0.8)"
        ),
        height=800,
        margin=dict(l=0, r=0, t=0, b=0)
    )
    
    return fig

# Streamlit UI
st.title('Organization-State Network Analyzer')

# Input and controls
col1, col2 = st.columns([2, 1])

with col1:
    text_input = st.text_area(
        "Paste your content here:",
        height=200,
        help="Paste the text containing organization and state information."
    )

if text_input:
    # Process the text
    df = process_text(text_input)
    
    # Get unique states
    all_states = set()
    for state_list in df['States']:
        all_states.update([s.strip() for s in state_list.split(',')])
    
    # Controls and stats
    with col2:
        selected_state = st.selectbox(
            'Filter by State:',
            ['All States'] + sorted(list(all_states))
        )
        
        st.metric('Total Organizations', len(df))
        st.metric('Total States', len(all_states))
        
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download data as CSV",
            data=csv,
            file_name="organization_state_data.csv",
            mime="text/csv"
        )
    
    # Show visualization
    st.plotly_chart(create_visualization(df, selected_state), use_container_width=True)
    
    # Show data table
    if selected_state != 'All States':
        filtered_df = df[df['States'].str.contains(selected_state)]
    else:
        filtered_df = df
    
    st.subheader('Analyzed Data')
    st.dataframe(filtered_df)
