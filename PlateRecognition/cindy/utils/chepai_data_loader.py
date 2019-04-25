# -*- coding: utf-8 -*-

from torch.utils.data import Dataset, DataLoader
import numpy as np
import os
import torch
import Augment
import cv2
import random
import sys  
import settings
from math import *
reload(sys)  
sys.setdefaultencoding('utf8')

EASY = settings.data_args['EASY']
AUG = settings.data_args['AUG']
HEIGHT = settings.data_args['HEIGHT']
WIDTH = settings.data_args['WIDTH']
KEEP_RATIO = settings.data_args['KEEP_RATIO']
LABEL_LEN = settings.data_args['LABEL_LEN']
DATA_PATHHEAD = settings.data_args['DATA_PATHHEAD']
AUG_RATIO = settings.data_args['AUG_RATIO']
BINARY = settings.data_args['BINARY']
TEST_TWODATASET = settings.data_args['TEST_TWODATASET']
MORE_AUG_RATIO = settings.data_args['MORE_AUG_RATIO']
MORE_AUG = settings.data_args['MORE_AUG']


class LineGenerate():

    def __init__(self, L_ScorePath, conH, conW, is_train, testdata_idx=0):

        self.conH = conH
        self.conW = conW
        self.image = []
        self.label = []
        self.path  = []
        self.is_train = is_train
        count = 0
        with open(L_ScorePath) as f:
            for line in f.readlines():
                onelabel = line.strip().split(",  ")[0]
                onepath = line.strip().split(",  ")[1]
                if testdata_idx == 0:
                    pth = DATA_PATHHEAD + "train-data/train-data/" + onepath
                else:
                    pth = "../0000_data/0006_plate/diy-test/train-data/" + onepath
                if BINARY:
                    img = cv2.imread(pth, 0) #see channel and type
                else:
                    img = cv2.imread(pth) #see channel and type
                    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB) 
                self.path.append(pth)
                self.image.append(img) 
                self.label.append(onelabel)
                count += 1                
                if count % 1000 == 0:
                    print(count)
        print(count)
        self.len = count
        self.testidx = 0
        if BINARY:
            self.smu = cv2.imread(DATA_PATHHEAD + "smu2.jpg", 0)
        else:
            self.smu = cv2.imread(DATA_PATHHEAD + "smu2.jpg")
            self.smu = cv2.cvtColor(self.smu, cv2.COLOR_BGR2RGB) 


    def get_len(self):
        return self.len

    def generate_line(self):
        #  random select in training dataset, and order in testing dataset
        if self.is_train:
            idx = int(torch.randint(high = self.len,size = (1,)).item())
        else:
            idx = self.testidx
            self.testidx += 1
            if self.testidx == self.len:
                self.testidx = 0

        path = self.path[idx]
        image = self.image[idx]
        if BINARY:
            if KEEP_RATIO:
                h,w = image.shape
                imageN = np.zeros((self.conH,self.conW))
                if self.is_train:
                    beginH = random.randint(0, int(abs(self.conH-h)))
                    beginW = random.randint(0, int(abs(self.conW-w)))
                else:
                    beginH = int(abs(self.conH-h)/2)
                    beginW = int(abs(self.conW-w)/2)
                if h <= self.conH and w <= self.conW:
                    imageN[beginH:beginH+h, beginW:beginW+w] = image
                elif float(h) / w > float(self.conH) / self.conW:
                    newW = int(w * self.conH / float(h))
                    if self.is_train:
                        beginW = random.randint(0, int(abs(self.conW-w)))
                    beginW = int(abs(self.conW-newW)/2)
                    image = cv2.resize(image, (newW, self.conH))
                    imageN[:,beginW:beginW+newW] = image
                elif float(h) / w <= float(self.conH) / self.conW:
                    newH = int(h * self.conW / float(w))
                    if self.is_train:
                        beginW = random.randint(0, int(abs(self.conW-w)))
                    beginH = int(abs(self.conH-newH)/2)
                    image = cv2.resize(image, (self.conW, newH))
                    imageN[beginH:beginH+newH,:] = image
                else:
                    print("????????????????????????")
            else:
                image = cv2.resize(image, (self.conW, self.conH))
        else:
            if KEEP_RATIO:
                h,w,_ = image.shape
                imageN = np.zeros((self.conH,self.conW,3))
                if self.is_train:
                    beginH = random.randint(0, int(abs(self.conH-h)))
                    beginW = random.randint(0, int(abs(self.conW-w)))
                else:
                    beginH = int(abs(self.conH-h)/2)
                    beginW = int(abs(self.conW-w)/2)
                if h <= self.conH and w <= self.conW:
                    imageN[beginH:beginH+h, beginW:beginW+w, :] = image
                elif float(h) / w > float(self.conH) / self.conW:
                    newW = int(w * self.conH / float(h))
                    if self.is_train:
                        beginW = random.randint(0, int(abs(self.conW-w)))
                    beginW = int(abs(self.conW-newW)/2)
                    image = cv2.resize(image, (newW, self.conH))
                    imageN[:,beginW:beginW+newW,:] = image
                elif float(h) / w <= float(self.conH) / self.conW:
                    newH = int(h * self.conW / float(w))
                    if self.is_train:
                        beginW = random.randint(0, int(abs(self.conW-w)))
                    beginH = int(abs(self.conH-newH)/2)
                    image = cv2.resize(image, (self.conW, newH))
                    imageN[beginH:beginH+newH,:,:] = image
                else:
                    print("????????????????????????")
            else:
                image = cv2.resize(image, (self.conW, self.conH))

        label = self.label[idx]

        if AUG:
            if self.is_train:
                # parts = 4
                parts = random.randint(2, 6)
                imageN = imageN.astype('uint8')
                if torch.rand(1) < AUG_RATIO:
                    imageN = Augment.GenerateDistort(imageN, parts)
                if torch.rand(1) < AUG_RATIO:
                    imageN = Augment.GenerateStretch(imageN, parts)
                if torch.rand(1) < AUG_RATIO:
                    imageN = Augment.GeneratePerspective(imageN)
        if MORE_AUG and self.is_train:
            imageN = imageN.astype('uint8')
            if np.random.rand() < MORE_AUG_RATIO:
                imageN = rot(imageN, r(60) - 30, imageN.shape, 30);
            if np.random.rand() < MORE_AUG_RATIO:
                imageN = rotRandrom(imageN, 10, (imageN.shape[1], imageN.shape[0]));
            if np.random.rand() < MORE_AUG_RATIO:
                imageN = AddSmudginess(imageN, self.smu)
            if np.random.rand() < MORE_AUG_RATIO and not BINARY:
                imageN = tfactor(imageN)    
            if np.random.rand() < MORE_AUG_RATIO:
                imageN = AddGauss(imageN, 1 + r(2));
            imageN = cv2.resize(imageN, (self.conW, self.conH))
            if torch.rand(1) < 0.001 and self.is_train:
                img = cv2.cvtColor(imageN, cv2.COLOR_RGB2BGR) 
                cv2.imwrite("img_show_train/%s.jpg" % label, img)

        return imageN, label, path


class ChePaiData_Loader(Dataset):
    """Face Landmarks dataset."""

    def __init__(self, lmdb_file, length, testdata_idx = 0, transform=None):
        """
        Args:
            csv_file (string): Path to the csv file with annotations.
            root_dir (string): Directory with all the images.
        transform (callable, optional): Optional transform to be applied
            on a sample.
        """
        if lmdb_file == "train":
            self.is_train = True
        else:
            self.is_train = False

        if self.is_train == True:
            L_ScorePath = DATA_PATHHEAD + 'train_data.txt'
        else:
            if TEST_TWODATASET:
                if testdata_idx == 0:
                    L_ScorePath = DATA_PATHHEAD + 'test_data.txt'
                else:
                    # import pdb; pdb.set_trace()
                    L_ScorePath = "../0000_data/0006_plate/diy-test/train-data-label.txt"
            else:
                L_ScorePath = DATA_PATHHEAD + 'test_data.txt'

        self.length = length
        self.conW = WIDTH
        self.conH = HEIGHT
        self.LG = LineGenerate(L_ScorePath, self.conH, self.conW, self.is_train, testdata_idx)

        self.dict = {}
        self.alphabet = u'深$秦$京$海$成$南$杭$苏$松$0$1$2$3$4$5$6$7$8$9$A$B$C$D$E$F$G$H$J$K$L$M$N$P$Q$R$S$T$U$V$W$X$Y$Z'.split('$')
        for i, item in enumerate(self.alphabet):
            self.dict[item] = i



    def __len__(self):
        if self.is_train:
            return self.length
        else:
            return self.LG.get_len()


    def __getitem__(self, idx):
        
        imageN, label, path = self.LG.generate_line()
        try:
            text = [self.dict[char] for char in label.decode('utf-8')]
        except:
            pdb.set_trace()

        label = np.zeros(LABEL_LEN)-1
        label[:len(text)]=text
        label = label.astype('int')

        imageN = imageN.astype('float32')
        imageN = (imageN-127.5)/127.5

        try:
            if not BINARY:
                imageN = imageN.transpose((2,0,1))
            else:
                imageN = imageN.reshape(1, imageN.shape[0], imageN.shape[1])
            sample = {'image': torch.from_numpy(imageN), 'label': torch.from_numpy(label)}
        except:
            pdb.set_trace()

        return sample  


def AddSmudginess(img, Smu):
    rows = r(Smu.shape[0] - HEIGHT)
    cols = r(Smu.shape[1] - WIDTH)
    adder = Smu[rows:rows + HEIGHT, cols:cols + WIDTH]
    adder = cv2.resize(adder, (WIDTH, HEIGHT))
    #   adder = cv2.bitwise_not(adder)
    img = cv2.resize(img, (WIDTH, HEIGHT))
    img = cv2.bitwise_not(img)
    img = cv2.bitwise_and(adder, img)
    img = cv2.bitwise_not(img)
    return img


def rot(img, angel, shape, max_angel):
    """ 使图像轻微的畸变

        img 输入图像
        factor 畸变的参数
        size 为图片的目标尺寸

    """
    size_o = [shape[1], shape[0]]

    size = (shape[1] + int(shape[0] * cos((float(max_angel) / 180) * 3.14)), shape[0])

    interval = abs(int(sin((float(angel) / 180) * 3.14) * shape[0]));

    pts1 = np.float32([[0, 0], [0, size_o[1]], [size_o[0], 0], [size_o[0], size_o[1]]])
    if (angel > 0):

        pts2 = np.float32([[interval, 0], [0, size[1]], [size[0], 0], [size[0] - interval, size_o[1]]])
    else:
        pts2 = np.float32([[0, 0], [interval, size[1]], [size[0] - interval, 0], [size[0], size_o[1]]])

    M = cv2.getPerspectiveTransform(pts1, pts2);
    dst = cv2.warpPerspective(img, M, size);

    return dst;


def rotRandrom(img, factor, size):
    shape = size;
    pts1 = np.float32([[0, 0], [0, shape[0]], [shape[1], 0], [shape[1], shape[0]]])
    pts2 = np.float32([[r(factor), r(factor)], [r(factor), shape[0] - r(factor)], [shape[1] - r(factor), r(factor)],
                       [shape[1] - r(factor), shape[0] - r(factor)]])
    M = cv2.getPerspectiveTransform(pts1, pts2);
    dst = cv2.warpPerspective(img, M, size);
    return dst;


def tfactor(img):
    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV);

    hsv[:, :, 0] = hsv[:, :, 0] * (0.8 + np.random.random() * 0.2);
    hsv[:, :, 1] = hsv[:, :, 1] * (0.8 + np.random.random() * 0.2);
    hsv[:, :, 2] = hsv[:, :, 2] * (0.8 + np.random.random() * 0.2);

    img = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB);
    return img

def AddGauss(img, level):
    return cv2.blur(img, (level * 2 + 1, level * 2 + 1));


def r(val):
    return int(np.random.random() * val)
