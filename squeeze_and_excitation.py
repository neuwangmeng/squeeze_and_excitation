
import torch
import torch.nn as nn


class ChannelSELayer(nn.Module):
    """
    Re-implementation of Squeeze-and-Excitation (SE) block described in::
    
    Hu et al., Squeeze-and-Excitation Networks, arXiv:1709.01507
    """

    def __init__(self, num_channels, reduction_ratio=2):
        super(ChannelSELayer, self).__init__()
        num_channels_reduced = num_channels // reduction_ratio
        self.reduction_ratio = reduction_ratio
        self.fc1 = nn.Linear(num_channels, num_channels_reduced, bias=False)
        self.fc2 = nn.Linear(num_channels_reduced, num_channels, bias=False)
        self.relu = nn.ReLU()
        self.sigmoid = nn.Sigmoid()
        

    def forward(self, input_tensor):
        batch_size, num_channels, H, W = input_tensor.size()
        input_rank = len(input_tensor.shape)
        squeeze_tensor = input_tensor.view(batch_size, num_channels, -1).mean(dim=2)

        # channel excitation
        fc_out_1 = self.relu(self.fc1(squeeze_tensor))
        fc_out_2 = self.sigmoid(self.fc2(fc_out_1))


        a, b = squeeze_tensor.size()
        output_tensor = torch.mul(input_tensor, fc_out_2.view(a,b,1,1))
        return output_tensor


class SpatialSELayer(nn.Module):
    """
    Implementation of SE block -- squeezing spatially
    and exciting channel-wise described in::
    Roy et al., Concurrent Spatial and Channel Squeeze & Excitation
    in Fully Convolutional Networks, MICCAI 2018
    Roy et al., Recalibrating Fully Convolutional Networks with Spatial
    and Channel'Squeeze & Excitation'Blocks, IEEE TMI 2018
    """

    def __init__(self, num_channels):
        super(SpatialSELayer, self).__init__()
        self.conv = nn.Conv2d(num_channels, 1, 1)
        self.sigmoid = nn.Sigmoid()

    def forward(self, input_tensor):
        # spatial squeeze
        batch_size,_,a,b = input_tensor.size()
        squeeze_tensor = self.sigmoid(self.conv(input_tensor))
        
        # spatial excitation
        output_tensor = torch.mul(input_tensor, squeeze_tensor.view(batch_size,1,a,b))

        return output_tensor


class ChannelSpatialSELayer(nn.Module):
    """
    Implementation of concurrent spatial and channel
    squeeze & excitation: with Max-out aggregation
    Roy et al., Recalibrating Fully Convolutional Networks with Spatial
    and Channel'Squeeze & Excitation'Blocks, IEEE TMI 2018
    """

    def __init__(self, num_channels, reduction_ratio=2):
        super(ChannelSpatialSELayer, self).__init__()
        self.cSE = ChannelSELayer(num_channels, reduction_ratio)
        self.sSE = SpatialSELayer(num_channels)

    def forward(self, input_tensor):
        output_tensor = torch.max(self.cSE(input_tensor), self.sSE(input_tensor))
        return output_tensor
