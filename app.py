import streamlit as st
import requests
import pandas as pd

# Set page configuration
st.set_page_config(
    page_title="FDA Drug Submission Lookup",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Title of the app
st.title("📋 FDA Drug Submission Lookup")

# Description
st.markdown("""
Enter a **drug brand name** to retrieve its FDA submission details. Only submissions with `submission_type` as **ORIG** will be displayed.
""")

# Sidebar for additional info or settings (optional)
st.sidebar.header("About")
st.sidebar.info(
    """
    This app uses the [FDA OpenFDA API](https://open.fda.gov/apis/drug/drugsfda/) to fetch drug submission data based on the brand name provided by the user.
    
    **Disclaimer:** Do not rely on OpenFDA to make decisions regarding medical care. While efforts are made to ensure data accuracy, all results are unvalidated.
    """
)

# Input form
with st.form(key='drug_form'):
    brand_name_input = st.text_input("Enter Drug Brand Name", value="", placeholder="e.g., Advil")
    submit_button = st.form_submit_button(label='Search')

# Initialize session state to hold the fetched data
if 'submission_data' not in st.session_state:
    st.session_state.submission_data = None

# Check if the submit button is clicked
if submit_button:
    if not brand_name_input.strip():
        st.warning("Please enter a valid drug brand name.")
    else:
        # Show a spinner while fetching data
        with st.spinner('Fetching data from FDA OpenFDA API...'):
            fda_api_key="l5tsOTUMyirqfKR2CSFnEFi2ot6B3LEYaaTejVvN"
            api_url = f'https://api.fda.gov/drug/drugsfda.json?api_key={fda_api_key}&search=openfda.brand_name:"{brand_name_input}"&limit=100'
            
            try:
                response = requests.get(api_url, timeout=10)
                response.raise_for_status()  # Raise an error for bad status codes
                data = response.json()
                results = data.get('results', [])
                
                orig_submissions = []
                
                for result in results:
                    submissions = result.get('submissions', [])
                    brand_names = result.get('openfda', {}).get('brand_name', ["N/A"])
                    generic_names = result.get('openfda', {}).get('generic_name', ["N/A"])
                    brand_names_str = ", ".join(brand_names)
                    generic_names_str = ", ".join(generic_names)
                    
                    # Modify submission_info to store each link as a separate record
                    for submission in submissions:
                        if submission.get('submission_type') == "ORIG":
                            brand_names_str = ", ".join(brand_names)
                            generic_names_str = ", ".join(generic_names)
                            app_docs = submission.get("application_docs", [])
                            for doc in app_docs:
                                doc_url = doc.get("url", "")
                                doc_type = doc.get("type", "N/A")
                                if doc_url:
                                    submission_info = {
                                        "Brand Name": brand_names_str,
                                        "Generic Name": generic_names_str,
                                        "Review Priority": submission.get("review_priority", "N/A"),
                                        "Application Number": result.get("application_number", "N/A"),
                                        "Sponsor Name": result.get("sponsor_name", "N/A"),
                                        "Document Type": doc_type,
                                        "Application Documents": doc_url,
                                    }
                                    orig_submissions.append(submission_info)

                
                if orig_submissions:
                    # Save data in session state
                    st.session_state.submission_data = pd.DataFrame(orig_submissions)
                    st.success(f"Found {len(orig_submissions)} original submission(s) for brand name '{brand_name_input}'.")
                else:
                    st.session_state.submission_data = None
                    print(results)
                    st.info(f"No original submissions (`submission_type`: 'ORIG') found for brand name '{brand_name_input}'.")
            
            except requests.exceptions.RequestException as e:
                st.error(f"An error occurred while fetching data: {e}")

# Render the DataFrame only if data is available in session state
if st.session_state.submission_data is not None:
    df = st.session_state.submission_data
    column_configuration = {
        "Brand Name": st.column_config.TextColumn("Brand Name", width="medium"),
        "Generic Name": st.column_config.TextColumn("Generic Name", width="medium"),
        "Review Priority": st.column_config.TextColumn("Review Priority", width="small"),
        "Application Number": st.column_config.TextColumn("Application Number", width="medium"),
        "Sponsor Name": st.column_config.TextColumn("Sponsor Name", width="medium"),
        "Document Type": st.column_config.TextColumn("Document Type", width="medium"),
        "Application Documents": st.column_config.LinkColumn(
            display_text="Open Document"
        ),
    }

    # Display the DataFrame with selectable rows
    st.header("All Submissions")
    selection = st.dataframe(
        df,
        hide_index=True,
        column_config=column_configuration,
        use_container_width=True,
        on_select="rerun",
        selection_mode="multi-row",
    )

    # Display selected submissions
    st.header("Selected Submissions")
    if selection and selection.selection:
        selected_rows = selection.selection.rows
        filtered_df = df.iloc[selected_rows]
        st.dataframe(
            filtered_df,
            hide_index=True,
            column_config=column_configuration,
            use_container_width=True,
        )
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Selected Submissions as CSV",
            data=csv,
            file_name=f"{brand_name_input}_Selected_FDA_ORIG_Submissions.csv",
            mime='text/csv',
        )
