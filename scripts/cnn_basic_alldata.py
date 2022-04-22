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

prefix = "/groups/CS156b/data/"
classes = ['No Finding', 'Enlarged Cardiomediastinum', 'Cardiomegaly',
            'Lung Opacity', 'Lung Lesion', 'Edema', 'Consolidation',
            'Pneumonia', 'Atelectasis', 'Pneumothorax', 'Pleural Effusion',
            'Pleural Other', 'Fracture', 'Support Devices']

imagex = 50
imagey = 50
batch_size = 256
n_epochs = 10

train = "/groups/CS156b/data/student_labels/train.csv"
traindf = pd.read_csv(train)

# nans as -1
classesdf = traindf[classes].fillna(-1)

paths = traindf["Path"].tolist()

# most seem to be 2320, 2828, but smaller for now
Xdf = np.array([np.asarray(Image.open(prefix+path).resize((imagex, imagey))) for path in paths if path[:5] == 'train']])
X_train = torch.from_numpy(Xdf.reshape((-1, 1, imagex, imagey)).astype('float32'))

y_train = torch.from_numpy((classesdf+1).to_numpy().astype('float32'))
train_dataset = TensorDataset(X_train, y_train)
training_data_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=False)

device = torch.device("cuda:0")

model = nn.Sequential(
    nn.Conv2d(1, 8, kernel_size=(3,3)),
    nn.ReLU(),
    nn.MaxPool2d(2),
    nn.Dropout(p=0.5),

    nn.Conv2d(8, 8, kernel_size=(3,3)),
    nn.ReLU(),
    nn.MaxPool2d(2),
    nn.Dropout(p=0.5),

    nn.Flatten(),
    nn.Linear(968, 64),
    nn.ReLU(),
    nn.Linear(64, 14)
    # PyTorch implementation of cross-entropy loss includes softmax layer
)

criterion = nn.MSELoss()
optimizer = optim.RMSprop(model.parameters())

# store metrics
training_loss_history = np.zeros([n_epochs, 1])

for epoch in range(n_epochs):
    print(f'Epoch {epoch+1}/{n_epoch}:', end='')
    # train
    model.train()
    for i, data in enumerate(training_data_loader):
        images, labels = data
        inputs, labels = inputs.to(device), labels.to(device)
        optimizer.zero_grad()
        # forward pass
        output = model(images)
        # calculate categorical cross entropy loss
        loss = criterion(output, labels)
        # backward pass
        loss.backward()
        optimizer.step()
        # track training loss
        training_loss_history[epoch] += loss.item()
        break;
        # progress update after 180 batches (~1/10 epoch for batch size 32)
        if i % 180 == 0: print('.',end='')
    training_loss_history[epoch] /= len(training_data_loader)
    print(f'\n\tloss: {training_loss_history[epoch,0]:0.4f}',end='')


test = "/groups/CS156b/data/student_labels/test_ids.csv"
testdf = pd.read_csv(test)

testpaths = testdf["Path"].tolist()
Xtestdf = np.array([np.asarray(Image.open(prefix+path).resize((imagex, imagey))) for path in testpaths])
X_test = torch.from_numpy(Xtestdf.reshape((-1, 1, imagex, imagey)).astype('float32'))

test_dataset = TensorDataset(X_test)
test_data_loader = DataLoader(test_dataset, batch_size=1, shuffle=False)

out = []
with torch.no_grad():
    model.eval()
    for i, data in enumerate(test_data_loader):
        data = data.to(device)
        images = data[0]
        # forward pass
        output = model(images)
        # find accuracy
        out.append(output)

out.insert(0, 'Id', testdf['Id'])
out.to_csv("/home/kmcgraw/CS156b/predictions/cnn_basic_1_10test.csv", index=False)
