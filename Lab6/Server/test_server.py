import json
import numpy as np
from flask import Flask, request, jsonify
import pymongo
from bson.objectid import ObjectId
from joblib import load
import requests

tweet_addr = 'https://api.thingspeak.com/apps/thingtweet/1/statuses/update'
tweet_key = 'LM0KABS7MZX6VZCR'
label_index = ['c', 'o', 'l', 'u', 'm', 'b', 'i', 'a']
#----------------------------------------------------
def get(post_id):
    document = collection.find_one({'_id': ObjectId(post_id)})
    return document
def clfpredict(data):
    datas = data['datas']
    data_array = np.array(datas).flatten().reshape((1, -1))
    X = scaler.transform(data_array)
    print(clf.predict_proba(X))
    return int(clf.predict(X))
def modulate(n):
    if n >= 24: n -= 24
    elif n < 0: n += 24
    return n
#--------------------------------------------------    
client = pymongo.MongoClient()
db = client.test_database
collection = db.collection # 
last_id = [0]
scaler, clf = load('model_11_11.joblib')

app = Flask(__name__)

@app.route('/predict')
def predict():
    # get data from MongoDB
    data = get(last_id[0])
    # prediction = model_predict(data)
    prediction = label_index[clfpredict(data)]
    prediction = jsonify({'prediction':str.upper(prediction)})
    return prediction

@app.route('/data', methods=['PUT'])
def upload_data():
    data = json.loads(request.data)
    print(data)
    # Put data into MongoDB using pymongo
    result = collection.insert_one(data).inserted_id
    last_id[0] = result
    return jsonify({'Numbers':collection.count_documents({})})

@app.route('/data', methods=['DELETE'])
def remove():
    collection.drop()
    return jsonify({'Return':'Sucess Remove DB'})

@app.route('/send', methods=['PUT'])
def send_twitter():
    data = json.loads(request.data)
    lat, lon, temperature, description = data['Package']
    tweet_post = {'api_key': tweet_key, 'status':'I am in %.2f Latitude, %.2f Longitude, and Temerature here is %.2f°C. Today is %s. Just Come to Catch Me!!!!!!!!!!!!!!'%(lat, lon, temperature, description)}
    requests.post(tweet_addr, tweet_post)
    print('sucessfully')
    return 'None'

@app.route('/worldtime',methods=['PUT'])
def world_time():
    url = 'http://worldtimeapi.org/api/timezone/America/New_York'
    timedict = requests.get(url).json()
    datetime, diff = timedict['utc_datetime'], timedict['utc_offset']
    timedict={}
    timedict['year'],timedict['month'],timedict['day'] = int(datetime[:4]), int(datetime[5:7]), int(datetime[8:10])
    timedict['hour'],timedict['minute'],timedict['second'] = modulate(int(str(datetime[11:13])) - int(str(diff[1:3]))), int(datetime[14:16]), int(datetime[17:19])
    return jsonify({'Return':timedict})

app.run(host='0.0.0.0', port=5000)
