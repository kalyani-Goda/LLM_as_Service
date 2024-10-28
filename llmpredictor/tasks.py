from celery import shared_task
from .models import GradingRequest
from .apps import PredictorConfig
from .services.grading_bt import grade_submissions
from .services.dataset_utils import extract_llm_ratings

@shared_task(bind=True)
def query_codellama(self, request_id, submissions, problem_statement, criterion_info, **kwargs):
    print("Initiating auto evaluation")
    PredictorConfig.initialize()

    tokenizer = PredictorConfig.tokenizer
    model = PredictorConfig.model
    device = PredictorConfig.device

    if tokenizer is None or model is None:
        raise ValueError("Tokenizer or model not initialized.")
    print("\nAll values initialized correctly\n")

    # Submissions files for the grading (id and content)
    submissions_for_grade = {key: value["content"] for key, value in submissions.items()}

    # Submissions files for the grading (id and content)
    submissions_file_id = {key: value["file_name"] for key, value in submissions.items()}

    # Get predictions
    grades = grade_submissions(
        tokenizer=tokenizer, model=model, device=device, problem_statement=problem_statement,
        submissions=submissions_for_grade, criterion_info=criterion_info, **kwargs
    )

    combined_json = {}
    try:
        rating_id_map = {}
        criterion_description = {}

        # Create maps for criterion and ratings
        for criterion_obj in criterion_info:
            raw_options = criterion_obj["Ratings"]
            criterion_id = str(criterion_obj["id"])
            criterion_name = str(criterion_obj["description"])
            criterion_description[criterion_id] = criterion_name
            rating_id_map[criterion_id] = {option["title"]: option["description"] for option in raw_options}
        
        # Prepare combined JSON output
        for criterion_id, response in grades.items():
            llm_ratings = extract_llm_ratings("", "", response)
            cllm_ratings = {}
            for student_id, result in llm_ratings.items():
                rating, reasoning = result
                file_name = submissions_file_id[student_id]
                cllm_ratings[file_name] = {
                    "Model choosen Rating": rating_id_map[criterion_id][rating],
                    "Reasoning": reasoning
                }
                llm_ratings[student_id] = {
                    "Model choosen Rating": rating_id_map[criterion_id][rating],
                    "Reasoning": reasoning
                }
            combined_json[criterion_description[criterion_id]] = cllm_ratings

    except Exception as e:
        grading_request = GradingRequest.objects.get(request_id=request_id)
        grading_request.status = "FAILED"
        grading_request.save()
        raise e

    # Update the database with results
    grading_request = GradingRequest.objects.get(request_id=request_id)
    grading_request.results = combined_json
    grading_request.status = "COMPLETED"
    grading_request.save()

    return combined_json