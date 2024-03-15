import logging
import os
import sys
from logging import getLogger
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import torch as th


WALL_COLOR = 0.25


def safe_max(arr):
    """
    Compute the mean of an array if there is at least one element.
    For empty array, return NaN. It is used for logging only.

    :param arr:
    :return:
    """
    return np.nan if len(arr) == 0 else np.max(arr)


def safe_min(arr):
    """
    Compute the mean of an array if there is at least one element.
    For empty array, return NaN. It is used for logging only.

    :param arr:
    :return:
    """
    return np.nan if len(arr) == 0 else np.min(arr)


def myformat(tensor):
    s = str(tensor)
    s = "".join(s.split())
    return s


def create_loggers(folder, names):
    # folderpath = os.path.join(os.path.dirname(__file__), timestamp)
    Path(folder).mkdir(parents=True, exist_ok=True)
    for name in names:
        logger_file = os.path.join(folder, f"{name}.log")
        logf = open(logger_file, "w")
        init_logger(verbose=3, name=name, out=logf)
        # initial_log(name, args)
        if "raw" not in name:
            init_logger(verbose=3, name=name)


def init_logger(verbose=None, name="policy_gradient", out=None):
    """Initialize default logger.

    :param verbose: verbosity level (0: WARNING, 1: INFO, 2: DEBUG)
    :type verbose: int
    :param name: name of the logger (default: policy_gradient)
    :type name: str
    :return: result of ``logging.getLogger(name)``
    :rtype: logging.Logger
    """
    if out is None:
        out = sys.stdout
    logger = logging.getLogger(name)
    ch = logging.StreamHandler(out)
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s", datefmt="%Y/%m/%d %H:%M:%S"
    )
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    if not verbose:
        logger.setLevel(logging.WARNING)
    elif verbose == 1:
        logger.setLevel(logging.INFO)
        logger.info("Output level: INFO")
    elif verbose == 2:
        logger.setLevel(logging.DEBUG)
        logger.debug("Output level: DEBUG")
    else:
        level = max(1, 12 - verbose)  # between 9 and 1
        logger.setLevel(level)
        logger.log(level, "Output level: %s" % level)


def draw(image):
    plt.axis("off")
    plt.imshow(image, cmap="gray", vmin=-1, vmax=1)
    plt.show()


def initial_log(name, args):
    logger = getLogger(name)
    logger.info(f"Layout:           {args['layout']}")
    logger.info(f"Learning rate:    {args['learning_rate']}")
    logger.info(f"Shield:           {args['shield']}")
    logger.info(f"Object detection: {args['object_detection']}")
    logger.info(f"Reward goal:      {args['reward_goal']}")
    logger.info(f"Reward crash:     {args['reward_crash']}")
    logger.info(f"Reward food:      {args['reward_food']}")
    logger.info(f"Reward time:      {args['reward_time']}")
    logger.info(f"Total timesteps:  {args['total_timesteps']}")
    logger.info(f"Logger:           {args['logger_name']}")
    logger.info(f"Seed:             {args['seed']}")
    logger.info(f"Gamma:            {args['gamma']}")
    logger.info(f"Render_or_not:    {args['render_or_not']}")


# FOR TINYGRID INPUT
def get_ground_wall(ghost_distance, center_color, detect_color, input):
    """
    Computes the ground truth of the presence of ghosts around the agent.

    :param ghost_distance: int representing the detection range of the agent.
    :param center_color: color of the agent
    :param detect_color: color of the ghost
    :param input: tensor representing the pacman grid world
    :return: tensor of {0, 1} representing the presence of grass on up, down, left and right
    """

    input = input["tinygrid"]

    centers = (input == center_color).nonzero()[:, 1:]
    neighbors = th.stack(
        (
            input[th.arange(input.size(0)), centers[:, 0] - 1, centers[:, 1]],
            input[th.arange(input.size(0)), centers[:, 0] + 1, centers[:, 1]],
            input[th.arange(input.size(0)), centers[:, 0], centers[:, 1] - 1],
            input[th.arange(input.size(0)), centers[:, 0], centers[:, 1] + 1],
        ),
        dim=1,
    )
    results = (neighbors == detect_color).float()

    if ghost_distance == 1:
        return results

    padded_input = th.nn.functional.pad(
        input,
        (
            ghost_distance - 1,
            ghost_distance - 1,
            ghost_distance - 1,
            ghost_distance - 1,
        ),
        "constant",
        WALL_COLOR,
    )
    l = th.arange(padded_input.size(0))
    centers = (padded_input == center_color).nonzero()[:, 1:]
    for i in range(2, ghost_distance + 1):
        neighbors = th.stack(
            (
                padded_input[l, centers[:, 0] - i, centers[:, 1]],
                padded_input[l, centers[:, 0] + i, centers[:, 1]],
                padded_input[l, centers[:, 0], centers[:, 1] - i],
                padded_input[l, centers[:, 0], centers[:, 1] + i],
            ),
            dim=1,
        )
        res2 = (neighbors == detect_color).float()
        results = th.logical_or(results, res2).float()

    # check clockwise neighbors, upperleft, upperright, ...
    neighbors = th.stack(
        (
            padded_input[l, centers[:, 0] - 1, centers[:, 1] + 1],
            padded_input[l, centers[:, 0] + 1, centers[:, 1] - 1],
            padded_input[l, centers[:, 0] - 1, centers[:, 1] - 1],
            padded_input[l, centers[:, 0] + 1, centers[:, 1] + 1],
        ),
        dim=1,
    )
    res2 = (neighbors == detect_color).float()
    results = th.logical_or(results, res2).float()
    # check counter clockwise neighbors
    neighbors = th.stack(
        (
            padded_input[l, centers[:, 0] - 1, centers[:, 1] - 1],
            padded_input[l, centers[:, 0] + 1, centers[:, 1] + 1],
            padded_input[l, centers[:, 0] + 1, centers[:, 1] - 1],
            padded_input[l, centers[:, 0] - 1, centers[:, 1] + 1],
        ),
        dim=1,
    )
    res2 = (neighbors == detect_color).float()
    results = th.logical_or(results, res2).float()

    if ghost_distance == 2:
        return results

    # check clockwise neighbors, upperleft, upperright, ...
    up = th.stack(
        (
            padded_input[l, centers[:, 0] - 1, centers[:, 1] - 2],
            padded_input[l, centers[:, 0] - 2, centers[:, 1] - 1],
            padded_input[l, centers[:, 0] - 2, centers[:, 1] + 1],
            padded_input[l, centers[:, 0] - 1, centers[:, 1] + 2],
        ),
        dim=1,
    )
    down = th.stack(
        (
            padded_input[l, centers[:, 0] + 1, centers[:, 1] - 2],
            padded_input[l, centers[:, 0] + 2, centers[:, 1] - 1],
            padded_input[l, centers[:, 0] + 2, centers[:, 1] + 1],
            padded_input[l, centers[:, 0] + 1, centers[:, 1] + 2],
        ),
        dim=1,
    )
    left = th.stack(
        (
            padded_input[l, centers[:, 0] - 2, centers[:, 1] - 1],
            padded_input[l, centers[:, 0] - 1, centers[:, 1] - 2],
            padded_input[l, centers[:, 0] + 1, centers[:, 1] - 2],
            padded_input[l, centers[:, 0] + 2, centers[:, 1] - 1],
        ),
        dim=1,
    )
    right = th.stack(
        (
            padded_input[l, centers[:, 0] - 2, centers[:, 1] + 1],
            padded_input[l, centers[:, 0] - 1, centers[:, 1] + 2],
            padded_input[l, centers[:, 0] + 1, centers[:, 1] + 2],
            padded_input[l, centers[:, 0] + 2, centers[:, 1] + 1],
        ),
        dim=1,
    )
    res2 = th.stack(
        (
            th.any((up == detect_color), dim=1),
            th.any((down == detect_color), dim=1),
            th.any((left == detect_color), dim=1),
            th.any((right == detect_color), dim=1),
        ),
        dim=1,
    ).float()

    results = th.logical_or(results, res2).float()
    if ghost_distance == 3:
        return results


def get_agent_coord(input, agent_color):
    centers = (input == agent_color).nonzero()[:, 1:]
    return int(centers[0][0]), int(centers[0][1])
