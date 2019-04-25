# -*- coding: utf-8 -*-
from __future__ import print_function, division
# from __future__ import unicode_litals, print_function, division
import torch
import torch.nn as nn
from torch.autograd import Variable
import torch.nn.functional as F
import numpy as np
import pdb
from cindy.seq_module import *
from cindy.ctc import CTC
from torch.utils.data import Dataset, DataLoader

from cindy.utils.basic import timeSince
from cindy.utils.chepai_data_loader import ChePaiData_Loader

from cindy.solver import seq_solver
from torch import optim
import cv2
import os
import settings

torch.manual_seed(1701)
torch.cuda.manual_seed_all(1701)
import progressbar
process = progressbar.ProgressBar()

HIDDEN_NUM = settings.network_args['HIDDEN_NUM']
CLASS_NUM = settings.network_args['CLASS_NUM']

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
        class_num = CLASS_NUM
        hidden_num = HIDDEN_NUM
        self.out = nn.Linear(hidden_num, class_num+1)

    def forward(self, input):
        image = input
        input = F.relu(self.conv1(input), True) # 48 * 200
        input = F.max_pool2d(input, kernel_size=(2, 2), stride=(2, 2)) 
        input = F.relu(self.conv2(input), True) # 24 * 100
        input = F.max_pool2d(input, kernel_size=(2, 2), stride=(2, 2))        
        input = F.relu(self.conv3(input), True) # 12 * 50
        input = F.max_pool2d(input, kernel_size=(2, 2), stride=(2, 2))
        input = F.relu(self.conv4(input), True) # 6 * 25
        input = F.relu(self.conv5(input), True) # 6 * 25
        input = F.max_pool2d(input, kernel_size=(2, 1), stride=(2, 1))
        input = F.relu(self.conv6(input), True) # 3 * 25
        input = F.relu(self.batch_norm(self.conv7(input)), True) # 1 * 25（according to experience)
        nB, nC, nH, nW = input.size()
        input = input.view(nB, nC, 1, nH*nW) 
        inp = input[:, :, 0, :].transpose(0, 2).transpose(1, 2)
        output = self.out(inp)
        output = output.transpose(0, 1)
        return output        

def showsettings(s):
    for key in s.keys():
        print(key , s[key])
    print('')

if __name__ == "__main__":

    exp_name = settings.exp_name['exp_name']

    pathfolder = ['model', 'img_show_train', 'wrong_img']
    for i in range(len(pathfolder)):
        if not os.path.exists(pathfolder[i]):
            os.makedirs(pathfolder[i])

    optimizer = settings.optimizer
    scheduler = settings.scheduler
    others = settings.others
    model = settings.model
    lmdb = settings.lmdb

    model['model_type'] = ChePaiReco
    model['model_path'] = 'model/' + exp_name + '-{:0>2d}.pkl'
    lmdb['lmdb_train_type'] = ChePaiData_Loader
    lmdb['lmdb_test_type'] = ChePaiData_Loader

    showsettings(lmdb)
    showsettings(model)
    settings.showsettings(settings.optimizer)
    settings.showsettings(settings.scheduler)
    settings.showsettings(settings.others)
    settings.showsettings(settings.data_args)

    the_solver = seq_solver(criterion = CTC, 
                        model = model,
                        lmdb = lmdb,
                        optimizer = optimizer, 
                        scheduler = scheduler, 
                        train_solver = 'seq_solver',
                        others = others)

    the_solver.forward()

