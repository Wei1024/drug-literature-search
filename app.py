import os
import requests
import shutil
import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
from pathlib import Path
from urllib.parse import urljoin
from source.reader import process_question
from source.utilities import download_pdf, download_from_cfm
import time

# Create a temporary directory
tmp_dir = Path("tmp")
tmp_dir.mkdir(parents=True, exist_ok=True)

# Function to cleanup the tmp folder
def cleanup_tmp_folder(folder_path):
    if folder_path.exists() and folder_path.is_dir():
        max_retries = 3
        retry_delay = 1  # seconds
        
        for retry in range(max_retries):
            try:
                for root, dirs, files in os.walk(folder_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        try:
                            os.chmod(file_path, 0o777)  # Ensure we have permission to delete
                            os.unlink(file_path)
                        except Exception as e:
                            print(f"Error deleting file {file_path}: {e}")
                            continue
                    for dir in dirs:
                        dir_path = os.path.join(root, dir)
                        try:
                            os.rmdir(dir_path)
                        except Exception as e:
                            print(f"Error deleting directory {dir_path}: {e}")
                            continue
                try:
                    os.rmdir(folder_path)
                except Exception as e:
                    print(f"Error deleting root directory {folder_path}: {e}")
                break  # If we get here, cleanup was successful
            except Exception as e:
                if retry < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                else:
                    print(f"Failed to cleanup temporary folder after {max_retries} attempts: {e}")

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
    brand_name_input = st.text_input("Enter Drug Brand Name", value="", placeholder="e.g., Opdivo")
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
        message_content = st.text_area("Enter the message content for processing:", value="")

        # Inside the "Process Application Documents" button
        if st.button("Process Application Documents"):
            downloaded_files = []
            for _, row in filtered_df.iterrows():
                doc_url = row["Application Documents"]
                if doc_url.endswith(".pdf"):
                    st.write(f"Downloading PDF from {doc_url}...")
                    downloaded_file = download_pdf(doc_url, tmp_dir)
                    if downloaded_file:
                        st.write(f"Downloaded: {downloaded_file}")
                        downloaded_files.append(downloaded_file)
                    else:
                        st.write(f"Failed to download {doc_url}")
                elif doc_url.endswith(".cfm"):
                    st.write(f"Scraping and downloading PDFs from {doc_url}...")
                    scraped_files = download_from_cfm(doc_url, tmp_dir)
                    if scraped_files:
                        for file in scraped_files:
                            st.write(f"Downloaded: {file}")
                        downloaded_files.extend(scraped_files)
                    else:
                        st.write(f"No PDF links found or failed to download from {doc_url}.")

            if downloaded_files:
                if message_content.strip():
                    try:
                        # Call the process_question function and capture results
                        processed_content, citations = process_question(message_content, downloaded_files)
                        
                        # Display the results in Streamlit
                        st.subheader("Results from AI")
                        st.markdown(processed_content)

                        if citations:
                            st.subheader("Citations")
                            for citation in citations:
                                st.markdown(citation)
                        
                    except Exception as e:
                        st.error(f"An error occurred during processing: {e}")
                    finally:
                        # Clean up the temporary folder after processing
                        cleanup_tmp_folder(tmp_dir)
                else:
                    st.warning("Please enter a valid message content.")
            else:
                # Clean up the temporary folder if no files were downloaded
                cleanup_tmp_folder(tmp_dir)