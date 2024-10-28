from django.urls import path
from llmpredictor.views import PredictorView

app_name = 'llmpredictor'

urlpatterns = [
    path('llmpredict/', PredictorView.as_view(), name='predictor'),
]
