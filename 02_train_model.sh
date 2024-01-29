#!/bin/bash

python ./flask_app/Topic_Models/train_models.py \
        --num_topics 35 \
        --num_iters 3000 \
        --model_type LDA \
        --load_data_path ./flask_app/Data/bills/congressional_bill_train_processed.pkl\
        --raw_text_path ./flask_app/Data/bills/congressional_bill_train.json \
        --save_trained_model_path ./flask_app/Topic_Models/trained_models/LDA_35.pkl

python ./flask_app/Topic_Models/train_models.py \
        --num_topics 35 \
        --num_iters 3000 \
        --model_type SLDA \
        --load_data_path ./flask_app/Data/bills/congressional_bill_train_processed.pkl\
        --raw_text_path ./flask_app/Data/bills/congressional_bill_train.json \
        --save_trained_model_path ./flask_app/Topic_Models/trained_models/SLDA_35.pkl

python ./flask_app/Topic_Models/train_models.py \
        --num_topics 35 \
        --num_iters 250 \
        --model_type CTM \
        --load_data_path ./flask_app/Data/bills/congressional_bill_train_processed.pkl\
        --raw_text_path ./flask_app/Data/bills/congressional_bill_train.json \
        --save_trained_model_path ./flask_app/Topic_Models/trained_models/CTM_35.pkl

