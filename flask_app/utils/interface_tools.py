import re, numpy as np, pandas as pd
from xml.dom import minidom
import os
import numpy as np
from sklearn import metrics
import subprocess


def read_data(path):
    return pd.read_json(path)


def filter_data(json_data, probability):
    filtered_topics = {}
    for a in json_data['topics']:
        results = json_data['topics'][a]
        each_file = pd.DataFrame(results)
        results = each_file[each_file['score']>=probability]
        filtered_topics[a]= {
            "spans": results['spans'].to_list(),
            "score": results['score'].to_list()
            }
    return filtered_topics


def get_words(dat, raw_string):
    words = {}
    for a in dat.keys():
        semi_words = []
        for b in dat[a]['spans']:
            try:
                semi_words.append(raw_string[b[0]:b[1]])
            except:
                continue
        words[a] = set(semi_words)
    return words


def highlight_words(text, words):
    for word in words:
        text = text.replace(word, f"<span style='background-color:yellow'>{word}</span>")
    return text


def save_response(name, label, response_time, document_id, user_id):
    root = minidom.Document()
    xml = root.createElement('root')
    root.appendChild(xml)

    user_name = root.createElement('name')
    user_name.setAttribute("name", name)
    xml.appendChild(user_name)

    response_times = root.createElement('response_time')
    response_times.setAttribute("response_time", str(response_time))
    xml.appendChild(response_times)

    document_ids = root.createElement('document_id')
    document_ids.setAttribute("document_id", str(document_id))
    xml.appendChild(document_ids)

    labels = root.createElement('label')
    labels.setAttribute("label", label)
    xml.appendChild(labels)

    user_ids = root.createElement('user_id')
    user_ids.setAttribute("user_id", str(user_id))
    xml.appendChild(user_ids)

    xml_str = root.toprettyxml(indent ="\t")

    directory = "./flask_app/static/responses/"+name

    save_path_file = directory + "/"+ str(document_id) +".xml"
    try:
        os.makedirs(directory)
    except:
        print("all_good")
    with open(save_path_file, "w") as f:
        f.write(xml_str)
    return xml_str



def get_texts (topic_list, all_texts, docs):
    results = {}
    for a in topic_list["cluster"].keys():
        sub_results = {}
        for b in topic_list["cluster"][a]:
            if str(b) in docs:
                continue
            sub_results[str(b)] = all_texts["text"][str(b)]
        results[a]= sub_results
    return results



def get_sliced_texts(topic_list, all_texts, docs):
    results = {}
    for a in topic_list["cluster"].keys():
        sub_results = {}
        counter = 0
        for b in topic_list["cluster"][a]:
            if str(b) in docs:
                continue
            if counter < 6:
                sub_results[str(b)] = all_texts["text"][str(b)]
            counter+=1
        results[a]= sub_results
    return results 


def get_single_document(top, all_texts, docs):
    results = {}

    for a in top:
        if str(a) not in docs:
                # continue
            results[str(a)] = all_texts["text"][str(a)]
    return results 


def save_labels(session):
    import json
    with open('./flask_app/static/users/users.json') as user_file:
        name_string = user_file.read()
        names = json.loads(name_string)

    with open('./flask_app/static/users/users.json', mode='w', encoding='utf-8') as name_json:
        names[session["name"]]["labels"] = session["labels"]
        names[session["name"]]["labelled_document"] = session["labelled_document"]
        json.dump(names, name_json, indent=4)


def labelled_docs(labe, all_texts):
    results = {}
    labelled = [x for x in labe.strip(",").split(",")][: : -1]
    if len(labelled) == 1 and '' in labelled: return results
    # try:
    for a in labelled:
        results[a] = all_texts["text"][a]
    # except:
    #     pass

    
    return results


def extract_label (name, number):
    responses_path =("./flask_app/static/responses/" + name + "/" + number +".xml" )
    doc = minidom.parse(responses_path)
    root = doc.getElementsByTagName("label")
    label = None
    for a in root:
        label = a.getAttribute("label")
    return label

def completed_json_ (name):
    import pandas as pd
    import glob
    path = "./flask_app/static/responses/" + name+"/*"
    doc_id = []
    doc_label = []
    res = []
    for a in glob.glob(path):
        doc = minidom.parse(a)
        user_label = doc.getElementsByTagName("label")
        document_id = doc.getElementsByTagName("document_id")
        for a in document_id:
            doc = a.getAttribute("document_id")
            doc_id.append(doc)
        for b in user_label:
            label = b.getAttribute("label")
            doc_label.append(label)
    for c in zip(doc_id, doc_label):
        res.append(c)
    df = pd.DataFrame(res, columns=["document_id", "label"])
    completed_json = {}
    for a in set(df["label"]):
        completed_json[a]=list(df[df["label"]==a]["document_id"])
    return completed_json


def get_completed(completed_json, all_texts):
    results = {}
    for a in completed_json.keys():
        sub_results = {}
        for b in completed_json[a]:
            sub_results[str(b)] = all_texts["text"][str(b)]
            results[a]= sub_results
    return results

def get_recommended_topic(recommended, topics, all_texts):
    results = {}
   
    for a in topics["cluster"].keys():
        sub_results = {}
        for b in topics["cluster"][a]:
            if b == recommended:
                for c in topics["cluster"][a]:
                    sub_results[str(c)] = all_texts["text"][str(c)]
                results[a] = sub_results
                recommended_topic = a
    return recommended_topic,  results

def save_time(name):
    from csv import writer
    import datetime
    if not os.path.exists("./flask_app/static/responses/"+name):
        subprocess.call(["mkdir", "./flask_app/static/responses/"+name])

    with open ("./flask_app/static/responses/"+name+"/time.csv", 'a', newline='') as f_object:
        writer_object = writer(f_object)
        writer_object.writerow([datetime.datetime.now()])
        f_object.close()


