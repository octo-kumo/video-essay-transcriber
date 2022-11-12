import random

import cv2 as cv
import numpy as np

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib

import torch

from keras.applications.vgg16 import VGG16
from keras.models import Model

from sklearn.cluster import KMeans

import scenedetect
from tqdm import trange


class keyFrame:
    # model_yolo = torch.hub.load('ultralytics/yolov3', 'yolov3')  # or yolov3-spp, yolov3-tiny, custom
    # model_vgg = VGG16()
    # model_vgg = Model(inputs=model_vgg.inputs, outputs=model_vgg.layers[-2].output)

    def get_square(self, x1, y1, x2, y2):
        x = x2 - x1
        y = y2 - y1

        if (y >= x):
            y2 -= y - x
        else:
            x1 += (x - y) // 2
            x2 -= (x - y) // 2

        return x1, y1, x2, y2

    def ratio(self, dim, x1, y1, x2, y2):
        return ((x2 - x1) / dim[1]) * ((y2 - y1) / dim[0])

    def normalize(self, img):
        return cv.cvtColor(cv.cvtColor(img, cv.COLOR_RGB2GRAY), cv.COLOR_GRAY2RGB)  # wtf

    def __init__(self, path, window=None):
        cap = cv.VideoCapture(path)
        a = scenedetect.detect(path,
                               scenedetect.detectors.AdaptiveDetector(
                                   adaptive_threshold=5.0,
                                   min_scene_len=int(cap.get(cv.CAP_PROP_FPS))
                               ),
                               )

        self.times = []
        for p in a:
            self.times.append(p[0].get_frames())
        self.times.append(a[-1][1].get_frames())

        num = 0
        cap = cv.VideoCapture(path)
        fps = cap.get(cv.CAP_PROP_FPS)
        print("fps = ", fps)
        self.frames = {}
        while (cap.isOpened()):
            ret, frame = cap.read()
            if (ret):
                if (num in self.times or num + 1 in self.times):
                    self.frames[num] = frame[..., ::-1]
                num += 1
            else:
                break

        self.yolo_out = {}
        self.faces = []
        for i in trange(len(self.times)):
            for j in range(1):
                if (self.times[i] - 1 + j in self.frames):
                    self.yolo_out[self.times[i] - 1 + j] = self.model_yolo(self.frames[self.times[i] - 1 + j])
                    for obj in self.yolo_out[self.times[i] - 1 + j].xyxy[0]:
                        if (obj[-1] == 0):
                            (x1, y1, x2, y2) = [int(obj[i]) for i in range(4)]
                            if (self.ratio(self.frames[self.times[i] - 1 + j].shape, x1, y1, x2, y2) <= 1 / 4): continue
                            (x1, y1, x2, y2) = self.get_square(x1, y1, x2, y2)
                            self.faces.append(
                                self.normalize(cv.resize(self.frames[self.times[i] - 1 + j][y1:y2, x1:x2], (224, 224),
                                                         interpolation=cv.INTER_AREA))
                            )
            if window: window['frame-progress'].UpdateBar(i, len(self.times))

        faces_flat = self.model_vgg.predict(np.array(self.faces))
        self.cluster = min(5, faces_flat.shape[0])
        self.res = KMeans(n_clusters=self.cluster, random_state=42).fit(faces_flat).labels_

    def get_clusters(self):
        ret = []
        for i in range(self.cluster):
            temp = []
            for j in range(5):
                idx = 0
                while (True):
                    idx = random.randint(0, len(self.faces) - 1)
                    if idx == i: break
                temp.append(self.faces[idx])
            ret.append(temp)

        return ret

    def get_frames(self, bad):
        fin = []

        idx = 0
        for i in range(1, len(self.times)):
            isBad = 0
            height, width = (self.frames[self.times[i] - 1].shape[0], self.frames[self.times[i] - 1].shape[1])
            mn, mx = 0, width
            for obj in self.yolo_out[self.times[i] - 1].xyxy[0]:
                if (obj[-1] == 0):
                    (x1, y1, x2, y2) = [int(obj[i]) for i in range(4)]
                    if (self.ratio(self.frames[self.times[i] - 1].shape, x1, y1, x2, y2) <= 1 / 4): continue

                    isBad |= bad[self.res[idx]]
                    if (bad[self.res[idx]]):
                        mn = max(mn, x2)
                        mx = min(mx, x1)
                    idx += 1

            time = (self.times[i - 1] + self.times[i]) // 2
            if (isBad):
                if mn < width / 2:
                    fin.append((time, self.frames[self.times[i] - 1][0:height, mn:width]))
                elif width / 2 < mx:
                    fin.append((time, self.frames[self.times[i] - 1][0:height, 0:mx]))

            else:
                fin.append((time, self.frames[self.times[i] - 1]))

        return fin
