import pymongo
import numpy as np
import sklearn
from sklearn.preprocessing import StandardScaler
from sklearn import model_selection, metrics
from sklearn.neural_network import MLPClassifier
from sklearn.ensemble import RandomForestClassifier
from joblib import dump

client = pymongo.MongoClient()
db = client.test_database
collection = db.collection 
collection.delete_many({'Tag':'Test'})

data_numbers = collection.count_documents({})
data_dim = len(collection.find_one({})['datas']) * 3

X = np.zeros((data_numbers, data_dim))
y = np.zeros((data_numbers, ))
print(X.shape)
label_index = ['c', 'o', 'l', 'u', 'm', 'b', 'i', 'a']
for index, data in enumerate(collection.find({})):
    datas, label = data['datas'], data['label']
    X[index, :] = np.array(datas).flatten()
    y[index] = label_index.index(label)

X, y = sklearn.utils.shuffle(X, y)

train_X, test_X, train_y, test_y = model_selection.train_test_split(X, y, test_size=0.2)
scaler = StandardScaler(); scaler.fit(train_X)
train_X = scaler.transform(train_X); test_X = scaler.transform(test_X)

clf = RandomForestClassifier(max_depth=5, random_state=0)
print('start training')
clf.fit(train_X, train_y)

# clf = MLPClassifier(solver='lbfgs', hidden_layer_sizes=(100, len(label_index)), alpha=1e-5, random_state=1, max_iter=400)
# print('start training')
# clf.fit(train_X, train_y)

y_prediction = clf.predict(test_X)
accuracy = np.sum(y_prediction == test_y) / test_y.shape[0]
matrix = metrics.confusion_matrix(test_y, y_prediction)
print('Acuracy is:', accuracy)
print(matrix)
dump((scaler, clf), 'model_11_11.joblib')