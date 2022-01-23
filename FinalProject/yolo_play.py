import torch
import numpy as np
import cv2

class Model(object):
    def __init__(self):
        # self.model = torch.hub.load('ultralytics/yolov5', 'yolov5l') # yolov5模型
        self.model = torch.hub.load('ultralytics/yolov5', 'custom',
                                    path='D:\Learning\\Newlearning\IOT\Project\yolov5\\runs\\train\exp13\\weights\\best.pt')  # default
        self.class_name = np.array(['metal', 'paper', 'plastic'])

    def get_predict(self, picture):
        self.predict = self.model(picture)
        datatable = self.predict.pandas().xyxy[0]
        temp = np.array(list(zip(datatable.name, datatable.confidence)))
        result_box = np.zeros((3, ))
        times_box = np.zeros((3, )) + 1e-10
        for i in range(temp.shape[0]):
            name = temp[i, 0]; confidence = float(temp[i, 1])
            index = np.where(self.class_name==name)[0][0]
            # index = int(name) # name 0, 1, 2
            result_box[index] += confidence
            times_box[index] += 1
        return result_box/times_box