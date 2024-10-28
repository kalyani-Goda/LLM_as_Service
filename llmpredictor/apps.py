import gc  # Add this import at the top of your file
from django.apps import AppConfig
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import time
import torch
import warnings
import os
import atexit
import signal
import sys
from django.conf import settings  # Import settings


warnings.filterwarnings("ignore", category=UserWarning, module="torch._utils")

def cleanup(signum=None, frame=None):
    torch.cuda.empty_cache()
    print("Cleaned up resources.")
    sys.exit(0)

class PredictorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'llmpredictor'

    tokenizer = None
    model = None
    # device = "cuda:7"
    device = settings.DEVICE
    _initialized = False

    @classmethod
    def initialize(cls):
        if not cls._initialized:
            # Clean up before initialization
            torch.cuda.empty_cache()
            gc.collect()
            start_time = time.time()
            # model_directory_path = "/raid/ganesh/nagakalyani/nagakalyani/autograding/huggingface_codellama/CodeLlama-7b-Instruct-hf"
            # adapter_path = "/raid/ganesh/nagakalyani/nagakalyani/autograding/huggingface_codellama/bodhitree_ai/ai_bodhitree/llmpredictor/services/models/final_checkpoint"
            # Use the model and adapter paths from settings
            model_directory_path = settings.MODEL_DIRECTORY_PATH
            # adapter_path = "/raid/ganesh/nagakalyani/bodhitree_ai/bodhitree_ai/llmpredictor/services/models/final_checkpoint"
            adapter_path = settings.ADAPTER_PATH
            cls.tokenizer = AutoTokenizer.from_pretrained(model_directory_path)
            cls.tokenizer.pad_token = cls.tokenizer.eos_token
            cls.model = AutoModelForCausalLM.from_pretrained(model_directory_path, torch_dtype=torch.float32, device_map=cls.device).eval()
            cls.tokenizer.padding_side = "right"
            cls.model = PeftModel.from_pretrained(cls.model, adapter_path)
            cls.model.eval()
            end_time = time.time()
            print(f"Loaded model and tokenizer in {end_time - start_time} seconds")
            cls._initialized = True

    def ready(self):
        if not os.environ.get('RUN_MAIN'):
            self.initialize()

atexit.register(cleanup)
signal.signal(signal.SIGTERM, cleanup)
signal.signal(signal.SIGINT, cleanup)

