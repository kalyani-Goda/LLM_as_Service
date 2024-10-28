python3 model_utils.py \
    --model_size "7b" \
    --user_prompt_path sample_user_prompt.txt \
    --system_prompt_path system_prompts/zero_shot_sys_prompt.txt \
    --device "cuda:0" \
    --run_inference True