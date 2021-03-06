import math

import torch
from torch.nn import Module, Parameter


# implementation of additive margin softmax loss in https://arxiv.org/abs/1801.05599

def l2_norm(input_tensor, axis=1):
    norm = torch.norm(input_tensor, 2, axis, True)
    output = torch.div(input_tensor, norm)
    return output


class ArcfaceLoss(Module):

    def __init__(self, embedding_size=512, class_num=51332, s=64., m=0.5):
        super(ArcfaceLoss, self).__init__()
        self.class_num = class_num
        self.kernel = Parameter(torch.Tensor(embedding_size, class_num)).cuda()

        # initial kernel
        self.kernel.data.uniform_(-1, 1).renorm_(2, 1, 1e-5).mul_(1e5)

        # the margin value, default is 0.5
        self.m = m

        # the scale value default is 64, see https://arxiv.org/abs/1704.06369
        self.s = s
        self.cos_m = math.cos(m)
        self.sin_m = math.sin(m)

        #
        self.mm = self.sin_m * m  # issue 1
        self.threshold = math.cos(math.pi - m)

    def forward(self, embbedings, label):
        # feat_norm
        # add by anxiang
        embbedings = l2_norm(embbedings, axis=1)

        # weights norm
        nB = len(embbedings)
        kernel_norm = l2_norm(self.kernel, axis=0)

        # get cos(theta)
        cos_theta = torch.mm(embbedings, kernel_norm)

        # for numerical stability
        cos_theta = cos_theta.clamp(-1, 1)

        # get sin_theta
        cos_theta_2 = torch.pow(cos_theta, 2)
        sin_theta_2 = 1 - cos_theta_2
        sin_theta = torch.sqrt(sin_theta_2)

        # cos(theta + m) = cos(theta)cos(m) - sin(theta)sin(m)
        cos_theta_m = (cos_theta * self.cos_m - sin_theta * self.sin_m)

        # this condition controls the theta + m should in range [0, pi]
        #                            #
        #  0  <= theta + m <= pi     #
        #  -m <= theta     <= pi-m   #
        #                            #
        cond_v = cos_theta - self.threshold
        cond_mask = cond_v <= 0

        # when theta not in [0,pi], use cos-face instead
        keep_val = (cos_theta - self.mm)
        cos_theta_m[cond_mask] = keep_val[cond_mask]

        # a little bit hacky way to prevent in_place operation on cos_theta
        output = cos_theta * 1.0
        idx_ = torch.arange(0, nB, dtype=torch.long)
        output[idx_, label] = cos_theta_m[idx_, label]

        # scale up in order to make softmax work, first introduced in normface
        output *= self.s
        return output
