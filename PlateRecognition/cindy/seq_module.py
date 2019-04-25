# -*- coding: utf-8 -*-
import numpy as np
from torch.autograd import Variable
from cindy.utils.basic import cal_distance
import torch
import pdb
import itertools
from warpctc_pytorch import CTCLoss
import torch.nn as nn
import torch.nn.functional as F
import random
from PIL import Image, ImageDraw
import math
import cv2

import numpy as np  
np.set_printoptions(threshold =1000000, suppress=True, precision=2) 

class Sequence(nn.Module):
    def __init__(self):
        super(Sequence, self).__init__()
        self.count_n = 0

    def loss(self, label, output):
        pass;

    def decode_batch(self):
        length,batch_size,dim = self.softmax.shape
        out_best = torch.max(self.softmax, 2)[1].data
        out_best = out_best.cpu().numpy()
        out_best = out_best.reshape(-1,batch_size)
        out_best = out_best.transpose()
        self.tmp_result = out_best
        out_best_list = [0]*batch_size
        for j in range(out_best.shape[0]):
            out_best_new = [k for k, g in itertools.groupby(out_best[j])]
            # out_best_new = out_best[j]
            out_best_list[j] = [int(x) for x in out_best_new if x != 0]
        return out_best_list

    def result_analysis(self):
        prediction = self.decode_batch()
        batch_size = self.softmax.size(1)
        delete_total = 0
        replace_total = 0
        insert_total = 0
        len_total = 0
        for i in range(batch_size):
            pre_list = prediction[i]
            label_list = self.label[i][self.label[i]!=-1].tolist()
            label_list = [int(ele)+1 for ele in label_list]
            distance, (delete, replace, insert) = cal_distance(label_list, pre_list)
            delete_total += delete
            replace_total += replace
            insert_total += insert
            len_total += len(label_list)
        result = [delete_total, replace_total, insert_total, len_total]
        return prediction, result  


    def result_analysis_recall(self):
        prediction = self.decode_batch()
        batch_size = self.softmax.size(1)
        delete_total = 0
        replace_total = 0
        insert_total = 0
        len_total = 0
        correct_count = 0
        pre_total = 0
        word_total = 0
        all_total = 0
        for i in range(batch_size):
            pre_list = prediction[i]
            label_list = self.label[i][self.label[i]!=-1].tolist()
            label_list = [int(ele)+1 for ele in label_list]
            
            temp_label_list = list()
            for k in range(len(label_list)):
                temp_label_list.append(label_list[k])

            distance, (delete, replace, insert) = cal_distance(label_list, pre_list)
            delete_total += delete
            replace_total += replace
            insert_total += insert
            len_total += len(label_list)
            pre_total += len(pre_list)
            correct_count += len(label_list) - delete - replace;
            if distance == 0:
                word_total += 1 
            # else:
            #     alphabet = u'_深秦京海成南杭苏松0123456789ABCDEFGHJKLMNPQRSTUVWXYZ'
            #     label_list.append(0)
            #     label_list.extend(pre_list)
            #     file_name = 'wrong_img/%d_%s.jpg'%(self.count_n, ''.join([alphabet[j] for j in label_list]))
            #     cv2.imwrite(file_name, self.image[i]*127.5+127.5)
            #     self.count_n += 1                 
            all_total += 1            
        result = [delete_total, replace_total, insert_total, len_total ,correct_count, len_total, pre_total, word_total, all_total]
        return prediction, result 
