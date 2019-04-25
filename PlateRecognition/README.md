### **车牌识别训练代码说明文档**

**环境及依赖：**

建议使用Anaconda构建虚拟环境 : 详见https://www.anaconda.com/

python : 2.7

pytorch : 0.4.0 

opencv : 3.4.3

Augment : 详见https://github.com/Canjie-Luo/Scene-Text-Image-Transformer

warpctc_pytorch : 详见https://github.com/SeanNaren/warp-ctc

**为了节省空间，删除了训练集4000张图片以及对应的label（即train-data文件夹）**

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
  
