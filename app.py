import streamlit as st
import requests

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

if submit_button:
    if not brand_name_input.strip():
        st.warning("Please enter a valid drug brand name.")
    else:
        # Show a spinner while fetching data
        with st.spinner('Fetching data from FDA OpenFDA API...'):
            # Construct the API URL
            api_url = f'https://api.fda.gov/drug/drugsfda.json?search=openfda.brand_name:"{brand_name_input}"&limit=100'
            
            try:
                response = requests.get(api_url, timeout=10)
                response.raise_for_status()  # Raise an error for bad status codes
                data = response.json()
                
                results = data.get('results', [])
                
                orig_submissions = []
                
                for result in results:
                    submissions = result.get('submissions', [])
                    brand_names = result.get('openfda', {}).get('brand_name', ["N/A"])
                    brand_names_str = ", ".join(brand_names)
                    
                    for submission in submissions:
                        if submission.get('submission_type') == "ORIG":
                            # Extract relevant fields
                            submission_info = {
                                "Brand Name": brand_names_str,
                                "Submission Type": submission.get("submission_type", "N/A"),
                                "Submission Number": submission.get("submission_number", "N/A"),
                                "Submission Status": submission.get("submission_status", "N/A"),
                                "Submission Status Date": submission.get("submission_status_date", "N/A"),
                                "Review Priority": submission.get("review_priority", "N/A"),
                                "Class Code": submission.get("submission_class_code", "N/A"),
                                "Class Description": submission.get("submission_class_code_description", "N/A"),
                                "Application Number": result.get("application_number", "N/A"),
                                "Sponsor Name": result.get("sponsor_name", "N/A"),
                            }
                            
                            # Optionally, include URLs of application documents
                            app_docs = submission.get("application_docs", [])
                            docs_info = []
                            for doc in app_docs:
                                doc_type = doc.get("type", "N/A")
                                doc_url = doc.get("url", "")
                                if doc_url:
                                    docs_info.append(f"[{doc_type}]({doc_url})")
                                else:
                                    docs_info.append(doc_type)
                            submission_info["Application Documents"] = ", ".join(docs_info) if docs_info else "N/A"
                            
                            orig_submissions.append(submission_info)
                
                if orig_submissions:
                    st.success(f"Found {len(orig_submissions)} original submission(s) for brand name '{brand_name_input}'.")
                    
                    for idx, submission in enumerate(orig_submissions, 1):
                        # Set the expander title to the Brand Name
                        expander_title = submission['Brand Name']
                        with st.expander(f"{expander_title}"):
                            submission_md = f"""
### Submission Details

- **Brand Name**: {submission['Brand Name']}
- **Submission Type**: {submission['Submission Type']}
- **Submission Number**: {submission['Submission Number']}
- **Submission Status**: {submission['Submission Status']}
- **Submission Status Date**: {submission['Submission Status Date']}
- **Review Priority**: {submission['Review Priority']}
- **Class Code**: {submission['Class Code']}
- **Class Description**: {submission['Class Description']}
- **Application Number**: {submission['Application Number']}
- **Sponsor Name**: {submission['Sponsor Name']}

### Application Documents
{submission['Application Documents']}
"""
                            st.markdown(submission_md)
                    
                    # Optionally, allow users to download the data as Markdown
                    download_md = ""
                    for idx, submission in enumerate(orig_submissions, 1):
                        download_md += f"## Submission {idx}: {submission['Brand Name']}\n\n"
                        download_md += f"- **Brand Name**: {submission['Brand Name']}\n"
                        download_md += f"- **Submission Type**: {submission['Submission Type']}\n"
                        download_md += f"- **Submission Number**: {submission['Submission Number']}\n"
                        download_md += f"- **Submission Status**: {submission['Submission Status']}\n"
                        download_md += f"- **Submission Status Date**: {submission['Submission Status Date']}\n"
                        download_md += f"- **Review Priority**: {submission['Review Priority']}\n"
                        download_md += f"- **Class Code**: {submission['Class Code']}\n"
                        download_md += f"- **Class Description**: {submission['Class Description']}\n"
                        download_md += f"- **Application Number**: {submission['Application Number']}\n"
                        download_md += f"- **Sponsor Name**: {submission['Sponsor Name']}\n\n"
                        download_md += f"### Application Documents\n{submission['Application Documents']}\n\n---\n\n"
                    
                    st.download_button(
                        label="📥 Download Submissions as Markdown",
                        data=download_md,
                        file_name=f"{brand_name_input}_FDA_ORIG_Submissions.md",
                        mime='text/markdown',
                    )
                else:
                    st.info(f"No original submissions (`submission_type`: 'ORIG') found for brand name '{brand_name_input}'.")
            
            except requests.exceptions.HTTPError as http_err:
                if response.status_code == 404:
                    st.error(f"No data found for brand name '{brand_name_input}'. Please check the brand name and try again.")
                else:
                    st.error(f"HTTP error occurred: {http_err}")
            except requests.exceptions.Timeout:
                st.error("The request timed out. Please try again later.")
            except requests.exceptions.RequestException as e:
                st.error(f"An error occurred while fetching data: {e}")
            except ValueError:
                st.error("Error parsing the response. The API might have returned unexpected data.")
