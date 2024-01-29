import argparse
from classical_topic_model import Topic_Model
from neural_model import Neural_Model
import pandas as pd

def main():
    # __init__(self, num_topics, model_type, load_data_path, train_len)
    argparser = argparse.ArgumentParser()
    argparser.add_argument("--num_topics", help="number of topics",
                       type=int, default=20, required=False)
    argparser.add_argument("--num_iters", help="number of iterations",
                       type=int, default=1000, required=False)
    argparser.add_argument("--model_type", help="type of the model, SLDA, LDA, CTM, LLDA",
                       type=str, default='LDA', required=False)
    argparser.add_argument("--load_data_path", help="Whether we LOAD the pickle processed data",
                       type=str, default='./flask_app/Data/bills/congressional_bill_train_processed.pkl', required=False)
    argparser.add_argument("--raw_text_path", help="only required for CTM and LLDA. pass in the json file of unprocessed texts",
                       type=str, default='./flask_app/Data/bills/congressional_bill_train.json', required=False)
    argparser.add_argument("--save_trained_model_path", help="The model path to save the trained models",
                       type=str, default='./flask_app/Topic_Models/trained_models/LDA_35.pkl', required=False)


    args = argparser.parse_args()
    


    if args.model_type == 'LDA' or args.model_type == 'SLDA':
        Model = Topic_Model(num_topics=args.num_topics, num_iters=args.num_iters,load_data_path= args.load_data_path, model_type=args.model_type)
        
        Model.train(args.save_trained_model_path)
    elif args.model_type == 'CTM':
        model = Neural_Model(num_topics=args.num_topics, num_iters=args.num_iters,load_data_path= args.load_data_path, model_type=args.model_type)
        df = pd.read_json(args.raw_text_path)
        model.train(args.save_trained_model_path, df.text.values.tolist())

if __name__ == "__main__":
    main()