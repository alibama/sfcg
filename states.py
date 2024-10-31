import streamlit as st
import pandas as pd
import re
from collections import defaultdict

def extract_states(text):
    """Extract state abbreviations from text."""
    # Dictionary of state abbreviations
    state_abbrevs = {
        'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
        'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
        'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
        'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
        'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY'
    }
    
    # Find all state abbreviations in the text
    found_states = set()
    for state in state_abbrevs:
        if re.search(r'\b' + state + r'\b', text):
            found_states.add(state)
    
    return list(found_states)

def extract_organization(text):
    """Extract organization name from the beginning of a bullet point."""
    # Look for organization name at start of line, typically before a parenthesis
    match = re.search(r'^\s*\*?\s*([^()]+?)(?:\s*\([^)]+\))?(?=\s+(?:is|has|have|works|working|connects|recruiting|mobilized|organized))', text)
    if match:
        return match.group(1).strip()
    return None

def process_text(raw_text):
    """Process raw text into structured data."""
    organizations = []
    states = []
    descriptions = []
    
    # Split text into lines and process each line
    lines = raw_text.split('\n')
    for line in lines:
        line = line.strip()
        if line.startswith('*') or line != '':  # Process non-empty lines and bullet points
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
