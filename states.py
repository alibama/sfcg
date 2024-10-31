import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import re
from collections import defaultdict
import json


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

def extract_states(text):
    """Extract state abbreviations from text."""
    state_abbrevs = {
        'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
        'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
        'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
        'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
        'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY'
    }
    
    found_states = set()
    for state in state_abbrevs:
        if re.search(r'\b' + state + r'\b', text):
            found_states.add(state)
    
    return list(found_states)

def extract_organization(text):
    """Extract organization name from the beginning of a bullet point."""
    match = re.search(r'^\s*\*?\s*([^()]+?)(?:\s*\([^)]+\))?(?=\s+(?:is|has|have|works|working|connects|recruiting|mobilized|organized))', text)
    if match:
        return match.group(1).strip()
    return None

def process_text(raw_text):
    """Process raw text into structured data."""
    organizations = []
    states = []
    descriptions = []
    
    lines = raw_text.split('\n')
    for line in lines:
        line = line.strip()
        if line.startswith('*') or line != '':
            org = extract_organization(line)
            if org:
                state_list = extract_states(line)
                if state_list:
                    organizations.append(org)
                    states.append(', '.join(state_list))
                    descriptions.append(line.strip('* '))

    return pd.DataFrame({
        'Organization': organizations,
        'States': states,
        'Description': descriptions
    })

def create_state_org_map(df, selected_state='All States'):
    """Create an interactive map showing organizations by state."""
    # Expand the states data
    expanded_data = []
    for _, row in df.iterrows():
        states = [s.strip() for s in row['States'].split(',')]
        for state in states:
            if state in STATE_COORDS:
                expanded_data.append({
                    'Organization': row['Organization'],
                    'State': state,
                    'Description': row['Description'],
                    'lat': STATE_COORDS[state][0],
                    'lon': STATE_COORDS[state][1]
                })
    
    expanded_df = pd.DataFrame(expanded_data)
    
    # Filter based on selected state
    if selected_state != 'All States':
        expanded_df = expanded_df[expanded_df['State'] == selected_state]
    
    # Create base map
    fig = go.Figure()
    
    # Add US state boundaries
    fig.add_trace(go.Scattergeo(
        locationmode='USA-states',
        lon=[STATE_COORDS[state][1] for state in STATE_COORDS],
        lat=[STATE_COORDS[state][0] for state in STATE_COORDS],
        mode='markers',
        marker=dict(size=1, color='gray'),
        showlegend=False
    ))
    
    # Calculate number of organizations per state
    state_counts = expanded_df['State'].value_counts()
    
    # Create a color scale based on unique organizations
    unique_orgs = expanded_df['Organization'].unique()
    colors = px.colors.qualitative.Set3[:len(unique_orgs)]
    org_colors = dict(zip(unique_orgs, colors))
    
    # Add points for each organization, with slight position adjustments for overlap
    for state in state_counts.index:
        state_data = expanded_df[expanded_df['State'] == state]
        n_orgs = len(state_data)
        
        # Calculate positions in a circular pattern
        for i, (_, org_row) in enumerate(state_data.iterrows()):
            # Create a small offset in a circular pattern
            angle = (2 * np.pi * i) / n_orgs
            offset = 0.3  # Adjust this value to control the spread of points
            adj_lat = org_row['lat'] + offset * np.sin(angle)
            adj_lon = org_row['lon'] + offset * np.cos(angle)
            
            fig.add_trace(go.Scattergeo(
                locationmode='USA-states',
                lon=[adj_lon],
                lat=[adj_lat],
                mode='markers+text',
                marker=dict(
                    size=12,
                    color=org_colors[org_row['Organization']],
                    line=dict(width=1, color='black')
                ),
                text=org_row['Organization'],
                textposition="top center",
                name=org_row['Organization'],
                hovertext=f"{org_row['Organization']}<br>{org_row['State']}<br>{org_row['Description']}",
                hoverinfo='text'
            ))
    
    # Update layout
    fig.update_layout(
        geo=dict(
            scope='usa',
            projection_type='albers usa',
            showland=True,
            landcolor='rgb(240, 240, 240)',
            countrycolor='rgb(204, 204, 204)',
        ),
        showlegend=True,
        height=600,
        margin=dict(l=0, r=0, t=30, b=0),
        title=dict(
            text='Organizations by State',
            x=0.5,
            y=0.95
        )
    )
    
    return fig

# Streamlit UI
st.title('Organization-State Network Analyzer')

# Text input area
text_input = st.text_area(
    "Paste your content here:",
    height=300,
    help="Paste the text containing organization and state information."
)

if text_input:
    # Process the text
    df = process_text(text_input)
    
    # Create a list of all unique states
    all_states = set()
    for state_list in df['States']:
        all_states.update([s.strip() for s in state_list.split(',')])
    
    # State filter dropdown
    selected_state = st.selectbox(
        'Filter by State:',
        ['All States'] + sorted(list(all_states))
    )
    
    # Filter the dataframe based on selected state
    if selected_state != 'All States':
        filtered_df = df[df['States'].str.contains(selected_state)]
    else:
        filtered_df = df
    
    # Create and display the map
    st.plotly_chart(create_state_org_map(df, selected_state), use_container_width=True)
    
    # Display the filtered dataframe
    st.subheader('Analyzed Data')
    st.dataframe(filtered_df)
    
    # Display some statistics
    st.subheader('Summary Statistics')
    col1, col2 = st.columns(2)
    with col1:
        st.metric('Total Organizations', len(df))
    with col2:
        st.metric('Total States', len(all_states))
    
    # Download button for CSV
    csv = filtered_df.to_csv(index=False)
    st.download_button(
        label="Download data as CSV",
        data=csv,
        file_name="organization_state_data.csv",
        mime="text/csv"
    )
