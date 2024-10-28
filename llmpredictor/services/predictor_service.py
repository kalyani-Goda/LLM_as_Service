import json
import time
from .serializers import FileUploadSerializer
import zipfile
from .tasks import query_codellama
from .services.dataset_utils import extract_llm_ratings
from django.core.files.base import ContentFile
from .models import GradingRequest
import uuid

