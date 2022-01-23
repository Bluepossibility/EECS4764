import json
import numpy as np
from flask import Flask, request, jsonify
import pandas
import requests
from yolo_play import Model
import datetime
import csv
from final_project_classes import *

model = Model()
default_class = ['metal', 'paper', 'plastic', 'other']
adjusting = {0:'metal', 1:'paper', 2:'plastic', 3:'other'}

 # Our data base structure {int(id):{'volume':[[datatime, volume each class]], 'location':[lat, lon]}}
reset_database = {}; new_key_db = {1:{0:'metal', 1:'other', 2:'plastic', 3:'paper'}, 2: {0:'paper', 1:'other', 2:'plastic', 3:'metal'}}
local_data = []
t = 0; time_range = 9; threshold = 0.15 # time range is time_range+1; 'data':[length time_range+1 list for average]
#------------------
lat, lon = 40.810033, -73.96201  # nwc
lat1, lon1 = 40.802948, -73.964268  # old home
database = {1: {'volume': [[get_datetime(), 0., 0., 0., 0.]], 'location': [lat1, lon1]}, 2: {'volume': [[get_datetime(), 0.0, 0.0, 0.0, 0.0]], 'location': [lat, lon]}}
m = Map(database)
m.initialize_random() # initialize random trash can for only simulation
m.update_map(new_key_db)

map_key = 'AIzaSyDVsu34HwY6IHeqaah5CLT_pMZbhgr9mQo' # google map key for future path plan
#--------------------------------------------------
app = Flask(__name__)

@app.route('/picture', methods=['PUT'])
def predict_timerange():
    data = json.loads(request.data)
    picture = np.array(data, dtype='uint8')
    result = model.get_predict(picture) # return confidence for each class, the order is same as default_class
    local_data.append(result)
    local_data = local_data[-time_range:] # only preserves 10 times predictino results for average
    prediction = np.mean(local_data, axis=0) # average confidence for each class
    final_result = []
    for i in range(prediction.shape[0]):
        if prediction[i] >= threshold:
            final_result.append([default_class[i], prediction[i]])
    if len(final_result) > 1:
        final_result = np.array(final_result); index = final_result[:, 1].astype('float32')
        final_result = final_result[index.argsort()].tolist() # sort confidence from small to large
    return jsonify({'results': final_result})

@app.route('/volume', methods=['PUT'])
def record_volume():
    volume_pac = json.loads(request.data) # time t, volume in each class
    for i in volume_pac.keys(): # only have one key, string i
        volume_with_time = volume_pac[i]['volume']
        database[int(i)]['volume'] += volume_with_time # database must use int index, because json would transfer int to str
    generate_pic(database)
    m.update_map(new_key_db)
    return jsonify('Get!')

@app.route('/location', methods=['PUT'])
def record_location():
    location = json.loads(request.data)
    for i in location.keys():
        location = location[i]['location']
        if int(i) in database.keys(): database[int(i)]['location'] = location
        else: database[int(i)] = {'volume': [], 'location':location}
    database[1]['location'] = [lat1, lon1]
    database[2]['location'] = [lat, lon]
    return jsonify('Get Location!')

@app.route('/reset', methods=['PUT'])
def reset():
    # compute dynamic adjusting; id is {'index':id}
    reset_index = json.loads(request.data)
    index = int(list(reset_index.keys())[0])
    volume_last = database[index]['volume'][-1][1:]
    if not index in reset_database.keys(): reset_database[index] = [volume_last]
    else: reset_database[index].append(volume_last)
    new_key = np.argsort(np.mean(reset_database[index], axis=0))
    for i in range(len(default_class)):
        adjusting[i] = default_class[new_key[i]] # adjusting 0, 1, 2, 3 represents default_class
    new_key_db[index] = adjusting
    database[index]['volume'].append([get_datetime(), 0, 0, 0, 0]) # clear all trash to reset
    m.update_map(new_key_db)
    return jsonify(adjusting)

@app.route('/picture', methods=['DELETE'])
def remove():
    for key in database.keys():
        w = csv.writer(open('output.csv'+str(key), 'w'))
        for time, volume in database[key]:
            w.writerow([time, volume])
    database[key]['volume']=[datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S"), 0, 0, 0, 0]
    return jsonify({'Return':'Sucess Save and show new plot'})

app.run(host='0.0.0.0', port=5000)