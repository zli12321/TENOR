from flask import Flask, request, render_template, url_for, redirect, flash, session, jsonify
from backend_server import User
# import random
import sqlite3
from utils.interface_tools import *
import json
from flask_session import Session
# import requests
from datetime import datetime
import os
import threading
import pickle
import time
import csv

Enable_security = False
user_names = []
blocked_users = set()


app = Flask(__name__)


time_folder = './flask_app/01-user_data/user_time_data/'
page_folder = './flask_app/01-user_data/user_page_tracker/'
instance_folder = './flask_app/01-user_data/user_instances/'
clicks_folder = './flask_app/01-user_data/user_clicks/'
per_doc_folder = './flask_app/01-user_data/user_data_per_doc/'

all_texts = json.load(open('./flask_app/Data/bills/congressional_bill_train.json'))

try:
    true_labels = list(all_texts['label'].values())
except:
    true_labels = ['null' for i in range(len(all_texts['text']))]

session_stop_events = {}


DATABASE = './flask_app/database/demo.db'
user_instances = {}


def create_connection():
    conn = sqlite3.connect(DATABASE)
    return conn

def init_db():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        # Create the 'users' table if it doesn't exist
        cursor.execute('''CREATE TABLE IF NOT EXISTS users
                         (id INTEGER PRIMARY KEY AUTOINCREMENT,
                         user_id INTEGER,
                         mode INTEGER NOT NULL)''')
        conn.commit()
        # Check if the 'user_id' and 'mode' columns exist in the 'users' table
        cursor.execute("PRAGMA table_info(users)")
        table_info = cursor.fetchall()
        columns = [info[1] for info in table_info]
        
        if 'user_id' not in columns:
            cursor.execute('ALTER TABLE users ADD COLUMN user_id INTEGER')
            conn.commit()
        
        if 'mode' not in columns:
            cursor.execute('ALTER TABLE users ADD COLUMN mode INTEGER NOT NULL')
            conn.commit()

        cursor.execute('''CREATE TABLE IF NOT EXISTS recommendations
                         (id INTEGER PRIMARY KEY AUTOINCREMENT,
                         user_id INTEGER,
                         label TEXT,
                         doc_id INTEGER,
                         response_time REAL,
                         actual_label TEXT,
                         purity REAL,
                         RI REAL,
                         NMI REAL,
                         topic_information TEXT,
                         FOREIGN KEY (user_id) REFERENCES users (id))''')
        
        conn.commit()

        cursor.execute('''CREATE TABLE IF NOT EXISTS user_label_track
                         (id INTEGER PRIMARY KEY AUTOINCREMENT,
                         user_id INTEGER,
                         time TEXT,
                         user_labels TEXT,
                         purity REAL,
                         RI REAL,
                         NMI REAL,
                         click_track TEXT,
                         FOREIGN KEY (user_id) REFERENCES users (id))''')
        
        conn.commit()

        



init_db()

def create_file(filename, columns):
    with open(filename, 'a') as f:
        columns += '\n'
        f.write(columns)

def create_user():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT MAX(user_id) FROM users')
        result = cursor.fetchone()

        if result[0] is not None:
            user_id = result[0] + 1
        else:
            user_id = 1

        mode = user_id % 3

        # print('user id is {}, mode is {}'.format(user_id, mode))
        cursor.execute('INSERT INTO users (user_id, mode) VALUES (?, ?)', (user_id, mode))
        conn.commit()

        model_map = {0: 'LDA', 1: 'SLDA', 2: "CTM"}

        user_instances[user_id] = User(user_id, all_texts['text'], model_type=model_map[mode], labels=true_labels)  # Create the User() object and store it in the user_instances dictionary


    filename = per_doc_folder + '{}.csv'.format(user_id)
    columns = ['user_id', 'doc_id', 'label', 'purity', 'randIndex', 'NMI', 'responseTime', 'sLDAUpFreq' ,'topKeywords', 'recommendID', 'actualLabel']
    create_file(filename, ','.join(columns))

    time_filename = time_folder + '{}.csv'.format(user_id)
    time_columns = ['user_id', 'minutesPassed', 'Purity', 'randIndex', 'NMI', 'numDocsLabeled', 'sLDAUpFreq']
    create_file(time_filename, ','.join(time_columns))
    
    click_filename = clicks_folder + '{}.csv'.format(user_id)
    click_columns = ['user_id', 'recommendID', 'viewID', 'action']
    create_file(click_filename, ','.join(click_columns))

    page_track_file_name = page_folder + '{}.csv'.format(user_id)
    page_columns = ['user_id', 'page', 'stat_time']
    create_file(page_track_file_name, ','.join(page_columns))

    print('Creating user', user_id)
    print('model is ',model_map[mode])

    
    return {'user_id': user_id, 'code': 200, 'msg': 'User created'}


def backend_save_user_labels(user_id, time_interval):
    user =  user_instances[user_id]

    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        
        cursor.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()

        if row is not None:
            user_labels = user.alto.user_labels
            dict_as_string = json.dumps(user_labels)
            clicks = json.dumps(user.click_tracks)
            user_purity, user_RI, user_NMI = user.get_metrics_to_save()
            cursor.execute('''INSERT INTO user_label_track
                            (user_id, time, user_labels, purity, RI, NMI, click_track)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                        (user_id, time_interval, dict_as_string, user_purity, user_RI, user_NMI, clicks))
            conn.commit()

            result = {}
            result['code'] = 200
            result['msg'] = 'SUCCESS'
            # conn.close()
            print('inserted')
            return result
        else:
            return {"code": 404, "msg": "User not found"}


def nist_recommend(user_id, label, doc_id, response_time):
    user =  user_instances[user_id]
    purity, RI, NMI, result = user.round_trip1(label, doc_id, response_time)
    document_topics = user.get_doc_information_to_save(doc_id)
    

    actual_label = true_labels[int(doc_id)]

    with open(per_doc_folder + '{}.csv'.format(user_id), 'a') as f:
        try:
            data_string = ','.join([
                    str(user_id),
                    str(doc_id),
                    str(label),
                    str(purity),
                    str(RI),
                    str(NMI),
                    str(response_time),
                    str(user.slda_update_freq),
                    str(document_topics['topics'][0][0]),
                    str(user.alto.last_recommended_doc_id),
                    actual_label]) + '\n'
            f.write(data_string)
        except:
            data_string = ','.join([
                    str(user_id),
                    str(doc_id),
                    str(label),
                    str(purity),
                    str(RI),
                    str(NMI),
                    str(response_time),
                    str(user.slda_update_freq),
                    'None',
                    str(user.alto.last_recommended_doc_id),
                    actual_label]) + '\n'
            f.write(data_string)
            print('failed to save')
        
        with open(clicks_folder + '{}.csv'.format(user_id), 'a') as f:
            data_string = ','.join([
                    str(user_id),
                    str(user.alto.last_recommended_doc_id),
                    str(doc_id),
                    'label']) + '\n'
                
            # print('data string is ', data_string)
            f.write(data_string)

    document_topics = json.dumps(document_topics)

    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        
        cursor.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()

        if row is not None:
            cursor.execute('''INSERT INTO recommendations
                            (user_id, label, doc_id, response_time, actual_label, purity, RI, NMI, topic_information)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                        (user_id, label, doc_id, response_time, actual_label,purity, RI, NMI, document_topics))
            conn.commit()

            result['code'] = 200
            result['msg'] = 'SUCCESS'
            # conn.close()
            return result
        else:
            return {"code": 404, "msg": "User not found"}


def skip_document(user_id):
    user =  user_instances[user_id]
    next_doc_id = user.skip_doc()
            # conn.close()
    return next_doc_id
        
 
def get_list(user_id, recommend_action):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        
        cursor.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()

        if row is not None:
            user =  user_instances[user_id]
            result = user.get_document_topic_list(recommend_action)
            result['code'] = 200
            result['msg'] = 'SUCCESS'
            return result
        else:
            return {"code": 404, "msg": "User not found"}


def check_active_list(user_id):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        
        cursor.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()

        if row is not None:
            user =  user_instances[user_id]
            result = user.check_active_list()
            result['code'] = 200
            result['msg'] = 'SUCCESS'
            return result
        else:
            return {"code": 404, "msg": "User not found"}


def get_doc_info(doc_id, user_id):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        
        cursor.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()

        if row is not None:
            user =  user_instances[user_id]
            result = user.get_doc_information(doc_id)
            result['code'] = 200
            result['msg'] = 'SUCCESS'
            # conn.close()
            with open(clicks_folder + '{}.csv'.format(user_id), 'a') as f:
                data_string = ','.join([
                        str(user_id),
                        str(user.alto.last_recommended_doc_id),
                        str(doc_id),
                        'click']) + '\n'
                
                # print('data string is ', data_string)
                f.write(data_string)
            return result
        else:
            return {"code": 404, "msg": "User not found"}


def record_data_for_session(session_id, stop_event):
    counter = 1
    while not stop_event.is_set():
        time.sleep(60)  # Wait for 60 seconds
        # Your logic to record data for the session
        user =  user_instances[session_id]
        with open(time_folder + '{}.csv'.format(session_id), 'a') as f:
            data_string = ','.join([
                    str(session_id),
                    str(counter),
                    str(user.purity), 
                    str(user.RI), 
                    str(user.NMI), 
                    str(user.alto.num_docs_labeled),
                    str(user.slda_update_freq)]) + '\n'
            
            # print('data string is ', data_string)
            f.write(data_string)
        
        with open(clicks_folder + '{}.csv'.format(session_id), 'a') as f:
            data_string = ','.join([
                str(session_id),
                str(user.alto.last_recommended_doc_id),
                'None',
                'None']) + '\n'
                
            # print('data string is ', data_string)
            f.write(data_string)
        print(f"Recording data for session: {session_id}")
        counter += 1


def save_page_time(user_id, page_name, stay_time):
    with open(page_folder + '{}.csv'.format(user_id), 'a') as f:
        data_string = ','.join([
                    str(user_id),
                    str(page_name),
                    str(stay_time)]) + '\n'
            
        # print('data string is ', data_string)
        f.write(data_string)

'''
This is frontend session
'''

predictions = []
os.urandom(24).hex()


app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24).hex()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

@app.route("/")
def home():
    return redirect(url_for("login"))


@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method =="POST":
        name = request.form["name"]

        if name in blocked_users:
            return redirect('https://i.gifer.com/8k9t.gif')

        if Enable_security == True and name not in user_names:
            return redirect('https://prolific.com/')

        with open('./flask_app/static/users/users.json') as user_file:
            name_string = user_file.read()
            names = json.loads(name_string)
        # name = request.form["name"]

        session["name"] = name
        session["begin"] = datetime.now()
        print(session["begin"])
        session["start_time"] = ""
        
        

        if name in list(names.keys()):
            session["name"] = names[name]['username']
            session["labels"] = names[name]["labels"]
            session["user_id"] = names[name]["id"]
            session["labelled_document"] = names[name]["labelled_document"]
            
            user_id = session["user_id"]
            print('user id is {}'.format(user_id))
            # return redirect(url_for("active_check", name=name))
            return redirect(url_for("home_page", name=name, user_id=user_id))
            
        else:
            
            user = create_user()
            user_id = user["user_id"] 
            session["user_id"] = user_id
            session["labels"] = ""
            session["labelled_document"] = ""
            data = {
                "username": name, 
                "id" : user_id,
                "labels" : session["labels"],
                "labelled_document" : session["labelled_document"]
            }

            session["user_id"] = user_id  
            names[name]=data
            
            with open('./flask_app/static/users/users.json', mode='w', encoding='utf-8') as name_json:
                # names = json.loads(name_string)
                names[name] = data
                json.dump(names, name_json, indent=4)


            return redirect(url_for("home_page", name=name, user_id=user_id))
    return render_template("login.html") 


# READING WHAT THE STUDY IS ABOUT
@app.route("//firstpage//<name>/", methods = ["POST", "GET"])
def home_page(name):
    if session.get("name") != name:
        # if not there in the session then redirect to the login page
        return redirect("/login")
    if request.method =="POST":
        cancel_param = request.form.get("cancel_param")
        if cancel_param and cancel_param == "cancel_value":  # Replace "cancel_value" with the specific value sent from the JavaScript
            # The "Cancel" button was clicked, so just render the "first.html" template again
            return render_template("first.html", name=name, time=session["begin"])

        
        save_page_time(session['user_id'], 'instruction', str(5))

        return redirect(url_for("active_check", name=name))
    return render_template("first.html", name=name, time=session["begin"])


@app.route("//checkactive//<name>//", methods=["POST", 'GET'])
def active_check(name):
    if session.get("name") != name:
        # if not there in the session then redirect to the login page
        return redirect("/login")


    # topics = get_list(session['user_id'], False)
    topics = check_active_list(session['user_id'])

    # print(topics)
    session_id = session["user_id"]
    session['id'] = session_id

    stop_event = threading.Event()
    session_stop_events[session_id] = stop_event
    # Start the dedicated thread for this session
    threading.Thread(target=record_data_for_session, args=(session_id, stop_event), daemon=True).start()

    if len(topics["cluster"].keys()) == 1:
        session["is_active"] = 1
        return redirect(url_for("active_list", name=name, time=session["begin"]))
    else:
        session["is_active"] = 0
        return redirect(url_for("non_active_list", name=name, time=session["begin"]))
    

@app.route("//active_list//<name>", methods=["POST", "GET"])
def active_list(name):
    if session.get("name") != name:
    # if not there in the session then redirect to the login page
        return redirect("/login")


    topics = get_list(session['user_id'], True)
    rec = str(topics["document_id"])
    docs = list(set(session["labelled_document"].strip(",").split(",")))
    # print(docs)
    if len(docs) == 1 and '' in docs: docs = []
    docs_len= len(docs)
    

    results = get_single_document(topics["cluster"]["1"], all_texts, docs)

    
    save_page_time(session['user_id'], 'document_list', str(5))
    if request.method =="POST":
        return redirect(url_for("finish"))
    return render_template("active_list.html", results=results, name=name, rec = rec, docs_len=docs_len)


@app.route("//non_active_list//<name>", methods=["POST", "GET"])
def non_active_list(name):
    if session.get("name") != name:
        # if not there in the session then redirect to the login page
        return redirect("/login")

    # get_topic_list = url + "//get_topic_list" 
    topics = get_list(session['user_id'], True)
        # print(session)

    recommended = int(topics["document_id"])

    docs = list(set(session["labelled_document"].strip(",").split(",")))
    if len(docs) == 1 and '' in docs: docs = []
    docs_len = len(docs)
    # print(recommended)

    recommended_topic, recommended_block = get_recommended_topic(recommended, topics, all_texts)
    # print(recommended_block)

    results = get_texts(topic_list=topics, all_texts=all_texts, docs=docs)

    sliced_results = get_sliced_texts(topic_list=topics, all_texts=all_texts, docs=docs)
    # print(sliced_results)
 
    keywords = topics["keywords"] 
    # print(keywords)
    
    save_page_time(session['user_id'], 'document_list', str(5))

    if request.method =="POST":
        return redirect(url_for("finish"))

    return render_template("nonactive.html", sliced_results=sliced_results, results=results, name=name, keywords=keywords, recommended=str(recommended), document_list = topics["cluster"], docs_len = docs_len, recommended_block=recommended_block, recommended_topic=recommended_topic, time=session["begin"])



@app.route("//active//<name>//<document_id>/", methods=["GET", "POST"])
def active(name, document_id):
    # topics = get_list(session['user_id'], True)

    text = all_texts["text"][str(document_id)]

    session["start_time"] = str(session["start_time"]) + "+" + str(datetime.now().strftime("%H:%M:%S"))

    # labels = list(set(session["labels"].strip(",").split(",")))
    docs = list(set(session["labelled_document"].strip(",").split(",")))
    print('doc are ', docs)

    if len(docs) == 1 and '' in docs: docs = []
    docs_len = len(docs)
    total = len(all_texts["text"])
    print('doc len is ', docs_len)

    if request.method =="POST":
        label = request.form.get("label").lower()
        drop = request.form.get("suggestion").lower()


        
        # This line has a big problem!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        label = str(drop) + str(label)
        label = label.strip()
        name=name
        document_id=document_id
        user_id = session["user_id"]
        
        print('label len is ', len(label))
        print('label is ', label)

        if len(label) == 0:
            document_id = skip_document(user_id)
            text = all_texts["text"][str(document_id)]
            
            response = get_doc_info(document_id, session["user_id"])  
            
            docs = list(set(session["labelled_document"].strip(",").split(",")))
            docs_len = len(docs)

            if len(response['dropdown']) > 0:
                labels = response['dropdown']
            # print('dropdown labels are', labels)
            else:
                labels = list(set(session["labels"].strip(",").split(",")))

            flash("You skipped the previous document")
            total = total = len(all_texts["text"].keys())

            return render_template("activelearning.html", text =text, predictions=labels, pred=response["prediction"], docs_len=docs_len, document_id=document_id, total=total , time=session["begin"]) 

        st = datetime.strptime(session["start_time"].strip("+").split("+")[-2], "%H:%M:%S")
        et = datetime.strptime(session["start_time"].strip("+").split("+")[-1], "%H:%M:%S")

        response_time = str(et-st)
        
        save_page_time(session['user_id'], 'labelling_page', str(et-st))

        save_response(name, label, response_time, document_id, user_id)
        

        posts = nist_recommend(int(user_id), label, document_id, response_time)

        next = posts["document_id"]
        # print(posts.keys())
        predictions.append(label.lower()) 
        
        
        session["labels"] = session["labels"] + "," + label
        # labels = list(set(session["labels"].strip(",").split(",")))
        # print(labels)
        session["labelled_document"] = session["labelled_document"]+","+str(document_id)
        
        save_labels(session)
        docs = list(set(session["labelled_document"].strip(",").split(",")))
        if len(docs) == 1 and '' in docs: docs = []
        # print('labelled docs are ', session['labelled_document'])
        # print('docs are', docs)
        docs_len = len(docs)

        # if len(response['dropdown']) > 0:
        #     labels = response['dropdown']
        #     # print('dropdown labels are', labels)
        # else:
        labels = list(set(session["labels"].strip(",").split(",")))
        # print('app labels are', labels)
        # print(label) 
        flash("You labeled \"{}\" for the previous document".format(label))
        # print('waiting to get to the next page')
        return redirect(url_for("active", name=name, document_id=next, time=session["begin"]))
        
    user_id = int(session['user_id'])
    response = get_doc_info(document_id, user_id)
    if len(response['dropdown']) > 0:
        labels = response['dropdown']
        # print('dropdown labels are', labels)
    else:
        labels = list(set(session["labels"].strip(",").split(",")))
        # print('app labels are', labels)

    return render_template("activelearning.html", text =text, predictions=labels, pred=response["prediction"], docs_len=docs_len, document_id=document_id, total=total , time=session["begin"]) 

    

### lABELLING THE TOPIC AND SAVING THE RESPONSE
@app.route("//get_label//<document_id>//", methods=["POST", 'GET'])
def get_label(document_id):
    document_id = document_id 
    user_id=session["user_id"] 
    # get_document_information = url + "//get_document_information"
    # data = requests.post(get_document_information, json={ "document_id": document_id,
    #                                                     "user_id":user_id
    #                                                      }).json()

    data = get_doc_info(document_id, user_id)
                                                         
    return redirect( url_for("label", response=data, name=session["name"], document_id=document_id))
    



@app.route("/logout", methods=["POST", "GET"])
def finish():
    name = session['name']
    user_id = session["user_id"]
    # session.pop(name, None)
    if name:
        blocked_users.add(name)
        user_instances[user_id].update_process = None

        with open(instance_folder + '{}_{}.pkl'.format(name, user_id), 'wb+') as outp:
            pickle.dump(user_instances[user_id], outp)
        user_instances[user_id] = None
        session_id = session.get('id')
        if session_id in session_stop_events:
            session_stop_events[session_id].set()  # Signal the thread to stop
            del session_stop_events[session_id]  # Remove the event


        session.clear()

    if user_id%4 == 0:
        return redirect('https://docs.google.com/forms/d/e/1FAIpQLScBHrNa2T20S6w_BBcVUWr9s5lHkWvjPHyJtrtpXnkqERXCdg/viewform?usp=sf_link')
    elif user_id%4 == 1:
        return redirect('https://docs.google.com/forms/d/e/1FAIpQLScjbDwIuGHR2uujRv5mrgsjANAnOywl-Jz383kAJKWWq5FMlw/viewform?usp=sf_link')
    elif user_id%4 == 2:
        return redirect('https://docs.google.com/forms/d/e/1FAIpQLSd3qoMsfVD1klrc6O-XmidQtqPkQ16Ld6fZA_HkQancwm7aBg/viewform?usp=sf_link')
    else:
        return redirect('https://docs.google.com/forms/d/e/1FAIpQLSd5Ki9poJdYGyM241exkSLrFSc7dBG0nDWYLyP9GzQuzD37TA/viewform?usp=sf_link')

    # return redirect("https://docs.google.com/forms/d/e/1FAIpQLSfEvyk1zQjI4FE0Gih0s4Q9xdm5J5lAWaF_aARtPRWhUwhI7Q/viewform?usp=sf_link")



@app.before_request
def require_login():
    allowed_route = ['login']
    if request.endpoint not in allowed_route and "name" not in session:
        return redirect('/login')



@app.route('//non_active_label//<name>//<document_id>/', methods=["POST", "GET"])
def non_active_label(name, document_id):
    # get_document_information = url + "//get_document_information"
    # response = requests.post(get_document_information, json={ "document_id": document_id,
    #                                                     "user_id":session["user_id"]
    #                                                      }).json()
    response = get_doc_info(document_id, session["user_id"])                                                    

    text = all_texts["text"][str(document_id)]
    # print('text', text)

    words = get_words(response["topic"],  text)
    # labels = list(set(session["labels"].strip(",").split(",")))
    # print("start time")
    session["start_time"] = str(session["start_time"]) + "+" + str(datetime.now().strftime("%H:%M:%S"))
    # print(session["start_time"])
    total = len(all_texts["text"].keys())
    docs = list(set(session["labelled_document"].strip(",").split(",")))
    if len(docs) == 1 and '' in docs: docs = []
    docs_len = len(docs)
    # print(docs_len)
    # print(response)
    # print('labelled docs are ', session['labelled_document'])
    # print('docs are', docs)


    if request.method =="POST":
        label = request.form.get("label").lower()
        drop = request.form.get("suggestion").lower()
        label = str(drop)+str(label)
        label = label.strip()

        name=name 
        document_id=str(document_id)
        user_id = session["user_id"]


        if len(label) == 0:
            document_id= skip_document(user_id)
            text = all_texts["text"][str(document_id)]
            
            # response = get_doc_info(document_id, session["user_id"])  
            words = get_words(response["topic"],  text)
            docs = list(set(session["labelled_document"].strip(",").split(",")))
            docs_len = len(docs)

            if len(response['dropdown']) > 0:
                labels = response['dropdown']
            # print('dropdown labels are', labels)
            else:
                labels = list(set(session["labels"].strip(",").split(",")))

            flash("You skipped the previous document")
            total = total = len(all_texts["text"].keys())
            return render_template("nonactivelabel.html", response=response, words=words, document_id=document_id, text=text, name=name, predictions=labels, pred=response["prediction"], total=total, docs_len=docs_len)


        st = datetime.strptime(session["start_time"].strip("+").split("+")[-2], "%H:%M:%S")
        et = datetime.strptime(session["start_time"].strip("+").split("+")[-1], "%H:%M:%S")

        
        response_time = str(et-st)
        
        save_page_time(session['user_id'], 'labelling_page', str(et-st))


        posts = nist_recommend(int(user_id), label, document_id, response_time)
        next = posts["document_id"]
        predictions.append(label.lower())
        
        
        session["labelled_document"] = session["labelled_document"]+","+str(document_id)
        docs = list(set(session["labelled_document"].strip(",").split(",")))
        if len(docs) == 1 and '' in docs: docs = []
        session["labels"] = session["labels"] + "," + label

        # labels = list(set(session["labels"].strip(",").split(",")))
        docs_len = len(docs)
        save_labels(session)

        save_response(name, label, response_time, document_id, user_id)
        

        response = get_doc_info(posts["document_id"], session["user_id"])  

        if len(response['dropdown']) > 0:
            labels = response['dropdown']
            # print('dropdown labels are', labels)
        else:
            labels = list(set(session["labels"].strip(",").split(",")))
            # print('app labels are', labels)


        # print(docs_len)
        flash("You labeled \"{}\" for the previous document".format(label))
        
        total = len(all_texts["text"].keys())
        done = len(docs)
        # print('trying to redirect to non active label again')
        return redirect(url_for("non_active_label", name=name, document_id=posts["document_id"]))
        # return redirect(url_for("non_active_label", response=response, words=words, document_id=posts["document_id"], name=name, predictions=labels, pred=response["prediction"], total=total, docs_len=docs_len))

    if len(response['dropdown']) > 0:
        labels = response['dropdown']
        # print('dropdown labels are', labels)
    else:
        labels = list(set(session["labels"].strip(",").split(",")))
        # print('app labels are', labels)
    return render_template("nonactivelabel.html", response=response, words=words, document_id=document_id, text=text, name=name, predictions=labels, pred=response["prediction"], total=total, docs_len=docs_len)
    # return render_template("nonactivelabel.html", response=response, words=words, document_id=document_id, text=text, name=name, predictions=labels, pred=[true_labels[int(document_id)]], total=total, docs_len=docs_len)


@app.route("/non_active/<name>/<topic_id>//<documents>//<keywords>")
def topic(name, topic_id, documents, keywords): 
    print(topic_id)
    # res = get_single_document(documents, all_texts)
    keywords = keywords.strip("'[]'").split("', '")
    docs = list(set(session["labelled_document"].strip(",").split(",")))
    if len(docs) == 1 and '' in docs: docs = []
    docs_len = len(docs)
    
    res = get_single_document(documents.strip("'[]'").split(", "), all_texts, docs=docs)

    return  render_template("topic.html", res = res, topic_id=topic_id, docs_len = docs_len, keywords=keywords) 
 

@app.route("/<name>/labeled/<document_id>")
def view_labeled(name,document_id):
    text = all_texts["text"][document_id]
    response = extract_label(name, document_id )
    
    save_page_time(session['user_id'], 'editting_label_page', str(5))
    return render_template("viewlabeled.html", text=text, response=response, document_id=document_id) 



@app.route("/<name>/labeled_list/")
def labeled_list(name):
    labe = session["labelled_document"]
    
    docss = labelled_docs(labe, all_texts)
    completed = completed_json_(name)
    completed_docs = get_completed(completed, all_texts)
    
    save_page_time(session['user_id'], 'completed_page', str(5))
    return render_template("completed.html", completed_docs=completed_docs, docss=docss)
 

@app.route("/<name>/edit_response/<document_id>")
def edit_labels(name, document_id):
    if session["is_active"] == True:
        return redirect(url_for("active", name=name, document_id=document_id))

    if session["is_active"] == False:
        return redirect(url_for("non_active_label", name=name, document_id=document_id))
    

@app.route("/save_user_label", methods=["POST"])
def save_user_labels():
    print('saving labels...')
    user_id = session.get("user_id")
    label_seconds = request.get_data(as_text=True)
    result = backend_save_user_labels(user_id, label_seconds)

    return jsonify(result)



if __name__ == "__main__":
    app.run(debug=True)
