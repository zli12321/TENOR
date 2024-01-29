from sklearn.linear_model import SGDClassifier
from utils.tools import purity_score
from utils.tools import active_selection
from utils.tools import remove_value_from_dict_values
from sklearn.metrics.cluster import adjusted_mutual_info_score
from sklearn.metrics.cluster import adjusted_rand_score
from scipy.sparse import vstack
import numpy as np
import random
from scipy.sparse import csr_matrix, hstack
import copy
from utils.tools import group_docs_to_topics
import logging
import os, sys
from contextlib import contextmanager


@contextmanager
def suppress_stdout():
    with open(os.devnull, 'w') as devnull:
        old_stdout = sys.stdout
        sys.stdout = devnull
        try:  
            yield
        finally:
            sys.stdout = old_stdout


'''
We use logistic regression as the classifier with chosen hyperparameters. You could also change the
of hyperparameters
'''
class Active_Learning():
    def __init__(self, doc_prob, text_vectorizer, doc_topic_prob=None):
        """
        doc_prob: a dictionary contains all the topics. Each topic 
        contains a list of documents along with their probabilities 
        belong to a specific topic
        {topic 1: [(document a, prob 1), (document b, prob 2)...]
        ...}

        doc_topic_prob: a list of lists, where each list is the topic probability
        for a specific document

        text_vectorizer: embeddings of text documents to feed into the classifier

        doc_topic_prob: the document topic probabilities processed when training the model. 
        If this is not provided, our method will process it for you but takes linger time to initialize
        """
        self.num_docs_labeled = 0
        self.last_recommended_topic = None
        self.last_recommended_doc_id = None
        self.recommended_doc_ids = set()

        if doc_topic_prob is None:
            topics_probs, doc_topic_prob= group_docs_to_topics(doc_prob)

        self.num_docs = len(doc_topic_prob)

        '''
        Concatenate the text vectorizer with the topic probability embeddings
        '''
        
        self.text_vectorizer = hstack([text_vectorizer, csr_matrix(copy.deepcopy(doc_topic_prob)).astype(np.float64)], format='csr')

        self.id_vectorizer_map = {}
        '''
        stores the scores of the documents after the user updates the classifier
        '''
        self.scores = []


        '''
        user_labels: labels the user creates for documents the user views
        curr_label_num: topic numbers computed by topic models
        '''
        self.user_labels = dict()

        '''
        Parameters or regressor can be changed later
        '''
        self.classifier = self.initialize_classifier()


        '''Stores and track labeled documents and labels'''
        self.documents_track = None
        self.labels_track = []


        self.classes = []


        self.doc_topic_prob = np.array(doc_topic_prob)
        self.doc_probs = doc_prob
    
    def update_doc_probs(self, doc_prob, doc_topic_prob):            
        self.doc_topic_prob = np.array(doc_topic_prob)
        self.doc_probs = doc_prob


    def initialize_classifier(self):
        return SGDClassifier(loss="log_loss", penalty='l2', tol=1e-3, random_state=42, learning_rate="optimal", eta0=0.1, validation_fraction=0.2, alpha = 0.000005)

    '''
    After selecting the document within a topic, drops it from the list
    '''
    def update_median_prob(self, topic_num, idx_in_topic):
        try:
            self.doc_probs[topic_num].pop(idx_in_topic)
        except:
            self.doc_probs.pop(topic_num)
        

    '''
    Preference function can be changed or chosen for ActiveLearning
    Return the recommended document ID from the list index and the 
    preference function score for the document. The score is -1 if
    the classifier is not intialized yet
    '''
    def preference(self, update=True):
        '''
        If the user only clicks the document, set update to be False
        '''
        if not update and self.last_recommended_doc_id is not None:
            # logging.info('return last recommended id')
            if self.last_recommended_doc_id in self.scores:
                return self.last_recommended_doc_id, self.scores[self.last_recommended_doc_id]
            return self.last_recommended_doc_id, -1
        

        '''
        If the classifier is not initialized yet, randomly pick a document from the corpus.
        Else, use active learing to pick a document
        '''
        if len(self.classes) < 2:
            chosen_idx = random.randint(0, self.num_docs)

            while chosen_idx in self.recommended_doc_ids:
                try:
                    chosen_idx = random.randint(0, self.num_docs)
                except Exception as e: 
                    logging.info("An exception occurred at picking a document:", e)


            self.recommended_doc_ids.add(chosen_idx)
            self.last_recommended_doc_id = chosen_idx

            return chosen_idx, -1
        else:
            try:
                for ele in self.recommended_doc_ids:
                    self.scores[ele] = float('-Inf')

                chosen_idx, chosen_topic, chosen_idx_in_topic = active_selection(self.doc_probs, self.scores)
                self.update_median_prob(chosen_topic, chosen_idx_in_topic)
                    
                while chosen_idx in self.recommended_doc_ids:
                    # logging.info('Selected Documents still exists')
                    chosen_idx, chosen_topic, chosen_idx_in_topic = active_selection(self.doc_probs, self.scores)
                    self.update_median_prob(chosen_topic, chosen_idx_in_topic)

                # logging.info('max median topic is ', chosen_topic)

                self.last_recommended_topic = chosen_topic
                self.recommended_doc_ids.add(chosen_idx)
                self.last_recommended_doc_id = chosen_idx
                    

                return chosen_idx, self.scores[chosen_idx]
            except Exception as e:
                logging.info("An exception occurred at picking a document:", e)
                return None, -1
       

    '''
    Select a document from the list by a preference function
    '''
    def recommend_document(self, update):
        document_id, score = self.preference(update)
        # logging.info(self.classes)
        return document_id, score

    '''
    Train the classifier with existing labeled documents
    '''
    def fit_classifier(self, initialized= False):
        if initialized:
            # for i in range(len(self.labels_track)):
                # self.classifier.partial_fit(self.documents_track, self.labels_track, self.classes)
            
            self.classifier.fit(self.documents_track, self.labels_track)
        else:
            # for i in range(len(self.labels_track)//10):
            # if self.num_docs_labeled % 10 == 0:
            # self.classifier.partial_fit(self.documents_track, self.labels_track, self.classes)
            self.classifier = self.initialize_classifier()
            self.classifier.fit(self.documents_track, self.labels_track)

        self.update_classifier()

    def is_labeled(self, doc_id):
        return doc_id in self.user_labels

    '''
    calculate the entropy for each document in the document list
    '''
    def update_classifier(self):
        guess_label_probas = self.classifier.predict_proba(self.text_vectorizer[0:self.num_docs])
        guess_label_logprobas = self.classifier.predict_log_proba(self.text_vectorizer[0:self.num_docs])
        scores = -np.sum(guess_label_probas*guess_label_logprobas, axis = 1)
        self.scores = scores
    

    '''
    To add a label to a document, given the document id, which is the index of the document in the list, 
    and the label of the document
    '''
    def label(self, doc_id, user_label):
        if int(doc_id) != self.last_recommended_doc_id:
            self.recommended_doc_ids.add(int(doc_id))
            remove_value_from_dict_values(self.doc_probs, int(doc_id))
            
            
        if self.is_labeled(doc_id):
            # if user_label in self.user_label_number_map:
            if user_label in self.classes:
                # label_num = self.user_label_number_map[user_label]
                self.user_labels[doc_id] = user_label
                self.labels_track[self.id_vectorizer_map[doc_id]] = user_label
                if len(self.classes) >= 2:
                    self.fit_classifier()              
            else:
                self.user_labels[doc_id] = user_label
                self.classes.append(user_label)
                self.labels_track[self.id_vectorizer_map[doc_id]] = user_label

                '''
                Initilize a classifier once at least two classes exists
                '''
                if len(self.classes) >= 2:
                    self.classifier = self.initialize_classifier()

                    self.fit_classifier(initialized=True)
        elif user_label in self.classes:  
            self.user_labels[doc_id] = user_label
            self.id_vectorizer_map[doc_id] = self.num_docs_labeled
            '''
            Adding documents and labels and track them
            '''
            self.labels_track.append(user_label)
            
            '''
            Add training data into to train the classifier
            '''
            if self.documents_track is None:
                self.documents_track = self.text_vectorizer[doc_id]
            else:
                self.documents_track = vstack((self.documents_track, self.text_vectorizer[doc_id]))
                
            if len(self.classes) >=  2:
                self.fit_classifier()
                        

            self.num_docs_labeled += 1

            # logging.info('\033[1mnum docs labeled {}\033[0m'.format(self.num_docs_labeled))
        else:
            self.classes.append(user_label)
            self.id_vectorizer_map[doc_id] = self.num_docs_labeled
                
            self.user_labels[doc_id] = user_label

            self.labels_track.append(user_label)
            if self.documents_track is None:
                self.documents_track = self.text_vectorizer[doc_id]
            else:
                self.documents_track = vstack((self.documents_track, self.text_vectorizer[doc_id]))

            if len(self.classes) >= 2:
                self.classifier = self.initialize_classifier()
                self.fit_classifier(initialized=True)
                    
    
            self.num_docs_labeled += 1
        
    '''
    given a document id, predict its associated label.
    This function is for frontend only. The results are top 3 predictions of the classifier given a document ID, 
    and a list that sorts the prediction outputs so users can quickly use it
    '''
    def predict_label(self, doc_id):       
        # logging.info('labels track {}'.format(self.labels_track))
        doc_id = int(doc_id)
        # logging.info('user_label_number_map is {}'.format(self.user_label_number_map))
        if len(self.classes) >= 2:
            classes = self.classifier.classes_
            probabilities = self.classifier.predict_proba(self.text_vectorizer[doc_id])[0]
            sorted_indices = probabilities.argsort()[::-1]
            top_three_indices = sorted_indices[:3]
            

            
            result = []
            for ele in top_three_indices:
                # result += classes[ele] + '    Confidence: ' + str(round(probabilities[ele], 2)) + '\n'
                result.append(classes[ele])

            # logging.info('id_vectorizer_map is {}'.format(self.id_vectorizer_map))
            # logging.info('prediction result is {}'.format(result))

            classes = np.array(classes)
            dropdown_indices = classes[sorted_indices]
            
            return result, dropdown_indices
        else:
            return ["Model suggestion starts after two distinct labels are created two labels to start active learning"], []
    

    '''
    Evaluate the cluster metrics given ground truth labels
    '''
    def eval_classifier(self, reference_labels):
        local_training_preds = self.classifier.predict(self.text_vectorizer[0:self.num_docs])
        with suppress_stdout():
            classifier_purity = purity_score(reference_labels[0:self.num_docs], local_training_preds[0:self.num_docs])
            classifier_RI = adjusted_rand_score(reference_labels[0:self.num_docs], local_training_preds[0:self.num_docs])
            classifier_NMI = adjusted_mutual_info_score(reference_labels[0:self.num_docs], local_training_preds[0:self.num_docs])

         
        logging.info('purity {}; RI {}; NMI {}'.format(classifier_purity, classifier_RI, classifier_NMI))
        return classifier_purity, classifier_RI, classifier_NMI
    
    '''
    If we have new features want to append to the text embeddings, for example, we update topic models,
    then update the text embedding and update the classifier
    '''
    def update_text_vectorizer(self, new_text_vectorizer):
        self.text_vectorizer = new_text_vectorizer
        labeld_doc_indices = list(self.user_labels.keys())

        self.documents_track = None

        for doc_id in labeld_doc_indices:
            if self.documents_track is None:
                self.documents_track = self.text_vectorizer[doc_id]
            else:
                self.documents_track = vstack((self.documents_track, self.text_vectorizer[doc_id]))

        self.classifier = self.initialize_classifier()

        self.fit_classifier(initialized=True)
