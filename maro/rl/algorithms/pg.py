# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import numpy as np
import torch

from maro.rl.algorithms.abs_algorithm import AbsAlgorithm
from maro.rl.models.learning_model import LearningModel

from .utils import expand_dim, preprocess, to_device


class PolicyGradientConfig:
    """Configuration for the Policy Gradient (PG) algorithm.

    Args:
        num_actions (int): Number of possible actions.
        reward_decay (float): Reward decay as defined in standard RL terminology.
    """
    __slots__ = ["num_actions", "reward_decay"]

    def __init__(self, num_actions: int, reward_decay: float):
        self.num_actions = num_actions
        self.reward_decay = reward_decay


class PolicyGradient(AbsAlgorithm):
    """Policy Gradient (PG) algorithm.

    The Policy Gradient algorithm base on the policy gradient theorem, a.k.a. REINFORCE.

    Args:
        model (LearningModel): Policy model.
        config: Configuration for the PG algorithm.
    """
    @to_device
    def __init__(self, model: LearningModel, config: PolicyGradientConfig):
        super().__init__(model, config)
        self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._model.to(self._device)

    @expand_dim
    def choose_action(self, state: np.ndarray):
        action_distribution = self._model(state, is_training=False)  # (num_actions,)
        return np.random.choice(self._config.num_actions, p=action_distribution)

    @preprocess
    def train(self, states: np.ndarray, actions: np.ndarray, returns: np.ndarray):
        action_distributions = self._model(states)
        action_prob = action_distributions.gather(1, actions.unsqueeze(1)).squeeze()   # (N, 1)
        loss = -(torch.log(action_prob) * returns).mean()
        self._model.step(loss)
