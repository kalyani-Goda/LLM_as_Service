import base64
from email.mime.text import MIMEText
from googleapiclient.discovery import build
import pickle
import streamlit as st
import requests
import zipfile
import io
import json
import pandas as pd

# Update API base URL to match the Django backend
API_BASE_URL = "http://10.195.100.5:8007/llmpredictor"  # Adjust if necessary

# Ensure session state is initialized
if 'page' not in st.session_state:
    st.session_state['page'] = 'home'

# Load Gmail API credentials from the token.pickle file
SCOPES = ['https://www.googleapis.com/auth/gmail.send']
creds = None
with open('token.pickle', 'rb') as token:
    creds = pickle.load(token)

# Create the Gmail API client
service = build('gmail', 'v1', credentials=creds)

# Function to send an email with the task ID using Gmail API
def send_email(recipient_email, task_id):
    message = MIMEText(f"Hello,\n\nYour grading request has been successfully received.\nYour Task ID is: {task_id}\n\nYou can use this Task ID to check the grading status after some time.\n\nThank you!")
    message['to'] = recipient_email
    message['from'] = 'tabuddy2024@gmail.com'
    message['subject'] = "Your Grading Request Task ID"
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

    try:
        message = (service.users().messages().send(userId="me", body={'raw': raw_message}).execute())
        print(f"Message sent successfully: {message['id']}")
    except Exception as e:
        print(f"An error occurred: {e}")
        raise

# Home Page
def home_page():
    st.title("Welcome to the Automatic Grading System")
    st.image("https://www.your-image-url.com/hero-image.jpg", use_column_width=True)
    st.write("""
    This application allows you to automatically grade programming assignments based on various criteria.
    You can either make a new grading request or check the status of a previous request.

    ### How to Use:
    - **New Grading Request**: Upload a problem statement, a rubric, and the submissions to automatically grade.
    - **Check Grading Status**: Enter your task ID to view the progress or download results.
    """)

    # Add buttons to navigate
    if st.button("New Grading Request"):
        st.session_state['page'] = 'new_request'
    elif st.button("Check Grading Status"):
        st.session_state['page'] = 'check_status'

# New Grading Request Page
def new_grading_request():
    st.title("New Grading Request")

    # Step 1: Upload Problem Statement
    problem_statement = st.text_area("Enter Problem Statement:")

    # Step 2: Enter Email Address
    email = st.text_input("Enter Your Email Address:")

    # Step 3: Select Model
    model_selection = st.selectbox("Select Grading Model", ["CodeLlama", "CodeStral", "AnotherModel"])

    # Step 4: Create Rubric (Dynamic Table)
    st.subheader("Create Rubric Criteria")

    # Number of criteria
    rubric_count = st.number_input("Number of Criteria", min_value=1, max_value=10, value=1, step=1)
    rubric = []

    # Loop through each criterion
    for i in range(int(rubric_count)):
        st.write(f"### Criterion {i+1}")
        id = i + 1
        criterion_title = f"criterion_{id}"
        # Input for the name of the criterion
        criterion_name = st.text_input(f"Enter name for Criterion {i+1}:", key=f"criterion_name_{i}")

        # Input for the max marks for the criterion
        max_marks = st.number_input(f"Max Marks for Criterion {i+1}", min_value=1.0, step=0.5, key=f"max_marks_{i}")

        # Input for the number of rating levels (dynamic, based on user input)
        rating_count = st.number_input(f"Number of Ratings for Criterion {i+1}", min_value=1, value=1, step=1, key=f"rating_count_{i}")

        # Create a list to store rating levels and their associated marks
        ratings = []
        for j in range(int(rating_count)):
            letter = chr(65 + j)  # 65 is the ASCII value of 'A', 66 for 'B', and so on
            rating_title = f"Rating {letter}"  # Generate rating title like 'Rating A', 'Rating B', etc.
            st.write(f"{rating_title} for Criterion {i+1}")
            rating_name = st.text_input(f"Enter Rating {letter} Name (e.g., Excellent, Good, Poor):", key=f"rating_name_{i}_{j}")
            rating_marks = st.number_input(f"Enter Marks for {rating_name}:", min_value=0.0, step=0.5, key=f"rating_marks_{i}_{j}")
            ratings.append({
                "title": letter,
                "description": rating_name,
                "marks": rating_marks
            })

        # Append this criterion along with its max marks and ratings to the rubric
        rubric.append({
            "id": id,
            "title": criterion_title,
            "description": criterion_name,
            "max_marks": max_marks,
            "Ratings": ratings
        })

    # Step 5: Upload Zip File with Submissions
    st.subheader("Upload Submissions")
    zip_file = st.file_uploader("Upload a Zip file containing .cpp submissions", type=["zip"])

    # Step 6: Submit grading task
    if st.button("Submit Grading Request"):
        if problem_statement and rubric and zip_file and email:
            try:
                # Prepare data for Django backend
                data = {
                    'problem_statement': problem_statement,
                    'criteria': json.dumps(rubric),  # Convert rubric list to JSON string
                    'model': model_selection
                }

                # # Send the files and other data to the backend
                # files = {key: content for key, content in submissions.items()}

                 # Send the zip file to the backend
                files = {'submission_zip': zip_file}

                # Send POST request to backend Django server
                response = requests.post(f"{API_BASE_URL}/llmpredict/", data=data, files=files)
                if response.status_code == 202:
                    response_data = response.json()  # Parse the response as JSON
                    task_id = response_data.get("task_id")
                    
                    # Send email to the user with the task ID
                    try:
                        send_email(email, task_id)
                        st.success(f"Grading request submitted successfully! Task ID has been sent to {email}")
                    except Exception as e:
                        st.error(f"Grading request submitted, but failed to send email: {str(e)}")
                else:
                    st.error("Error submitting the grading request.")
            except zipfile.BadZipFile:
                st.error("Uploaded file is not a valid zip file.")
        else:
            st.error("Please complete all fields before submitting.")

    # Back button to return to home page
    if st.button("Back to Home"):
        st.session_state['page'] = 'home'

# Check Grading Status Page
def check_grading_status():
    st.title("Check Grading Status")

    # Step 1: Enter Task ID
    task_id = st.text_input("Enter Task ID to check status:")
    if st.button("Check Status"):
        if task_id:
            # Send GET request to check status from Django server
            response = requests.get(f"{API_BASE_URL}/llmpredict/", params={'task_id': task_id})
            if response.status_code == 200:
                result = response.json()
                if result:
                    st.success("Grading task completed! Here are the results:")
                    st.json(result)  # Display the results in JSON format

                    # Convert the result to a DataFrame with the correct format
                    rows = []

                    # Iterate through student submissions
                    for student_id in result[next(iter(result))].keys():
                        row = {"submission_id": student_id}

                        # Iterate through all criteria and add columns accordingly
                        for idx, (criterion, student_responses) in enumerate(result.items(), start=1):
                            if student_id in student_responses:
                                response_data = student_responses[student_id]
                                row[f"criterion_{idx}"] = criterion
                                row[f"Choosen_rating_{idx}"] = response_data["Model choosen Rating"]
                                row[f"Model_reasoning_{idx}"] = response_data["Reasoning"]

                        rows.append(row)

                    # Convert the list of rows into a DataFrame
                    df = pd.DataFrame(rows)

                    # Reorder columns to match the required format
                    ordered_columns = ["submission_id"]
                    for idx in range(1, len(result) + 1):
                        ordered_columns.extend([
                            f"criterion_{idx}",
                            f"Choosen_rating_{idx}",
                            f"Model_reasoning_{idx}"
                        ])
                    df = df[ordered_columns]

                    # Save the DataFrame to a CSV file in-memory
                    csv_buffer = io.StringIO()
                    df.to_csv(csv_buffer, index=False)
                    csv_data = csv_buffer.getvalue()

                    # Provide a link to download the CSV file
                    st.download_button(
                        label="Download CSV File",
                        data=csv_data,
                        file_name="grading_results_correct_format.csv",
                        mime="text/csv"
                    )
                else:
                    st.info("Task is still in progress, please check after some time.")
            else:
                st.error("Error fetching task status.")
        else:
            st.error("Please enter a task ID.")

    # Back button to return to home page
    if st.button("Back to Home"):
        st.session_state['page'] = 'home'

# Main App Logic to handle navigation
if st.session_state['page'] == 'home':
    home_page()
elif st.session_state['page'] == 'new_request':
    new_grading_request()
elif st.session_state['page'] == 'check_status':
    check_grading_status()
