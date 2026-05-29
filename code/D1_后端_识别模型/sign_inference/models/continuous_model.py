"""连续手语 ctcn 模型结构（与 sign_app/CNN_LSTM.py 一致）"""
import torch
import torch.nn as nn
from torchvision import models


class FeatureExtractor(nn.Module):
    def __init__(self, model_name="resnet18"):
        super().__init__()
        if model_name == "resnet18":
            original = models.resnet18(weights=models.ResNet18_Weights.IMAGENET1K_V1)
            self.feature_dim = 512
        else:
            raise ValueError(model_name)
        self.feature_layers = nn.Sequential(
            original.conv1,
            original.bn1,
            original.relu,
            original.maxpool,
            original.layer1,
            original.layer2,
            original.layer3,
            original.layer4,
            original.avgpool,
        )
        for p in self.parameters():
            p.requires_grad = False

    def forward(self, x):
        return torch.flatten(self.feature_layers(x), 1)


class MultiHeadAttention(nn.Module):
    def __init__(self, embed_size, heads):
        super().__init__()
        self.embed_size = embed_size
        self.heads = heads
        self.head_dim = embed_size // heads
        self.values = nn.Linear(self.head_dim, self.head_dim, bias=False)
        self.keys = nn.Linear(self.head_dim, self.head_dim, bias=False)
        self.queries = nn.Linear(self.head_dim, self.head_dim, bias=False)
        self.fc_out = nn.Linear(heads * self.head_dim, embed_size)

    def forward(self, values, keys, query):
        n = query.shape[0]
        vl, kl, ql = values.shape[1], keys.shape[1], query.shape[1]
        values = values.reshape(n, vl, self.heads, self.head_dim)
        keys = keys.reshape(n, kl, self.heads, self.head_dim)
        queries = query.reshape(n, ql, self.heads, self.head_dim)
        values = self.values(values)
        keys = self.keys(keys)
        queries = self.queries(queries)
        energy = torch.einsum("nqhd,nkhd->nhqk", [queries, keys])
        attention = torch.softmax(energy / (self.embed_size ** 0.5), dim=3)
        out = torch.einsum("nhql,nlhd->nqhd", [attention, values]).reshape(
            n, ql, self.heads * self.head_dim
        )
        return self.fc_out(out)


class MultiModalCNNTransformerModel(nn.Module):
    def __init__(self, feature_dim=638, num_classes=100, transformer_layers=3, heads=8, dropout=0.5):
        super().__init__()
        self.transformer = nn.TransformerEncoder(
            nn.TransformerEncoderLayer(d_model=feature_dim, nhead=heads, dropout=dropout),
            num_layers=transformer_layers,
        )
        self.attention = MultiHeadAttention(feature_dim, heads)
        self.classifier = nn.Sequential(
            nn.Linear(feature_dim, 128),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(128, num_classes),
        )

    def forward(self, x, lengths=None):
        if lengths is not None:
            x = x[:, : lengths.max().item(), :]
        out = self.transformer(x.permute(1, 0, 2))
        attn_out = self.attention(out.permute(1, 0, 2), out.permute(1, 0, 2), out.permute(1, 0, 2))
        return self.classifier(attn_out[:, -1, :])
