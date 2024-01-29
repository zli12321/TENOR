'''
This file processes the data for models to do topic model or active learning
'''
import pandas as pd
import spacy
import re
from spacy.lang.en.stop_words import STOP_WORDS
import pickle
import argparse
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
import os
import json
from tqdm import tqdm


'''
Put your data into json format that could be read by pandas
'''
class Preprocessing():
    def __init__(self, data_path):
        print('Processing data...')
        df = pd.read_json(data_path)
        self.df = df
        data = df.text.values.tolist()
        self.data = data
        self.texts = data
        self.indices_to_void = []

        
        '''
        If the data is already processed and saved in a file, the directly loads from 
        the pickle file to speed up the processing step, which is about 10 minutes for
        the congressional bill dataset
        '''
        nlp = spacy.load('en_core_web_sm')
        nlp.add_pipe('sentencizer')

        docs = []
        # Wrap `tqdm` around `data` to create a progress bar
        for doc in tqdm(data):
            # Process each item with `nlp` and append to `docs` list
            docs.append(nlp(doc))


        print('expanding stopwords')
        stop_words = STOP_WORDS
        self.data_words_nonstop, self.word_spans = [], []

    
        '''
        Use TF-IDF to add words above certain threathold 
        to the stopwords list
        '''
        print('tf-idf filtering words')
        tf_idf_words = self.get_filtered_words(data, 3)

        stop_words = stop_words.union(tf_idf_words)

        print('stopwords')
        print(stop_words)
        print('----')
        print(len(stop_words))

        
        '''
        create a list of tokenized words and spans associated witht the words
        newsgroup dataset is very messy with a lot of punctuations and unwanted
        characters, treat it differntly
        '''
        if 'newsgroup' in data_path:
            for i, doc in enumerate(docs):
                temp_doc = []
                temp_span = []
                for token in doc:
                    if not len(str(token)) == 1 and (re.search('[a-z0-9]+',str(token))) \
                        and not token.pos_ == 'PROPN' and not token.is_digit and not token.is_space \
                                                    and str(token).lower() not in stop_words and str(token).strip() != "":
                            temp_doc.append(token.lemma_.lower())
                            temp_span.append((token.idx, token.idx + len(token)))
                    

                self.data_words_nonstop.append(temp_doc)
                self.word_spans.append(temp_span)   
        else:
            for i, doc in enumerate(docs):
                temp_doc = []
                temp_span = []
                for token in doc:
                    if (re.search('[a-z0-9]+',str(token))) \
                        and not len(str(token)) == 1 and not token.is_digit and not token.is_space \
                            and str(token).lower() not in stop_words and str(token).strip() != "":
                        temp_doc.append(token.lemma_.lower())
                        temp_span.append((token.idx, token.idx + len(token)))
        
                self.data_words_nonstop.append(temp_doc)
                self.word_spans.append(temp_span)
                

        filtered_datawords_nonstop = [[''.join(char for char in tok if char.isalpha() or char.isspace()) for tok in doc] for doc in self.data_words_nonstop]
        self.data_words_nonstop = filtered_datawords_nonstop

        print('length of filtered documents is ', len(filtered_datawords_nonstop))
        
     
    '''
    return a list of low importance words using tf-id
    '''
    def get_filtered_words(self, text, threthold):
        vectorizer = TfidfVectorizer()

        vectorizer.fit(text)
        # Get feature names and their idf values
        feature_names = vectorizer.get_feature_names_out()
        idf_values = vectorizer.idf_
        low_importance_words = [word for word, idf in zip(feature_names, idf_values) if idf <= threthold]
        return low_importance_words


    '''
    Save the processed data as tokens to perform topic modeling
    '''
    def save_data(self, save_path):
        print('saving data...')
        print(self.data_words_nonstop[0])
        result = {}
         

        result['datawords_nonstop'] = [ele for i, ele in enumerate(self.data_words_nonstop) if i not in self.indices_to_void]
        result['spans'] = [ele for i, ele in enumerate(self.word_spans) if i not in self.indices_to_void]
       
        '''
        Save the processed texts and spans of the keywords to display to users into a pickle file
        '''
        with open(save_path, 'wb+') as outp:
            pickle.dump(result, outp)

        print('processed data length', len(result['datawords_nonstop']))

    '''
    Currently not being used
    '''
    def convert_clean_data_to_json(self, save_path):
        processed_test_data = [' '.join(doc) for doc in self.data_words_nonstop]
        result = []
        for i in range(len(processed_test_data)):
            curr = {'texts': processed_test_data[i]}
            result.append(curr)

        df = pd.DataFrame(result)

        df.to_json(save_path, orient='records', lines=False)

    def check_empty(self, lst):
        return all(item == "" for item in lst)

    # def contains

    '''
    Dumpy the remaining documents after processing to a new json file
    '''
    def dump_new_json(self, save_path):
        result = dict()
        result['text'] = dict()
        counter = 0
        '''
        also try to save the labels if they exist
        '''
        try:
            labels = self.df.label.values.tolist()
            sub_labels = self.df.sub_labels.tolist()
            result['label'] = dict()
            result['sub_labels'] = dict()
        except:
            print('no labels for this dataset')
            pass

        '''
        Remove the documents that have fewer than 10 tokens after processing
        '''
        for i, row in enumerate(self.data):
            if len(self.data[i].split()) > 10 and len(self.data_words_nonstop[i]) > 4 and self.check_empty(self.data_words_nonstop[i]) == False:
                result['text'][str(counter)] = self.data[i]

                if 'label' in result: result['label'][str(counter)] = labels[i]
                if 'sub_labels' in result: result['sub_labels'][str(counter)] = sub_labels[i]
                counter += 1
            else:
                self.indices_to_void.append(i)

        with open(save_path, "w") as outfile:
            json.dump(result, outfile)


def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument("--doc_dir", help="Where we read the source documents",
                       type=str, default="./Data/bills/congressional_bill_train.json", required=False)
    argparser.add_argument("--save_path", help="Save processed the data for topic modeling",
                       type=str, default='./Data/bills/congressional_bill_train_processed.pkl', required=False)
    argparser.add_argument("--new_json_path", help="The original json file will have documents removed after processing, save\
                           the new json file for topc model",
                       type=str, default='./Data/bills/congressional_bill_train.json', required=False)
    
    args = argparser.parse_args()

    process_obj = Preprocessing(args.doc_dir)
    process_obj.dump_new_json(args.new_json_path)
    process_obj.save_data(args.save_path)

if __name__ == "__main__":
    main()
