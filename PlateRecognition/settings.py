# -*- coding: utf-8 -*-
from torch import optim

############################### main model ###############################
exp_name = {
    'exp_name'  :'chepai_reco'
}

scheduler = {
    'scheduler_type': optim.lr_scheduler.MultiStepLR,
    'milestones'    : [16, 24],
    'gamma'         : 0.1,
    'total_epoch'   : 32
}

optimizer = {
    'optim_type'    : optim.SGD,
    'lr'            : 0.1,
    'momentum'      : 0.9,
    'weight_decay'  : 0.0001
}

others = {
    'log_path'  : 'log/' + exp_name['exp_name']
}

model = {
    'mode'          : "Train",
    # 'mode'          : "Test",
    'ngpu'          : [0],
    'loading_epoch' : 0,
}

lmdb = {
    'lmdb_train_path'  : "train",
    'lmdb_train_length': 2000 * 64,
    'batch_size_train': 64, # actually 32
    'lmdb_test_path'  : "test",
    'lmdb_test_length': 0,
    'batch_size_test': 64, # actually 1
}
############################### main model ###############################

################################ network #################################
network_args = {
    'HIDDEN_NUM': 256,
    'CLASS_NUM': 43,
}
################################ network #################################

############################### dataloader ###############################
data_args = {
    'EASY'      : False,
    'AUG'       : True,
    'HEIGHT'    : 48,
    'WIDTH'     : 200,
    'KEEP_RATIO': True,
    'LABEL_LEN' : 25,
    'DATA_PATHHEAD' : "datasets/",
    'AUG_RATIO' : 0.4,
    'BINARY'    : False,
    'TEST_TWODATASET' : False,  # always set False !
    'MORE_AUG'  : True,
    'MORE_AUG_RATIO'  : 0.4,
}
############################### dataloader ###############################

def showsettings(s):
    for key in s.keys():
        print(key , s[key])
    print('')