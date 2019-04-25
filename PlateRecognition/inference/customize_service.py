#coding=utf-8
# from __future__ import print_function, division
# from __future__ import unicode_litals, print_function, division
import torch
import torch.nn as nn
import itertools
from torch.autograd import Variable
from model_service.pytorch_model_service import PTServingBaseService
import torch.nn.functional as F
import numpy as np
from PIL import Image
# import cv2
import os


class huawei2019(PTServingBaseService):
    def __init__(self,model_name, model_path,gpu=None):
        print(model_name,model_path)
        self.model_name = model_name
        self.model_path = model_path
        self.model = ChePaiReco()
        self.model.load_state_dict(torch.load(model_path, map_location=torch.device('cpu')))


    def _preprocess(self, data):

        for key in data['images'].keys():
            img_path = data['images'][key]

        image = Image.open(img_path).convert('RGB')
        conH = 48
        conW = 200
        w, h = image.size
        imageN = np.zeros((conH, conW, 3))
        beginH = int(abs(conH-h)/2)
        beginW = int(abs(conW-w)/2)

        if h <= conH and w <= conW:
            image = np.asarray(image)
            imageN[beginH:beginH+h, beginW:beginW+w, :] = image
        elif float(h) / w > float(conH) / conW:
            newW = int(w * conH / float(h))
            beginW = int(abs(conW-newW)/2)
            image = image.resize((newW, conH))
            image = np.asarray(image)
            imageN[:,beginW:beginW+newW,:] = image
        elif float(h) / w <= float(conH) / conW:
            newH = int(h * conW / float(w))
            beginH = int(abs(conH-newH)/2)
            image = image.resize((conW, newH))
            image = np.asarray(image)
            imageN[beginH:beginH+newH,:,:] = image
        imageN = imageN.astype('float32')
        imageN = (imageN-127.5)/127.5       
        imageN = imageN.transpose((2,0,1))
        imageN = torch.from_numpy(imageN).unsqueeze(0)
        return imageN    

    def _postprocess(self, data):
        output = data
        output = output.transpose(0, 1)
        out_best = torch.max(output, 2)[1].data.cpu().numpy()[0]
        out_best_new = [k for k, g in itertools.groupby(out_best)]
        out_best_list = [int(x) for x in out_best_new if x != 0]
        dic = '0123456780123456789ABCDEFGHJKLMNPQRSTUVWXYZ'
        result = ''.join([dic[charidx - 1] for charidx in out_best_list])
        print(result)
        return result

    def _inference(self,img):
        return self.model(img)

class ChePaiReco(nn.Module):
    def __init__(self):
        super(ChePaiReco, self).__init__()
        self.conv1  = nn.Conv2d(3,   16,  kernel_size=(3, 3), padding=(1, 1), stride=(1, 1))
        self.conv2  = nn.Conv2d(16,  64,  kernel_size=(3, 3), padding=(1, 1), stride=(1, 1))
        self.conv3  = nn.Conv2d(64,  128,  kernel_size=(3, 3), padding=(1, 1), stride=(1, 1))
        self.conv4  = nn.Conv2d(128, 128,  kernel_size=(3, 3), padding=(1, 1), stride=(1, 1))
        self.conv5  = nn.Conv2d(128, 256,  kernel_size=(3, 3), padding=(1, 1), stride=(1, 1))
        self.conv6  = nn.Conv2d(256, 256,  kernel_size=(3, 3), padding=(1, 1), stride=(1, 1))
        self.conv7  = nn.Conv2d(256, 256,  kernel_size=(3, 1), padding=(0, 0), stride=(3, 1))
        self.batch_norm = nn.BatchNorm2d(256)
        self.out = nn.Linear(256, 44)

    def forward(self, input):
        image = input
        input = F.relu(self.conv1(input), True) # 48 * 1152
        input = F.max_pool2d(input, kernel_size=(2, 2), stride=(2, 2)) 
        input = F.relu(self.conv2(input), True) # 24 * 576
        input = F.max_pool2d(input, kernel_size=(2, 2), stride=(2, 2))        
        input = F.relu(self.conv3(input), True) # 
        input = F.max_pool2d(input, kernel_size=(2, 2), stride=(2, 2))
        input = F.relu(self.conv4(input), True) # 12 * 288
        input = F.relu(self.conv5(input), True) # 
        input = F.max_pool2d(input, kernel_size=(2, 1), stride=(2, 1))
        input = F.relu(self.conv6(input), True) # 
        input = F.relu(self.batch_norm(self.conv7(input)), True) # 1 * 72 or 9 * 3
        nB, nC, nH, nW = input.size()
        inp = input[:, :, 0, :].transpose(0, 2).transpose(1, 2)
        output = self.out(inp)
        output = F.softmax(output, -1)
        return output        

