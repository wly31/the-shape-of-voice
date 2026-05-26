"""孤立手语字母 CNN（与 sign_app/CNNModel.py 一致）"""
from torch.nn import BatchNorm1d, Conv1d, Dropout, Linear, MaxPool1d, Module, ReLU, Sequential


class CNNModel(Module):
    def __init__(self):
        super().__init__()
        self.cnnLayers = Sequential(
            Conv1d(63, 32, 3, 1, 2),
            BatchNorm1d(32),
            ReLU(),
            Conv1d(32, 64, 3, 1, 2),
            BatchNorm1d(64),
            ReLU(),
            MaxPool1d(kernel_size=2, stride=2),
            Conv1d(64, 128, 3, 1, 2),
            BatchNorm1d(128),
            ReLU(),
            Dropout(p=0.3),
            Conv1d(128, 256, 3, 1, 2),
            BatchNorm1d(256),
            ReLU(),
            MaxPool1d(kernel_size=2, stride=2),
            Conv1d(256, 512, 5, 1, 2),
            BatchNorm1d(512),
            ReLU(),
            MaxPool1d(kernel_size=2, stride=2),
            Conv1d(512, 512, 5, 1, 2),
            BatchNorm1d(512),
            ReLU(),
            Dropout(p=0.4),
        )
        self.linearLayers = Sequential(
            Linear(512, 26),
            BatchNorm1d(26),
            ReLU(),
        )

    def forward(self, x):
        x = self.cnnLayers(x)
        x = x.view(x.size(0), -1)
        return self.linearLayers(x)
