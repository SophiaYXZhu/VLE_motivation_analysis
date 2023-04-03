from tqdm import tqdm
from matplotlib import pyplot as plt
import torch
import torch.nn as nn
import torch.nn.functional as F

class FNN(nn.Module):
    def __init__(self, n_classes_in, n_classes_out):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(n_classes_in, 128), 
            nn.ReLU(),
            nn.Linear(128, 256),
            nn.ReLU(),
            nn.Linear(256, n_classes_out), 
            # nn.Softmax()
        )

    def forward(self, X):
        return self.net(X)


class CRNN(nn.Module):
    """
    
    Input:
        X: (n_samples, n_channel, n_length)
        Y: (n_samples)
        
    Output:
        out: (n_samples)
        
    Pararmetes:
        n_classes: number of classes
        
    """

    def __init__(self, in_channels, out_channels, n_len_seg, n_classes, device, verbose=False):
        super(CRNN, self).__init__()
        
        self.n_len_seg = n_len_seg
        self.n_classes = n_classes
        self.in_channels = in_channels
        self.out_channels = out_channels

        self.device = device
        self.verbose = verbose

        # (batch, channels, length)
        self.cnn = nn.Conv1d(in_channels=self.in_channels, 
                            out_channels=self.out_channels, 
                            kernel_size=1, 
                            stride=2)
        # (batch, seq, feature)
        self.rnn = nn.LSTM(input_size=(self.out_channels), 
                            hidden_size=self.out_channels, 
                            num_layers=1, 
                            batch_first=True, 
                            bidirectional=False)
        self.dense = nn.Linear(out_channels, n_classes)
        # self.layer_out = nn.ReLU()
        
    def forward(self, x):

        self.n_channel, self.n_length = x.shape[-2], x.shape[-1]
        assert (self.n_length % self.n_len_seg == 0), "Input n_length should divided by n_len_seg"
        self.n_seg = self.n_length // self.n_len_seg

        out = x
        if self.verbose:
            print(out.shape)

        # (n_samples, n_channel, n_length) -> (n_samples, n_length, n_channel)
        out = out.permute(0,2,1)
        if self.verbose:
            print(out.shape)
        # (n_samples, n_length, n_channel) -> (n_samples*n_seg, n_len_seg, n_channel)
        out = out.view(-1, self.n_len_seg, self.n_channel)
        if self.verbose:
            print(out.shape)
        # (n_samples*n_seg, n_len_seg, n_channel) -> (n_samples*n_seg, n_channel, n_len_seg)
        out = out.permute(0,2,1)
        if self.verbose:
            print(out.shape)
        # cnn
        out = self.cnn(out)
        if self.verbose:
            print(out.shape)
        # global avg, (n_samples*n_seg, out_channels)
        out = out.mean(-1)
        if self.verbose:
            print(out.shape)
        out = out.view(-1, self.n_seg, self.out_channels)
        if self.verbose:
            print(out.shape)
        _, (out, _) = self.rnn(out)
        out = torch.squeeze(out, dim=0)
        if self.verbose:
            print(out.shape)
        out = self.dense(out)
        if self.verbose:
            print(out.shape)
        # out = self.layer_out(out)
        return out