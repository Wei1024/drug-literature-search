from openai import OpenAI
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Access the OpenAI API key
openai_api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=openai_api_key)

vector_store_id = "vs_CZ8iQ33pren9nJCVmJWYAIKU"
assistant_id = "asst_irHZYkP29dGAn684wP0CIM6D"

# Ready the files for upload to OpenAI
file_paths = ["data/test_clinical_review.pdf"]
file_streams = [open(path, "rb") for path in file_paths]

# Use the upload and poll SDK helper to upload the files, add them to the vector store,
# and poll the status of the file batch for completion.
file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
    vector_store_id=vector_store_id, files=file_streams
)

# Print status and file counts to check the result of this operation
print(file_batch.status)
print(file_batch.file_counts)

vector_store_files = client.beta.vector_stores.files.list(vector_store_id=vector_store_id)

for file in vector_store_files.data:
    print(f"File ID: {file.id}")

assistant = client.beta.assistants.update(
    assistant_id=assistant_id,
    tool_resources={"file_search": {"vector_store_ids": [vector_store_id]}},
)

# Create a thread and attach the file to the message
thread = client.beta.threads.create(
    messages=[
        {
            "role": "user",
            "content": "Does it mention any research results for children?"
        }
    ]
)

# Print tool resources to check if file search is available
print(thread.tool_resources.file_search)

# Use the create and poll SDK helper to create a run and poll the status
run = client.beta.threads.runs.create_and_poll(
    thread_id=thread.id, assistant_id=assistant.id
)

# Ensure the run completed before processing the messages
if run.status == "completed":
    # Fetch messages from the thread
    messages = list(client.beta.threads.messages.list(thread_id=thread.id, run_id=run.id))

    if messages and messages[0].content:  # Check if messages have content
        message_content = messages[0].content[0].text
        annotations = message_content.annotations

        # Process annotations and replace text with citation markers
        citations = []
        for index, annotation in enumerate(annotations):
            message_content = message_content.value.replace(annotation.text, f"[{index}]")
            if file_citation := getattr(annotation, "file_citation", None):
                cited_file = client.files.retrieve(file_citation.file_id)
                citations.append(f"[{index}] {cited_file.filename}")

        # Print the modified message content with citations
        print(message_content)
        print("\n".join(citations))
    else:
        print("No content found in the messages.")
else:
    print(f"Run status: {run.status}")

# Delete files from the vector store after the conversation is complete
for file in vector_store_files.data:
    deleted_vector_store_file = client.beta.vector_stores.files.delete(
        vector_store_id=vector_store_id,
        file_id=file.id
    )
    print(f"Deleted file: {file.id}")

