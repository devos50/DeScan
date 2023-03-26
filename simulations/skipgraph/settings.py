from dataclasses import dataclass

from simulations.settings import SimulationSettings


@dataclass
class SkipGraphSimulationSettings(SimulationSettings):
    """
    Settings related to simulations with the Skip Graph overlay.
    """

    # The number of Skip Graphs we should maintain.
    skip_graphs: int = 1

    # The total number of searches initiated during the simulation.
    num_searches: int = 1000

    # The number of left/right neighbours each peer will maintain in the Skip Graph routing table.
    nb_size: int = 1

    # The fraction of peers that are offline during the simulation. Note that these offline peers will join the Skip
    # Graph first, but they will be unresponsive during content retrieval. This is an integer number ranging from 0-100.
    offline_fraction: int = 0

    # The fraction of peers that we consider as being malicious. This is an integer number ranging from 0-100.
    malicious_fraction: int = 0

    # Whether we assign sequential keys to nodes in the Skip Graphs. If set to True, it will assign an incrementing
    # integer value to each node as key. This makes debugging and testing easier.
    assign_sequential_sg_keys: bool = False

    # If set to True, the key distribution of peers will be evenly spaced, equalizing storage requirements. If set to
    # False, keys will be assigned randomly.
    fix_sg_key_distribution: bool = False
