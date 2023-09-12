from collections import OrderedDict
import warnings
import flwr as fl
import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision.transforms import Compose, ToTensor, Normalize
from torch.utils.data import DataLoader
from torchvision.datasets import CIFAR10
import pandas as pd
from scipy.io import arff
from pandas import DataFrame
from sklearn.model_selection import train_test_split
import numpy as np
RANDOM_SEED = 42

# #############################################################################
# Regular PyTorch pipeline: nn.Module, train, test, and DataLoader
# #############################################################################

warnings.filterwarnings("ignore", category=UserWarning)
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

class Encoder(nn.Module):

  def __init__(self, seq_len, n_features, embedding_dim=64):
    super(Encoder, self).__init__()

    self.seq_len, self.n_features = seq_len, n_features
    self.embedding_dim, self.hidden_dim = embedding_dim, 2 * embedding_dim

    self.rnn1 = nn.LSTM(
      input_size=n_features,
      hidden_size=self.hidden_dim,
      num_layers=1,
      batch_first=True
    )

    self.rnn2 = nn.LSTM(
      input_size=self.hidden_dim,
      hidden_size=embedding_dim,
      num_layers=1,
      batch_first=True
    )

  def forward(self, x):
    x = x.reshape((1, self.seq_len, self.n_features))

    x, (_, _) = self.rnn1(x)
    x, (hidden_n, _) = self.rnn2(x)

    return hidden_n.reshape((self.n_features, self.embedding_dim))

class Decoder(nn.Module):

  def __init__(self, seq_len, input_dim=64, n_features=1):
    super(Decoder, self).__init__()

    self.seq_len, self.input_dim = seq_len, input_dim
    self.hidden_dim, self.n_features = 2 * input_dim, n_features

    self.rnn1 = nn.LSTM(
      input_size=input_dim,
      hidden_size=input_dim,
      num_layers=1,
      batch_first=True
    )

    self.rnn2 = nn.LSTM(
      input_size=input_dim,
      hidden_size=self.hidden_dim,
      num_layers=1,
      batch_first=True
    )

    self.output_layer = nn.Linear(self.hidden_dim, n_features)

  def forward(self, x):
    x = x.repeat(self.seq_len, self.n_features)
    x = x.reshape((self.n_features, self.seq_len, self.input_dim))

    x, (hidden_n, cell_n) = self.rnn1(x)
    x, (hidden_n, cell_n) = self.rnn2(x)
    x = x.reshape((self.seq_len, self.hidden_dim))

    return self.output_layer(x)

class RecurrentAutoencoder(nn.Module):

  def __init__(self, seq_len, n_features, embedding_dim=64):
    super(RecurrentAutoencoder, self).__init__()

    self.encoder = Encoder(seq_len, n_features, embedding_dim).to(device)
    self.decoder = Decoder(seq_len, embedding_dim, n_features).to(device)

  def forward(self, x):
    x = self.encoder(x)
    x = self.decoder(x)

    return x

def train_model(model, train_dataset, val_dataset, n_epochs):
  optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
  criterion = nn.L1Loss(reduction='sum').to(device)
  history = dict(train=[], val=[])

  best_model_wts = copy.deepcopy(model.state_dict())
  best_loss = 10000.0

  for epoch in range(1, n_epochs + 1):
    model = model.train()

    train_losses = []
    for seq_true in train_dataset:
      optimizer.zero_grad()

      seq_true = seq_true.to(device)
      seq_pred = model(seq_true)

      loss = criterion(seq_pred, seq_true)

      loss.backward()
      optimizer.step()

      train_losses.append(loss.item())

    val_losses = []
    model = model.eval()
    with torch.no_grad():
      for seq_true in val_dataset:

        seq_true = seq_true.to(device)
        seq_pred = model(seq_true)

        loss = criterion(seq_pred, seq_true)
        val_losses.append(loss.item())

    train_loss = np.mean(train_losses)
    val_loss = np.mean(val_losses)

    history['train'].append(train_loss)
    history['val'].append(val_loss)

    if val_loss < best_loss:
      best_loss = val_loss
      best_model_wts = copy.deepcopy(model.state_dict())

    print(f'Epoch {epoch}: train loss {train_loss} val loss {val_loss}')

  model.load_state_dict(best_model_wts)
  return model.eval(), history


def create_dataset(df):
    sequences = df.astype(np.float32).to_numpy().tolist()
    dataset = [torch.tensor(s).unsqueeze(1).float() for s in sequences]
    n_seq, seq_len, n_features = torch.stack(dataset).shape
    return dataset, seq_len, n_features

# #############################################################################
# Federating the pipeline with Flower
# #############################################################################

#Preprocess datas
def load(arff_file,decode_str=True):
    data, meta = arff.loadarff(arff_file)
    df = DataFrame(data,columns = meta.names())
    if decode_str:
        df_str = df.select_dtypes(include=['object'])
        if not df_str.empty:
            df[df_str.columns] = df_str.applymap(lambda x:x.decode('utf-8'))
    return df

def preprocess():
    print("Preprocessing .....")
    with open('ECG5000/ECG5000_TRAIN.arff') as f:
      train = load(f)

    with open('ECG5000/ECG5000_TEST.arff') as f:
      test = load(f)

    df = pd.concat([train, test], ignore_index=True)
    df = df.sample(frac=1.0)
    print(df.shape)

    CLASS_NORMAL = 1
    class_names = ['Normal', 'R on T', 'PVC', 'SP', 'UB']
    new_columns = list(df.columns)
    new_columns[-1] = 'target'
    df.columns = new_columns

    #Setting algo
    normal_df = df[df.target == str(CLASS_NORMAL)].drop(labels='target', axis=1)
    anomaly_df = df[df.target != str(CLASS_NORMAL)].drop(labels='target', axis=1)

    train_df, val_df = train_test_split(
        normal_df,
        test_size=0.15,
        random_state=RANDOM_SEED
    )

    val_df, test_df = train_test_split(
        val_df,
        test_size=0.33,
        random_state=RANDOM_SEED
    )
    return train_df, val_df

train_df , val_df = preprocess()
trainloader, seq_len, n_features = create_dataset(train_df)
valloader, _, _ = create_dataset(val_df)

RecurrentAutoencoder = RecurrentAutoencoder(seq_len, n_features, 128)
RecurrentAutoencoder =  RecurrentAutoencoder.to(device)

# Define Flower client
class FlowerClient(fl.client.NumPyClient):
  def get_parameters(self, config):
    return [val.cpu().numpy() for _, val in RecurrentAutoencoder.state_dict().items()]

  def set_parameters(self, parameters):
    params_dict = zip(RecurrentAutoencoder.state_dict().keys(), parameters)
    state_dict = OrderedDict({k: torch.tensor(v) for k, v in params_dict})
    RecurrentAutoencoder.load_state_dict(state_dict, strict=True)

  def fit(self, parameters, config):
    self.set_parameters(parameters)
    train_model(RecurrentAutoencoder, trainloader,valloader, epochs=1)
    return self.get_parameters(config={}), len(trainloader.dataset), {}

#   def evaluate(self, parameters, config):
#     self.set_parameters(parameters)
#     #loss, accuracy = test(RecurrentAutoencoder, valloader)
#     return float(loss), len(valloader.dataset), {"accuracy": float(accuracy)}

# Start Flower client
fl.client.start_numpy_client(server_address="195.83.169.139:8080", client=FlowerClient())

