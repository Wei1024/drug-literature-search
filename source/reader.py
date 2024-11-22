from openai import OpenAI
import os
from dotenv import load_dotenv

def process_question(message_content, file_paths):
    load_dotenv()  # Load environment variables from .env file
    openai_api_key = os.getenv("OPENAI_API_KEY")

    client = OpenAI(api_key=openai_api_key)

    vector_store_id = os.getenv("VECTOR_STORE_ID")
    assistant_id = os.getenv("ASSISTANT_ID")

    file_streams = [open(path, "rb") for path in file_paths]

    # Upload files to OpenAI
    file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
        vector_store_id=vector_store_id, files=file_streams
    )
    print(file_batch.status)
    print(file_batch.file_counts)

    # List files in the vector store
    vector_store_files = client.beta.vector_stores.files.list(vector_store_id=vector_store_id)

    # Update assistant with file resources
    assistant = client.beta.assistants.update(
        assistant_id=assistant_id,
        tool_resources={"file_search": {"vector_store_ids": [vector_store_id]}},
    )

    # Create a thread
    thread = client.beta.threads.create(
        messages=[{"role": "user", "content": message_content}]
    )

    # Poll the run for completion
    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread.id, assistant_id=assistant.id
    )

    if run.status == "completed":
        messages = list(client.beta.threads.messages.list(thread_id=thread.id, run_id=run.id))

        if messages and messages[0].content:
            message_content = messages[0].content[0].text
            annotations = message_content.annotations

            # Process annotations for citations
            citations = []
            for index, annotation in enumerate(annotations):
                message_content.value = message_content.value.replace(annotation.text, f"[{index}]")
                if file_citation := getattr(annotation, "file_citation", None):
                    cited_file = client.files.retrieve(file_citation.file_id)
                    citations.append(f"[{index}] {cited_file.filename}")

            # Delete files from the vector store after processing
            for file in vector_store_files.data:
                client.beta.vector_stores.files.delete(
                    vector_store_id=vector_store_id,
                    file_id=file.id
                )

            return message_content.value, citations  # Return processed content and citations

        else:
            return "No content found in the messages.", []

    else:
        # # Delete files even if the run does not complete successfully
        for file in vector_store_files.data:
            client.beta.vector_stores.files.delete(
                vector_store_id=vector_store_id,
                file_id=file.id
            )
        return f"Run status: {run.status}", []


# # Replace these with the actual file paths you want to upload for testing
# file_paths = [
#     "tmp/21-441_Advil%20Allergy-Sinus_BioPharmr.pdf",
#     "tmp/21-441_Advil%20Allergy-Sinus_Pharmr.pdf",
#     "tmp/21-441_Advil%20Allergy-Sinus_Chemr.pdf",
#     "tmp/21-441_Advil%20Allergy-Sinus_Medr.pdf"
# ]

# # Define a sample question or message content
# message_content = "What are the reviewers of each?"
# # Call the process_question function
# result_content, citations = process_question(message_content, file_paths)

# # Output the results
# print("Processed Content:\n", result_content)
# print("\nCitations:\n", citations)