from django.db import models

class GradingRequest(models.Model):
    problem_statement = models.TextField()
    rubric = models.JSONField()  # Assuming you are storing rubric as JSON
    submission_zip = models.FileField(upload_to='submissions/')
    request_id = models.CharField(max_length=255, blank=True, null=True)
    cellery_task_id = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=50, default="PENDING")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    results = models.JSONField(blank=True, null=True)  # New field for storing results


    def __str__(self):
        return f"GradingRequest {self.id} - Status: {self.status}"
