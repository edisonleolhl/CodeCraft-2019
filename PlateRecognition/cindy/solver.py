import torch.nn as nn
from cindy.utils.basic import cindy_gradient_clip
import torch
from torch.autograd import Variable
from torch.utils.data import DataLoader
import time
from warpctc_pytorch import CTCLoss
import numpy as np
from cindy.utils.basic import timeSince
import settings

class solver(object):

    def __init__(self, criterion, model, lmdb, optimizer, scheduler, train_solver, others, pre_train = False):

        self.loss_layer = criterion()

        self.model = model['model_type']().cuda()

        self.mode = model['mode']

        self.multigpus = False

        if model['ngpu'] != None:
            self.multigpus = True

        if self.multigpus:
            self.model = nn.DataParallel(self.model, device_ids=model['ngpu'])
        print(self.model)

        if optimizer['momentum']:
            self.optimizer = optimizer['optim_type'](self.model.parameters(), lr=optimizer['lr'], momentum=optimizer['momentum'], weight_decay = optimizer['weight_decay'])
        else:
            self.optimizer = optimizer['optim_type'](self.model.parameters(), lr=optimizer['lr'], weight_decay = optimizer['weight_decay'])

        if self.mode == "Train":        
            data_set = lmdb['lmdb_train_type'](lmdb_file = lmdb['lmdb_train_path'], length = lmdb['lmdb_train_length'])
            if lmdb['lmdb_train_length'] == 0:
                self.lmdb_train = DataLoader(data_set, batch_size=lmdb['batch_size_train'], shuffle=True, num_workers=0) 
            else:
                self.lmdb_train = DataLoader(data_set, batch_size=lmdb['batch_size_train'], shuffle=True, num_workers=0) 
        if settings.data_args['TEST_TWODATASET']:
            data_set = lmdb['lmdb_test_type'](lmdb_file = lmdb['lmdb_test_path'], length = lmdb['lmdb_test_length'], testdata_idx=0)
            self.lmdb_test1 = DataLoader(data_set, batch_size=lmdb['batch_size_test'], shuffle=False, num_workers=0) 
            data_set = lmdb['lmdb_test_type'](lmdb_file = lmdb['lmdb_test_path'], length = lmdb['lmdb_test_length'], testdata_idx=1)
            self.lmdb_test2 = DataLoader(data_set, batch_size=lmdb['batch_size_test'], shuffle=False, num_workers=0)             
        else:
            data_set = lmdb['lmdb_test_type'](lmdb_file = lmdb['lmdb_test_path'], length = lmdb['lmdb_test_length'])
            self.lmdb_test = DataLoader(data_set, batch_size=lmdb['batch_size_test'], shuffle=False, num_workers=0) 

        self.total_epoch = scheduler['total_epoch']

        self.others = others
        self.log_path = others['log_path']
        self.model_path = model['model_path']
        if train_solver == 'seq_solver':
            self.train_solver = seq_solver
        self.start = time.time()

        # input('wait')

    def train_one_epoch(self, ep):
        pass
    def test_one_epoch(self, ep):
        pass

    def forward(self):
        if settings.data_args['TEST_TWODATASET']:
            if self.mode == "Train":
                for ep in range(self.total_epoch-self.last_epoch):
                    ep = ep+self.last_epoch
                    self.train_one_epoch(ep)
                    self.test_one_epoch_twodataset(ep)
            else:
                self.test_one_epoch_testonly_twodataset()            
        else:
            if self.mode == "Train":
                for ep in range(self.total_epoch-self.last_epoch):
                    ep = ep+self.last_epoch
                    self.train_one_epoch(ep)
                    self.test_one_epoch(ep)
            else:
                self.test_one_epoch_testonly()
        
import pdb
class seq_solver(solver):

    def __init__(self, criterion, model, lmdb, optimizer, scheduler, train_solver, others, pre_train = False):
        super(seq_solver, self).__init__(criterion, model, lmdb, optimizer, scheduler, train_solver, others, pre_train)
        last_epoch = -1
        self.last_epoch = 0
        if model['loading_epoch'] != 0:
            check_point = torch.load(model['model_path'].format(model['loading_epoch']))
            self.model.load_state_dict(check_point['state_dict'])
            self.optimizer.load_state_dict(check_point['optimizer'])
            last_epoch = model['loading_epoch']
            self.last_epoch = last_epoch + 1
        self.scheduler = scheduler['scheduler_type'](self.optimizer, milestones = scheduler['milestones'], gamma = scheduler['gamma'], last_epoch=last_epoch)

    def train_one_epoch(self, ep):
        self.model.train()
        loss_aver = 0
        if self.scheduler is not None:
            self.scheduler.step()
            print('learning_rate: ', self.scheduler.get_lr())   
        for it, (sample_batched) in enumerate(self.lmdb_train):
            inputs = sample_batched['image'].squeeze(0)
            labels = sample_batched['label'].squeeze(0)

            inputs = Variable(inputs.cuda())

            output = self.model(inputs)
            output = output.transpose(0, 1)
            loss = self.loss_layer(output, labels, inputs)
            self.optimizer.zero_grad()
            loss.backward()
            loss = loss.data[0]
            l2_norm = cindy_gradient_clip(self.model)

            if not np.isnan(l2_norm):
                self.optimizer.step()
            else:
                print('l2_norm: ', l2_norm)
                l2_norm = 0

            if it == 0:
                loss_aver = loss
            if(loss > 10000 or loss < 0):
                loss = loss_aver
                print('inf')
            if not np.isnan(loss):           
                loss_aver = 0.9*loss_aver+0.1*loss            

            if (ep == 0 and it < 1000 and it % 100 == 0) or (it % 1000 == 0):
                prediction, result = self.loss_layer.result_analysis_recall()
                CR = 1-(float)(result[0]+result[1])/result[3]
                AR = 1-(float)(result[0]+result[1]+result[2])/result[3]
                recall = float(result[4]) / result[5]
                precision = float(result[4]) / (result[6]+0.000001)             
                WER = float(result[7])/result[8]
                print('Train: %10s Epoch: %3d it: %6d, loss: %.4f CR: %.4f  AR: %4f, l2_norm: %.4f, recall: %.4f, precision: %.4f, WER: %.4f' % 
                    (timeSince(self.start), ep, it, loss_aver, CR, AR, l2_norm, recall, precision,WER))

            if it%10000 == 0 and it != 0:
                self.test_one_epoch(ep)
                self.model.train()

        prediction, result = self.loss_layer.result_analysis_recall()
        CR = 1-(float)(result[0]+result[1])/result[3]
        AR = 1-(float)(result[0]+result[1]+result[2])/result[3]
        recall = float(result[4]) / result[5]
        precision = float(result[4]) / (result[6]+0.000001)         
        WER = float(result[7])/result[8]
        print('Train: %10s Epoch: %3d it: %6d, loss: %.4f CR: %.4f  AR: %4f, l2_norm: %.4f, recall: %.4f, precision: %.4f, WER: %.4f' % 
            (timeSince(self.start), ep, it, loss_aver, CR, AR, l2_norm, recall, precision, WER))
        f = open(self.log_path+'TrainAccuracyLoss.log', 'a')
        f.write('%d %f %f %f %f %f %f\n' % (ep, loss_aver, CR, AR, recall, precision, WER))
        f.close();

        torch.save({
            'epoch': ep,
            'state_dict': self.model.state_dict(),
            'optimizer' : self.optimizer.state_dict(),
            }, self.model_path.format(ep))  


    def test_one_epoch(self, ep):
        self.model.eval()
        loss_aver = 0
        total_result = [0]*9
        for it, (sample_batched) in enumerate(self.lmdb_test):
            inputs = sample_batched['image'].squeeze(0)
            labels = sample_batched['label'].squeeze(0)

            inputs = Variable(inputs.cuda())
            output = self.model(inputs)
            output = output.transpose(0, 1)
            loss = self.loss_layer(output, labels, inputs)
            prediction, result = self.loss_layer.result_analysis_recall()
            loss = loss.data[0]
            if it == 0:
                loss_aver = loss
            loss_aver = 0.9*loss_aver+0.1*loss      

            for i, ele in enumerate(result):
                total_result[i] += ele 

            if it % 5000 == 0:
                CR = 1-(float)(total_result[0]+total_result[1])/total_result[3]
                AR = 1-(float)(total_result[0]+total_result[1]+total_result[2])/total_result[3] 
                recall = float(total_result[4]) / total_result[5]
                precision = float(total_result[4]) / (total_result[6]+0.000001)                     
                WER = float(total_result[7])/total_result[8]
                print('Test : %10s Epoch: %3d it: %6d, loss: %.4f CR: %.4f  AR: %4f  delete: %4f, replace: %4f, insert: %4f, len : %4d, recall: %.4f, precision: %.4f, WER: %.4f, right_word: %4d, total word: %.4f' % 
                            (timeSince(self.start), ep, it, loss_aver, CR, AR, total_result[0], total_result[1], total_result[2], total_result[3], recall, precision, WER, total_result[7], total_result[8]))   

        CR = 1-(float)(total_result[0]+total_result[1])/total_result[3]
        AR = 1-(float)(total_result[0]+total_result[1]+total_result[2])/total_result[3]     
        recall = float(total_result[4]) / total_result[5]
        precision = float(total_result[4]) / (total_result[6]+0.000001)             
        WER = float(total_result[7])/total_result[8]
        print('Test : %10s Epoch: %3d it: %6d, loss: %.4f CR: %.4f  AR: %4f  delete: %4d, replace: %4d, insert: %4d, len : %4d, recall: %.4f, precision: %.4f correct: %4d, len: %4d, pre_len: %4d, WER: %.4f, right_word: %4d, total word: %.4f' % 
                    (timeSince(self.start), ep, it, loss_aver, CR, AR, total_result[0], total_result[1], total_result[2], total_result[3], recall, precision, total_result[4], total_result[5], total_result[6],WER, total_result[7], total_result[8])) 

        f = open(self.log_path+'TestAccuracyLoss.log', 'a')
        f.write('%d %f %f %f %f %f %f\n' % (ep, loss_aver, CR, AR, recall, precision, WER))
        f.close();

    def test_one_epoch_twodataset(self, ep):
        self.model.eval()
        loss_aver = 0
        total_result = [0]*9
        for it, (sample_batched) in enumerate(self.lmdb_test1):
            inputs = sample_batched['image'].squeeze(0)
            labels = sample_batched['label'].squeeze(0)

            inputs = Variable(inputs.cuda())
            output = self.model(inputs)
            output = output.transpose(0, 1)
            loss = self.loss_layer(output, labels, inputs)
            prediction, result = self.loss_layer.result_analysis_recall()
            loss = loss.data[0]
            if it == 0:
                loss_aver = loss
            loss_aver = 0.9*loss_aver+0.1*loss      

            for i, ele in enumerate(result):
                total_result[i] += ele 

            if it % 5000 == 0:
                CR = 1-(float)(total_result[0]+total_result[1])/total_result[3]
                AR = 1-(float)(total_result[0]+total_result[1]+total_result[2])/total_result[3] 
                recall = float(total_result[4]) / total_result[5]
                precision = float(total_result[4]) / (total_result[6]+0.000001)                     
                WER = float(total_result[7])/total_result[8]
                print('Test : %10s Epoch: %3d it: %6d, loss: %.4f CR: %.4f  AR: %4f  delete: %4f, replace: %4f, insert: %4f, len : %4d, recall: %.4f, precision: %.4f, WER: %.4f, right_word: %4d, total word: %.4f' % 
                            (timeSince(self.start), ep, it, loss_aver, CR, AR, total_result[0], total_result[1], total_result[2], total_result[3], recall, precision, WER, total_result[7], total_result[8]))   

        CR = 1-(float)(total_result[0]+total_result[1])/total_result[3]
        AR = 1-(float)(total_result[0]+total_result[1]+total_result[2])/total_result[3]     
        recall = float(total_result[4]) / total_result[5]
        precision = float(total_result[4]) / (total_result[6]+0.000001)             
        WER = float(total_result[7])/total_result[8]
        print('Test : %10s Epoch: %3d it: %6d, loss: %.4f CR: %.4f  AR: %4f  delete: %4d, replace: %4d, insert: %4d, len : %4d, recall: %.4f, precision: %.4f correct: %4d, len: %4d, pre_len: %4d, WER: %.4f, right_word: %4d, total word: %.4f' % 
                    (timeSince(self.start), ep, it, loss_aver, CR, AR, total_result[0], total_result[1], total_result[2], total_result[3], recall, precision, total_result[4], total_result[5], total_result[6],WER, total_result[7], total_result[8])) 

        f = open(self.log_path+'TestAccuracyLoss.log', 'a')
        f.write('%d %f %f %f %f %f %f\n' % (ep, loss_aver, CR, AR, recall, precision, WER))
        f.close();

        loss_aver = 0
        total_result = [0]*9
        for it, (sample_batched) in enumerate(self.lmdb_test2):
            inputs = sample_batched['image'].squeeze(0)
            labels = sample_batched['label'].squeeze(0)

            inputs = Variable(inputs.cuda())
            output = self.model(inputs)
            output = output.transpose(0, 1)
            loss = self.loss_layer(output, labels, inputs)
            prediction, result = self.loss_layer.result_analysis_recall()
            loss = loss.data[0]
            if it == 0:
                loss_aver = loss
            loss_aver = 0.9*loss_aver+0.1*loss      

            for i, ele in enumerate(result):
                total_result[i] += ele 

            if it % 5000 == 0:
                CR = 1-(float)(total_result[0]+total_result[1])/total_result[3]
                AR = 1-(float)(total_result[0]+total_result[1]+total_result[2])/total_result[3] 
                recall = float(total_result[4]) / total_result[5]
                precision = float(total_result[4]) / (total_result[6]+0.000001)                     
                WER = float(total_result[7])/total_result[8]
                print('Test : %10s Epoch: %3d it: %6d, loss: %.4f CR: %.4f  AR: %4f  delete: %4f, replace: %4f, insert: %4f, len : %4d, recall: %.4f, precision: %.4f, WER: %.4f, right_word: %4d, total word: %.4f' % 
                            (timeSince(self.start), ep, it, loss_aver, CR, AR, total_result[0], total_result[1], total_result[2], total_result[3], recall, precision, WER, total_result[7], total_result[8]))   

        CR = 1-(float)(total_result[0]+total_result[1])/total_result[3]
        AR = 1-(float)(total_result[0]+total_result[1]+total_result[2])/total_result[3]     
        recall = float(total_result[4]) / total_result[5]
        precision = float(total_result[4]) / (total_result[6]+0.000001)             
        WER = float(total_result[7])/total_result[8]
        print('Test : %10s Epoch: %3d it: %6d, loss: %.4f CR: %.4f  AR: %4f  delete: %4d, replace: %4d, insert: %4d, len : %4d, recall: %.4f, precision: %.4f correct: %4d, len: %4d, pre_len: %4d, WER: %.4f, right_word: %4d, total word: %.4f' % 
                    (timeSince(self.start), ep, it, loss_aver, CR, AR, total_result[0], total_result[1], total_result[2], total_result[3], recall, precision, total_result[4], total_result[5], total_result[6],WER, total_result[7], total_result[8])) 

        f = open(self.log_path+'TestAccuracyLoss.log', 'a')
        f.write('%d %f %f %f %f %f %f\n' % (ep, loss_aver, CR, AR, recall, precision, WER))
        f.close();        

    def test_one_epoch_testonly(self):
        self.model.eval()
        ep = 0
        # self.model.batch_norm.train()
        loss_aver = 0
        total_result = [0]*9
        for it, (sample_batched) in enumerate(self.lmdb_test):
            inputs = sample_batched['image'].squeeze(0)
            labels = sample_batched['label'].squeeze(0)

            inputs = Variable(inputs.cuda())
            output = self.model(inputs)
            output = output.transpose(0, 1)
            loss = self.loss_layer(output, labels, inputs)

            prediction, result = self.loss_layer.result_analysis_recall()
            loss = loss.data[0]
            if it == 0:
                loss_aver = loss
            loss_aver = 0.9*loss_aver+0.1*loss      

            for i, ele in enumerate(result):
                total_result[i] += ele 

            if it % 5000 == 0:
                CR = 1-(float)(total_result[0]+total_result[1])/total_result[3]
                AR = 1-(float)(total_result[0]+total_result[1]+total_result[2])/total_result[3] 
                recall = float(total_result[4]) / total_result[5]
                precision = float(total_result[4]) / (total_result[6]+0.000001)                     
                WER = float(total_result[7])/total_result[8]
                print('Test : %10s Epoch: %3d it: %6d, loss: %.4f CR: %.4f  AR: %4f  delete: %4f, replace: %4f, insert: %4f, len : %4d, recall: %.4f, precision: %.4f, WER: %.4f, right_word: %4d, total word: %.4f' % 
                            (timeSince(self.start), ep, it, loss_aver, CR, AR, total_result[0], total_result[1], total_result[2], total_result[3], recall, precision, WER, total_result[7], total_result[8]))   

        CR = 1-(float)(total_result[0]+total_result[1])/total_result[3]
        AR = 1-(float)(total_result[0]+total_result[1]+total_result[2])/total_result[3]     
        recall = float(total_result[4]) / total_result[5]
        precision = float(total_result[4]) / (total_result[6]+0.000001)             
        WER = float(total_result[7])/total_result[8]
        print('Test : %10s Epoch: %3d it: %6d, loss: %.4f CR: %.4f  AR: %4f  delete: %4d, replace: %4d, insert: %4d, len : %4d, recall: %.4f, precision: %.4f correct: %4d, len: %4d, pre_len: %4d, WER: %.4f, right_word: %4d, total word: %.4f' % 
                    (timeSince(self.start), ep, it, loss_aver, CR, AR, total_result[0], total_result[1], total_result[2], total_result[3], recall, precision, total_result[4], total_result[5], total_result[6],WER, total_result[7], total_result[8])) 

        f = open(self.log_path+'OnlyTestAccuracyLoss.log', 'a')
        f.write('%d %f %f %f %f %f %f\n' % (ep, loss_aver, CR, AR, recall, precision, WER))
        f.close();

    def test_one_epoch_testonly_twodataset(self):
        self.model.eval()
        ep = 0
        # self.model.batch_norm.train()
        loss_aver = 0
        total_result = [0]*9
        for it, (sample_batched) in enumerate(self.lmdb_test1):
            inputs = sample_batched['image'].squeeze(0)
            labels = sample_batched['label'].squeeze(0)

            inputs = Variable(inputs.cuda())
            output = self.model(inputs)
            output = output.transpose(0, 1)
            loss = self.loss_layer(output, labels, inputs)

            prediction, result = self.loss_layer.result_analysis_recall()
            loss = loss.data[0]
            if it == 0:
                loss_aver = loss
            loss_aver = 0.9*loss_aver+0.1*loss      

            for i, ele in enumerate(result):
                total_result[i] += ele 

            if it % 5000 == 0:
                CR = 1-(float)(total_result[0]+total_result[1])/total_result[3]
                AR = 1-(float)(total_result[0]+total_result[1]+total_result[2])/total_result[3] 
                recall = float(total_result[4]) / total_result[5]
                precision = float(total_result[4]) / (total_result[6]+0.000001)                     
                WER = float(total_result[7])/total_result[8]
                print('Test : %10s Epoch: %3d it: %6d, loss: %.4f CR: %.4f  AR: %4f  delete: %4f, replace: %4f, insert: %4f, len : %4d, recall: %.4f, precision: %.4f, WER: %.4f, right_word: %4d, total word: %.4f' % 
                            (timeSince(self.start), ep, it, loss_aver, CR, AR, total_result[0], total_result[1], total_result[2], total_result[3], recall, precision, WER, total_result[7], total_result[8]))   

        CR = 1-(float)(total_result[0]+total_result[1])/total_result[3]
        AR = 1-(float)(total_result[0]+total_result[1]+total_result[2])/total_result[3]     
        recall = float(total_result[4]) / total_result[5]
        precision = float(total_result[4]) / (total_result[6]+0.000001)             
        WER = float(total_result[7])/total_result[8]
        print('Test : %10s Epoch: %3d it: %6d, loss: %.4f CR: %.4f  AR: %4f  delete: %4d, replace: %4d, insert: %4d, len : %4d, recall: %.4f, precision: %.4f correct: %4d, len: %4d, pre_len: %4d, WER: %.4f, right_word: %4d, total word: %.4f' % 
                    (timeSince(self.start), ep, it, loss_aver, CR, AR, total_result[0], total_result[1], total_result[2], total_result[3], recall, precision, total_result[4], total_result[5], total_result[6],WER, total_result[7], total_result[8])) 

        f = open(self.log_path+'OnlyTestAccuracyLoss.log', 'a')
        f.write('%d %f %f %f %f %f %f\n' % (ep, loss_aver, CR, AR, recall, precision, WER))
        f.close();        

        ep = 0
        # self.model.batch_norm.train()
        loss_aver = 0
        total_result = [0]*9
        for it, (sample_batched) in enumerate(self.lmdb_test2):
            inputs = sample_batched['image'].squeeze(0)
            labels = sample_batched['label'].squeeze(0)

            inputs = Variable(inputs.cuda())
            output = self.model(inputs)
            output = output.transpose(0, 1)
            loss = self.loss_layer(output, labels, inputs)

            prediction, result = self.loss_layer.result_analysis_recall()
            loss = loss.data[0]
            if it == 0:
                loss_aver = loss
            loss_aver = 0.9*loss_aver+0.1*loss      

            for i, ele in enumerate(result):
                total_result[i] += ele 

            if it % 5000 == 0:
                CR = 1-(float)(total_result[0]+total_result[1])/total_result[3]
                AR = 1-(float)(total_result[0]+total_result[1]+total_result[2])/total_result[3] 
                recall = float(total_result[4]) / total_result[5]
                precision = float(total_result[4]) / (total_result[6]+0.000001)                     
                WER = float(total_result[7])/total_result[8]
                print('Test : %10s Epoch: %3d it: %6d, loss: %.4f CR: %.4f  AR: %4f  delete: %4f, replace: %4f, insert: %4f, len : %4d, recall: %.4f, precision: %.4f, WER: %.4f, right_word: %4d, total word: %.4f' % 
                            (timeSince(self.start), ep, it, loss_aver, CR, AR, total_result[0], total_result[1], total_result[2], total_result[3], recall, precision, WER, total_result[7], total_result[8]))   

        CR = 1-(float)(total_result[0]+total_result[1])/total_result[3]
        AR = 1-(float)(total_result[0]+total_result[1]+total_result[2])/total_result[3]     
        recall = float(total_result[4]) / total_result[5]
        precision = float(total_result[4]) / (total_result[6]+0.000001)             
        WER = float(total_result[7])/total_result[8]
        print('Test : %10s Epoch: %3d it: %6d, loss: %.4f CR: %.4f  AR: %4f  delete: %4d, replace: %4d, insert: %4d, len : %4d, recall: %.4f, precision: %.4f correct: %4d, len: %4d, pre_len: %4d, WER: %.4f, right_word: %4d, total word: %.4f' % 
                    (timeSince(self.start), ep, it, loss_aver, CR, AR, total_result[0], total_result[1], total_result[2], total_result[3], recall, precision, total_result[4], total_result[5], total_result[6],WER, total_result[7], total_result[8])) 

        f = open(self.log_path+'OnlyTestAccuracyLoss.log', 'a')
        f.write('%d %f %f %f %f %f %f\n' % (ep, loss_aver, CR, AR, recall, precision, WER))
        f.close();           