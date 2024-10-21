
# FDA Drug Submission Lookup App

## Overview

This app allows users to search for a drug's FDA submission by entering the drug's brand name. Once a query is made, the app retrieves FDA-documented reviews on the drug's submission. Users can then select documents they wish to review and ask specific questions, such as "Do they conduct any research on children population?" The app utilizes OpenAI's Assistant API with a File Search function to screen and evaluate documents, even those containing difficult medical terms, to provide insightful answers.

This is a demonstration of how AI can be used to efficiently review and analyze multiple documents, some of which may exceed 200 pages, simultaneously.

## Features

- Search FDA submissions by brand name.
- Select specific documents from the results.
- Ask custom questions about the submission (e.g., research on specific populations).
- AI-powered search through complex documents to answer user queries.

## Installation

To run this app, you need **Python 3.9**. Follow these steps to install and run the app:

### 1. Clone the Repository

```bash
git clone <repository-url>
cd <repository-directory>
```

### 2. Create a Virtual Environment

Use Python 3.9 to create a virtual environment:

```bash
python3.9 -m venv venv
```

Activate the virtual environment:

- On **Windows**:

  ```bash
  venv\Scripts\activate
  ```

- On **macOS/Linux**:

  ```bash
  source venv/bin/activate
  ```

### 3. Install Dependencies

Install the required packages using the `requirements.txt` file:

```bash
pip install -r requirements.txt
```
### 4. Update .env

1. Create an openai api key through their website
2. In the OpenAI API dashboard, create an Assistant and enable the file search function, then attach a vectorstore to it
3. Replace the example with actual api key and IDs in the .env file

### 5. Run the App

Start the app with Streamlit:

```bash
streamlit run app.py
```

## Usage

1. Open the app in your browser after running it.
2. Enter a drug's brand name to search for FDA submissions.
3. Select documents you'd like to review.
4. Enter a question about the documents (e.g., "Do they conduct any research on children population?").
5. The AI will search through the selected documents and provide an answer based on the information found.

## Contact

For any questions or issues, please contact me at weihua.huang24@gmail.com, I am also open to work on different AI or data science related projects to improve the efficiency of your organizations' operation. Please contact me through my email as well to explore the opportunities. 
