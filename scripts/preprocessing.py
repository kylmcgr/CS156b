import torch
import pandas as pd
import numpy as np
from torch import nn
from PIL import Image
from torch import optim
import matplotlib.pyplot as plt
import torch.nn.functional as F
from torch.autograd import Variable
from torchvision import datasets, transforms, models
import torch.nn as nn
from torch.utils.data import Dataset, TensorDataset, DataLoader
import cv2
import skimage.io
import skimage.color
import skimage.filters
from sklearn import preprocessing
import sys

def preprocessing_complex(image):
	new_image = image.resize((320, 320))
	new_image = np.float32(new_image)
	bilateral = cv2.bilateralFilter(new_image, 5, 50, 50)
	block_size =75
	local_thresh = skimage.filters.threshold_local(new_image, block_size, offset=5)
	binary_local = new_image > local_thresh
	gaussHist = skimage.exposure.equalize_hist(new_image)
	max = 0
	min = new_image[0,0]
	for i in range(new_image.shape[0]):
	    for j in range(new_image.shape[1]):
	        if new_image[i,j] > max:
	            max = new_image[i,j]
	        if new_image[i,j] < min:
	            min = new_image[i,j]
	t = min + 0.9 * (max-min)
	binary_mask = new_image < t
	area_closed = skimage.morphology.area_closing(binary_mask,area_threshold = 128)
	total_img = np.stack([gaussHist,binary_local,bilateral],axis=-1)
	selection = total_img.copy()
	selection[~area_closed] = 0
	return selection
	
def preprocessing_simple(image):
	new_image = image.resize((320, 320))
	new_image = np.float32(new_image)
	bilateral = cv2.bilateralFilter(new_image, 5, 50, 50)
	blurred_image = skimage.filters.gaussian(bilateral, sigma=1.0)
	max = 0
	min = blurred_image[0,0]
	for i in range(blurred_image.shape[0]):
	    for j in range(blurred_image.shape[1]):
	        if blurred_image[i,j] > max:
	            max = blurred_image[i,j]
	        if blurred_image[i,j] < min:
	            min = blurred_image[i,j]
	t = min + 0.9 * (max-min)
	binary_mask = blurred_image < t
	area_closed = skimage.morphology.area_closing(binary_mask,area_threshold = 128)
	selection = blurred_image.copy()
	selection[~area_closed] = 0
	return selection
	
def load_traindata(processing, classes, naVal, split_i, split_len, fillna=True, resizex=320, resizey=320):
    traindf = pd.read_csv("/groups/CS156b/data/student_labels/train.csv")
    N = traindf.shape[0]
    # split = [0,10] if split_len = 15,000
    beg = split_i * split_len
    end = (split_i + 1) * split_len
    classesdf = traindf[classes].fillna(naVal).iloc[beg:end]
    paths = traindf["Path"].iloc[beg:end].tolist()  
    if processing == "simple":
        Xdf = np.array([preprocessing_simple(Image.open("/groups/CS156b/data/"+path)) for path in paths])
    elif processing == "complex":
        Xdf = np.array([preprocessing_complex(Image.open("/groups/CS156b/data/"+path)) for path in paths])
    else:
        Xdf = np.array([np.asarray(Image.open("/groups/CS156b/data/"+path).resize((resizex, resizey))) for path in paths])
    return Xdf, classesdf
    
def get_dataLoader(Xdf, classesdf, processing, resizex=320, resizey=320):
    num_channels = 1
    if processing == "complex":
        num_channels = 3
    X_train = torch.from_numpy(Xdf.reshape((-1, num_channels, resizex, resizey)).astype('float32'))
    return X_train
    
def load_testdata(processing, resizex=320, resizey=320, numtest=10):
    testdf = pd.read_csv("/groups/CS156b/data/student_labels/solution_ids.csv")
    testpaths = testdf["Path"].tolist()
    # if partial_data:
    #     testpaths = testdf["Path"].iloc[:numtest].tolist()
    if processing == "simple":
        Xtestdf = np.array([preprocessing_simple(Image.open("/groups/CS156b/data/"+path)) for path in testpaths])
        X_test = torch.from_numpy(Xtestdf.reshape((-1, 1, resizex, resizey)).astype('float32'))
    elif processing == "complex":
        Xtestdf = np.array([preprocessing_complex(Image.open("/groups/CS156b/data/"+path)) for path in testpaths])
        X_test = torch.from_numpy(Xtestdf.reshape((-1, 3, resizex, resizey)).astype('float32'))
    else:
        Xtestdf = np.array([np.asarray(Image.open("/groups/CS156b/data/"+path).resize((resizex, resizey))) for path in testpaths])
        X_test = torch.from_numpy(Xtestdf.reshape((-1, 1, resizex, resizey)).astype('float32'))
    return X_test
    
	
if __name__ == "__main__":
    if len(sys.argv) < 6:
        print("Invalid number of arguments")
        sys.exit()
    processing = sys.argv[1] # processing = simple, or complex
    naVal = sys.argv[2] # -1, 0, -0,5
    split_i = int(sys.argv[3]) # [0,10]
    split_len = int(sys.argv[4])
    if sys.argv[5] == "test_only":
        test_only = True
    else:
        test_only = False

    classes = ['No Finding', 'Enlarged Cardiomediastinum', 'Cardiomegaly',
            'Lung Opacity', 'Lung Lesion', 'Edema', 'Consolidation',
            'Pneumonia', 'Atelectasis', 'Pneumothorax', 'Pleural Effusion',
            'Pleural Other', 'Fracture', 'Support Devices']
            
    filename = "/groups/CS156b/2022/team_dirs/DJJ/processed_train_data_"+processing+"_naVal="+naVal+"_split="+sys.argv[3]+"_size="+sys.argv[4]+".pt"
    batch_size = 64
    
    device = torch.device("cuda:0")
    if not test_only:
        Xdf, classesdf = load_traindata(processing, classes, naVal, split_i, split_len)
        X_train = get_dataLoader(Xdf, classesdf, processing)
        torch.save(X_train, filename)
    else:
        X_test = load_testdata(processing)
        filename = "/groups/CS156b/2022/team_dirs/DJJ/processed_solution_data_"+processing+".pt"
        torch.save(X_test, filename)