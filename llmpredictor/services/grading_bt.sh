TASK=$1

python3 grading_bt.py \
    --system_prompt_path system_prompts/zero_shot_sys_prompt.txt  \
    --context_path /raid/ganesh/nagakalyani/nagakalyani/autograding/huggingface_codellama/ICER_Code/queue/$TASK/ps.txt \
    --lab_folder_path /raid/ganesh/nagakalyani/nagakalyani/autograding/huggingface_codellama/ICER_Code/queue/$TASK --device "cuda:3" \
    --criterion_info /raid/ganesh/nagakalyani/nagakalyani/autograding/huggingface_codellama/ICER_Code/queue/$TASK/criteria.json \
    --output_file_path outputs/$TASK \
    --max_length 4096

python3 log_grades.py \
    --results_folder_path outputs/$TASK \
    --criterion_info /raid/ganesh/nagakalyani/nagakalyani/autograding/huggingface_codellama/ICER_Code/queue/$TASK/criteria.json