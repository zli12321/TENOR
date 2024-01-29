import numpy as np
from sklearn import metrics
from scipy.special import comb


'''
Returns
doc_prob_topic: D X T matrix, where D is is the number of documents
T is the number of topics from the topic model. For each document, it
contains a list of topic probabilities.

topics_probs: A dictionary, for each topic key, contains a list of tuples
[(dic_id, probability)...]. Each tuple has a document id, representing 
the row id of the document, and probability the document belong to this topic.
For each topic, it only contains a list of documents that are the most likely 
associated with that topic.
'''
def group_docs_to_topics(model_inferred):
    doc_prob_topic = []
    doc_to_topics, topics_probs = {}, {}

    for doc_id, inferred in enumerate(model_inferred):
        doc_topics = list(enumerate(inferred))
        doc_prob_topic.append(inferred)

        doc_topics.sort(key = lambda a: a[1], reverse= True)

        doc_to_topics[doc_id] = doc_topics
        
        if doc_topics[0][0] in topics_probs:
            topics_probs[doc_topics[0][0]].append((doc_id, doc_topics[0][1]))
        else:
            topics_probs[doc_topics[0][0]] = [(doc_id, doc_topics[0][1])]

    for k, v in topics_probs.items():
        topics_probs[k].sort(key = lambda a: a[1], reverse= True)

    print(topics_probs.keys())
    
    return topics_probs, doc_prob_topic


''' Calculates purity between two sets of labels'''
def purity_score(y_true, y_pred):
    # compute contingency matrix (also called confusion matrix)
    contingency_matrix = metrics.cluster.contingency_matrix(y_true, y_pred)
    print(contingency_matrix)
    # return purity
    return np.sum(np.amax(contingency_matrix, axis=0)) / np.sum(contingency_matrix)

'''Each topic has a list of assigned documents, pick the topic that has the maximum median
   preference function scores- mainly the topic the classifier is the most confused about '''
def pick_topic(topic_U):
    '''
    topic_U: A dictionary that contains the following information:
    {
    topic 1: [preference function scores for documents assigned to topic 1],
    topic 2: [preference function scores for documents assigned to topic 2]
    ...
    }
    '''

    max_medium_topic = float('-Inf')
    max_medium_topic_probability = float('-Inf')
    for k, v in topic_U.items():
        curr_median = np.median(v)
        # print('topic {} median {}'.format(k, curr_median))
        if curr_median >= max_medium_topic_probability:
            max_medium_topic = k
            max_medium_topic_probability = curr_median

    
    return max_medium_topic


'''
Find the document that satisfies the preference function for active learning with tpic modeing
'''
def active_selection(document_probas, entropy):
    '''
    document_probas: a two dimensional array that contains the following information
    {
    topic 1: a list of tuples of documents assigned to topic 1, sorted in descending order by probability,
    each tuple is (document_id: the index of the document in the list, probability: the probability of the document
    assigned to topic 1)
    ...
    }

    entropy: the entropy of the classifier for the list of documents, in a list format
    [entropy for doc 1, entropy for doc 2...]
    '''

    doc_info_with_id = {}
    doc_info_no_id = {}
    for k, v in document_probas.items():
        lst = [(doc_id, prob*entropy[doc_id]) for doc_id, prob in v]
        lst1 = [prob for doc_id, prob in lst] 
        doc_info_with_id[k] = lst
        doc_info_no_id[k] = lst1

    '''Find the topic with maximum median preference function score'''
    max_medium_topic = pick_topic(doc_info_no_id)

    '''Find the most confusing document within that topic- the maximum cpreference function score'''
    max_idx = np.argmax(doc_info_no_id[max_medium_topic])
    chosen_doc_id = doc_info_with_id[max_medium_topic][max_idx][0]

    return chosen_doc_id, max_medium_topic, max_idx


'''
Remove a value from the dictionary 
'''
def remove_value_from_dict_values(dictionary, value_to_remove):
    for key, value_list in dictionary.items():
        dictionary[key] = [(idx, val) for idx, val in value_list if idx != value_to_remove]


'''Calculates the rand index score between two sets of labels'''
def rand_index(actual, pred):

    tp_plus_fp = comb(np.bincount(actual), 2).sum()
    tp_plus_fn = comb(np.bincount(pred), 2).sum()
    A = np.c_[(actual, pred)]
    tp = sum(comb(np.bincount(A[A[:, 0] == i, 1]), 2).sum()
             for i in set(actual))
    fp = tp_plus_fp - tp
    fn = tp_plus_fn - tp
    tn = comb(len(A), 2) - tp - fp - fn
    return (tp + tn) / (tp + fp + fn + tn)