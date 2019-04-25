### **车牌识别训练代码&推理代码说明文档**
1. cindy/utils/chepai_data_loader.py 用来读取数据、数据预处理

1. 本项目用到了 data augmentation，使用了开源的 Augment 项目（具体见下文的Github链接）

1. warpctc_pytorch 用来计算损失函数（具体见下文Github链接）

1. inference 文件夹内是线上部署的代码，包含训练好的模型文件以及推理代码文件

1. 为了节省空间，删除了训练集4000张图片以及对应的 label（即train-data文件夹）

    删除前的目录层级如下：

    ```
    datasets
      |smu2.jpg
      |test_data.txt
      |train_data.txt
      |train-data
        |train-data-label.txt
        |train-data
          |2b6b3180b74c55b0.jpg
          |...
    ```    
  
1. 环境及依赖

    建议使用Anaconda构建虚拟环境 : 详见https://www.anaconda.com/
    
    python : 2.7
    
    pytorch : 0.4.0 
    
    opencv : 3.4.3
    
    Augment : 详见https://github.com/Canjie-Luo/Scene-Text-Image-Transformer
    
    warpctc_pytorch : 详见https://github.com/SeanNaren/warp-ctc
    
