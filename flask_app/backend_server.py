from classifier import Active_Learning
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
import pickle
from multiprocessing import Process, Manager
import copy
import random
import os
from Topic_Models.classical_topic_model import Topic_Model
from Topic_Models.neural_model import Neural_Model
import logging


class User():
    '''
    Initialize a user session with needed elements
    '''
    def __init__(self, user_id, raw_texts, model_type, num_topics=35, data_path='./flask_app/Data/bills/congressional_bill_train_processed.pkl', labels=None):
        '''
        user_id: the id of the user in the database
        raw_texts: all the raw texts in a list
        model: the type of model can be LDA, SLDA, or CTM
        num_topics: the number of topics for the topic model
        data_path: the path of the processed dataset
        labels: If you have groundtruth labels and want to measure purity, randindex, and NMI, pass them as a list to 
        the parameter. Else, leave it to be None
        '''
        self.labels = labels if labels is not None else ['null' for i in raw_texts]
        self.user_id = user_id
        self.raw_texts = raw_texts
        self.data_path = data_path
        self.slda_save_path = './flask_app/Topic_Models/trained_models/SLDA_user{}.pkl'.format(self.user_id)
        '''
        Here we use TFIDF unigram as embeddings for the classifier
        '''
        self.vectorizer = TfidfVectorizer(stop_words='english', lowercase=True, ngram_range=(1,1))
        self.updated_model = False
        self.click_tracks = {}
        self.slda_update_freq = 0
        self.purity = -1
        self.RI = -1
        self.NMI = -1
        self.model_type = model_type

        self.vectorizer_idf = self.vectorizer.fit_transform(raw_texts)
        self.user_labels = set()

        if model_type == 'LDA' or model_type == 'SLDA' or model_type == 'CTM':
            self.update_process = None

            model_path = './flask_app/Topic_Models/trained_models/{}_{}.pkl'.format(model_type, num_topics)
            if model_type == 'CTM':
                self.model = Neural_Model(load_model=True, load_data_path=data_path, model_path=model_path, model_type=model_type)
            else:
                self.model = Topic_Model(load_model=True, load_data_path=data_path, model_path=model_path, model_type=model_type)
            self.topics = self.model.print_topics(verbose=False)
               

            # concatenated_features = self.model.concatenate_features(self.model.doc_topic_probas, self.vectorizer_idf)
            # self.concatenated_features = concatenated_features
            self.string_topics = {str(k): v for k, v in self.topics.items()}  
            self.document_probas, self.doc_topic_probas = self.model.group_docs_to_topics()
                
            logging.info(f'Using model {model_type}')

            self.alto = Active_Learning(copy.deepcopy(self.document_probas), self.vectorizer_idf, self.doc_topic_probas)
        else:
            raise('Unsupported Model Type')
      

    '''
    Fetch the document information given a document id. 
    '''
    def get_doc_information(self, doc_id):
        result = dict()
        
        self.click_tracks[str(doc_id)] = 'click'

        if self.model_type == 'LDA' or self.model_type == 'SLDA' or self.model_type == 'CTM':
            topic_distibution, topic_res_num = self.model.predict_doc_with_probs(int(doc_id), self.topics)
            result['topic_order'] = topic_distibution
            # result['topic_keywords'] = topic_keywords
            result['topic'] = self.model.get_word_span_prob(int(doc_id), topic_res_num, 0.001)

            if len(self.user_labels) >= 2:
                preds, dropdown = self.alto.predict_label(int(doc_id))
                result['prediction'] = preds
                result['dropdown'] = dropdown
            else:
                result['prediction'] = ['']
                result['dropdown'] = []
            # logging.info('result', result)

            return result
        elif self.model_type == 'no_topic':
            preds, dropdown = self.alto.predict_label(int(doc_id))
            result['prediction'] = preds
            result['dropdown'] = dropdown

            topics = {"1": {"spans": [], "keywords": []}}
            result['topic'] = topics
            result['topic_order'] = {}

            return result


    '''
    Skip the current recommended document and return the next recommended document
    '''
    def skip_doc(self):
        doc_id, _ = self.alto.recommend_document(True)
        
        return doc_id


    '''
    When the user enters a label for a document, this method automatically returns
    the next recommended document
    '''
    def sub_roundtrip(self, label, doc_id, response_time):
        result = dict()
        self.click_tracks[str(doc_id)] = 'label, recommended {}'.format(self.alto.last_recommended_doc_id)

        if self.model_type == 'SLDA' or self.model_type == 'LDA' or self.model_type == 'CTM':
            if isinstance(label, str):
                logging.info('calling self.label...')
                self.user_labels.add(label)
                self.alto.label(int(doc_id), label)
                        
            selected_document, _ = self.alto.recommend_document(True)
             
            result['document_id'] = str(selected_document)
                    
            logging.info('unique label classes is {}'.format(len(self.user_labels)))
            if len(self.user_labels) >= 2:
                user_purity, user_RI, user_NMI = self.alto.eval_classifier(self.labels)
                self.purity = user_purity
                self.RI = user_RI
                self.NMI = user_NMI
                return user_purity, user_RI, user_NMI, result
            else:
                '''
                If classifier is not initialized yet, all metrics are -1
                '''
                return -1, -1, -1, result
        elif self.model_type == 'no_topic':
            if isinstance(label, str):
                self.user_labels.add(label)
                self.alto.label(int(doc_id), label)
                    
            selected_document, _ = self.alto.recommend_document(True)
            
            # result['raw_text'] = str(random_document)
            result['document_id'] = str(selected_document)

            logging.info('unique user labels length is {}'.format(len(self.user_labels)))
            if len(self.user_labels) >= 2:
                user_purity, user_RI, user_NMI = self.alto.eval_classifier(self.labels)
                self.purity = user_purity
                self.RI = user_RI
                self.NMI = user_NMI
                return user_RI, user_NMI, result
            else:
                return -1, -1, -1, result


    '''
    Retrive the document informaton-topic orders, predictions from the classifier
    to save to the database
    '''      
    def get_doc_information_to_save(self, doc_id):
        result = dict()
        logging.info('getting document information to save...')
        if self.model_type == 'LDA' or self.model_type == 'SLDA' or self.model_type == 'CTM':
            
            topic_distibution, topic_res_num = self.model.predict_doc_with_probs(int(doc_id), self.topics)
            result['topic_order'] = topic_distibution
            result['topics'] = topic_res_num

            if len(self.user_labels) >= 2:
                preds, dropdown = self.alto.predict_label(int(doc_id))
                result['prediction'] = preds
            else:
                result['prediction'] =['No prediction']

            return result
        elif self.model_type == 'no_topic':
            if len(self.user_labels) >= 2:
                preds, dropdown = self.alto.predict_label(int(doc_id))
                result['prediction'] = preds
            else:
                result['prediction'] =['No prediction']
            
            result['topics'] = {}
            result['topic_order'] = {}
       
            return result

    '''
    Reinitialize a slda topic model and train it and save it.
    '''
    def update_slda(self):
        classifier_labels = self.alto.classifier.predict(self.alto.text_vectorizer)
        predicted_labels = {i: classifier_labels[i] for i in range(len(classifier_labels))}

        model = Topic_Model(num_topics=self.num_topics,num_iters=self.num_iter, load_data_path=self.data_path, load_model=False, model_type=self.model_type, user_labels=predicted_labels)
        model.train(model_path=self.slda_save_path)

    '''
    Load the updated SLDA model to the current process
    '''
    def load_updated_model(self):
        try:
            self.model = Topic_Model(load_model=True, load_data_path=self.data_path, model_path=self.slda_save_path, model_type=self.model_type)
            self.topics = self.model.print_topics(verbose=False)

            self.string_topics = {str(k): v for k, v in self.topics.items()}
            # logging.info(self.string_topics)
                            
            self.document_probas, self.doc_topic_probas = self.model.group_docs_to_topics()
            
            # self.word_topic_distributions = self.model.word_topic_distribution

            concatenated_features = self.model.concatenate_features(self.model.doc_topic_probas, self.vectorizer_idf)
            self.concatenated_features = concatenated_features

            self.alto.update_text_vectorizer(self.concatenated_features)

            self.alto.update_doc_probs(copy.deepcopy(self.document_probas), self.doc_topic_probas)

            logging.info('updated new SLDA model')
        except Exception as e:
            logging.info(f"An error occurred loading: {e}")
            pass

        with Manager() as manager:
            self.update_process = Process(target=self.update_slda)
            self.update_process.start()

    '''
    When the user enters a label for a document, this method automatically returns
    the next recommended document. Also loads or train a new SLDA model
    '''
    def round_trip1(self, label, doc_id, response_time):
        # logging.info('calling round trip')
        logging.info('alto num docs labeld are', self.alto.num_docs_labeled)
        if self.model_type == 'SLDA':
            logging.info('SLDA mode')
            '''
            Start updateing sLDA model as soon as the user labels 4 documents
            '''
            if self.alto.num_docs_labeled >= 4:
                if self.update_process is None:
                    self.slda_update_freq += 1
                    with Manager() as manager:
                        self.update_process = Process(target=self.update_slda)
                        self.update_process.start()
                elif not self.update_process.is_alive():
                    '''
                    After SLDA model finishes updating in the backend, load it from the
                    saved directory. Then updates the sLDA again
                    '''
                    self.load_updated_model()
                    self.slda_update_freq += 1
                    with Manager() as manager:
                        self.update_process = Process(target=self.update_slda)
                        self.update_process.start()
            
            result = self.sub_roundtrip(label, doc_id, response_time)
            return result
        else:
            return self.sub_roundtrip(label, doc_id, response_time)


    '''
    Return a dictionary, where the keys represent the topics from the topic
    model. and the values are the documents associated with the topic number
    '''
    def get_document_topic_list(self, recommend_action):
        logging.info('calling get document topic list')

        if self.model_type == 'LDA' or self.model_type == 'SLDA' or self.model_type == 'CTM':
            document_probas = self.document_probas

            result = {}
            cluster = {}
            for k, v in document_probas.items():
                cluster[str(k)] = [ele[0] for ele in v if not self.alto.is_labeled(int(ele[0]))]

            result['cluster'] = cluster
            
            # logging.info(recommend_result)
            if recommend_action:
                random_document, _ = self.alto.recommend_document(False)
            else:
                random_document = -1

            result['document_id'] = random_document
            result['keywords'] = self.string_topics
            
        else:
            result = {}
            cluster = {}
            cluster["1"] = [i for i in range(len(self.raw_texts))]
            # logging.info(cluster)
            result['cluster'] = cluster
            if recommend_action:
                random_document, _ = self.alto.recommend_document(False)
            else:
                random_document = -1
            
            result['document_id'] = random_document
            result['keywords'] = {}
           

        
        return result
    

    '''
    check whether the mode is just active learning or with topic model
    '''
    def check_active_list(self):
        logging.info('calling check active list')
        # print('self.model is', self.model_type)
        if self.model_type == 'LDA' or self.model_type == 'SLDA' or self.model_type == 'CTM':
            document_probas = self.document_probas
            result = {}
            cluster = {}
            for k, v in document_probas.items():
                cluster[str(k)] = [ele[0] for ele in v]

            result['cluster'] = cluster
            result['keywords'] = self.string_topics
            
        else:
            result = {}
            cluster = {}
            cluster["1"] = list(range(len(self.raw_texts)))
            # logging.info(cluster)
            result['cluster'] = cluster
     
            result['keywords'] = {}
            

        return result


    '''
    Calculate the metrics and return them. Accuracy, purity, rand index, NMI
    '''
    def get_metrics_to_save(self):
        try:
            user_purity, user_RI, user_NMI = self.alto.eval_classifier(self.labels)
            self.purity = user_purity
            self.RI = user_RI
            self.NMI = user_NMI
            return user_purity, user_RI, user_NMI
        except:
            return -1, -1, -1