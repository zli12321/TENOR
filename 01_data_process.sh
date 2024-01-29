#!/bin/bash

# First process the data
python ./flask_app/data_process.py \
       --doc_dir ./flask_app/Data/bills/congressional_bill_train.json \
       --save_path ./flask_app/Data/bills/congressional_bill_train_processed.pkl \
       --new_json_path ./flask_app/Data/bills/congressional_bill_train.json

