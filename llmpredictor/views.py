# In llmpredictor/views.py
import os
import uuid
from rest_framework.views import APIView
from rest_framework.response import Response
from celery.result import AsyncResult
from django.http import HttpResponse
from django.conf import settings
from django.core.files.storage import default_storage
import json
import time
from .serializers import FileUploadSerializer
import zipfile
from .tasks import query_codellama
from .services.dataset_utils import extract_llm_ratings
from django.core.files.base import ContentFile
from .models import GradingRequest
import uuid

def home(request):
    return HttpResponse("Welcome to Auto Grading Server")

class PredictorView(APIView):
    def post(self, request):
        start_time = time.time()
        data = request.data

        # Validate request data
        problem_statement = data.get('problem_statement')
        criteria_json = data.get('criteria')
        zip_file = request.FILES.get('submission_zip')
        
        if not problem_statement or not criteria_json or not zip_file:
            return Response({"error": "Missing required fields: problem_statement, criteria, or submission_zip"}, status=400)
        
        # Load criteria
        try:
            criteria = json.loads(criteria_json)
        except json.JSONDecodeError:
            return Response({"error": "Invalid JSON for criteria"}, status=400)
        
        # Extract submissions from the zip file
        submissions_filename = self.extract_submissions_from_zip(zip_file)
        if not submissions_filename:
            return Response({"error": "Invalid zip file"}, status=400)
        
        # Create a unique request ID
        request_id = str(uuid.uuid4())

        # Save grading request to the database
        grading_request = GradingRequest(
            problem_statement=problem_statement,
            rubric=criteria,
            request_id=request_id,
            status="PENDING"
        )
        grading_request.submission_zip.save(zip_file.name, ContentFile(zip_file.read()))
        grading_request.save()

        # Start grading task using Celery
        try:
            task = query_codellama.apply_async(
                args=[request_id, submissions_filename, problem_statement, criteria],
                kwargs={'criterion_name': "", 'max_length': 4096, 'few_shot': False, 'few_shot_examples': 0, 'train_split': 0.7}
            )

            # Update grading request with Celery task ID and status
            grading_request.cellery_task_id = task.id
            grading_request.status = "IN_PROGRESS"
            grading_request.save()
            print(task.id)
            end_time = time.time()
            print("Total time taken:", end_time - start_time)
            return Response({'status_code': 202, 'task_id': task.id}, status=202)
        except Exception as e:
            print(f"Error starting grading task: {e}")
            grading_request.status = "FAILED"
            grading_request.save()
            return Response({"error": "Something went wrong"}, status=500)

    def get(self, request):
        start_time = time.time()
        task_id = request.query_params.get('task_id')

        if not task_id:
            return Response({"error": "task_id is required"}, status=400)

        task_result = AsyncResult(task_id)
        if task_result.status == "SUCCESS":
            end_time = time.time()
            print("Total time taken:", end_time - start_time)
            return Response(task_result.result, status=200)
        else:
            end_time = time.time()
            print("Total time taken:", end_time - start_time)
            return Response({"message": "Task is still pending"}, status=202)

    @staticmethod
    def extract_submissions_from_zip(zip_file):
        submissions = {}
        try:
            with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                unique_id = 1
                for file_info in zip_ref.infolist():
                    if file_info.filename.endswith(".cpp"):
                        with zip_ref.open(file_info) as file:
                            content = file.read().decode('utf-8').strip()
                            file_name = file_info.filename
                            submissions[str(unique_id)] = {
                                "file_name": file_name,
                                "content": content
                            }
                            unique_id += 1
        except zipfile.BadZipFile:
            return None
        return submissions