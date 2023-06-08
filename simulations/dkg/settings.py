from dataclasses import dataclass
from enum import Enum
from typing import Optional

from simulations.skipgraph.settings import SkipGraphSimulationSettings


class Dataset(Enum):
    TRIBLER = 0
    ETHEREUM = 1


@dataclass
class DKGSimulationSettings(SkipGraphSimulationSettings):
    """
    Settings related to simulations with the DKG overlay.
    """

    # The replication factor, e.g., on how many nodes we store a particular content item/transaction.
    replication_factor: int = 2

    # Path to the file containing the main experiment data. This file contains the content items/transactions and
    # will be read at the start of the simulation.
    data_file_name: str = "data/blocks.json"

    # Whether we sidestep the content injection; normally we would have to send out network requests to store content
    # at particular participants but to speed up experiments, we can skip this step by setting this setting to True.
    fast_data_injection: bool = False

    # Which dataset to use for the simulation. We currently support experiment with "Ethereum" and "Tribler" but you
    # can easily add your own datasets. We refer to the README.md in the simulations directory for instructions on how
    # to do so.
    dataset = Dataset.ETHEREUM

    # Used when experimenting with the "Ethereum" dataset. Indicates the number of Ethereum blocks being processed
    # during the simulation.
    max_eth_blocks: Optional[int] = None

    # The transaction interval to track storage costs for different peers. Will be disabled if set to None.
    track_storage_interval: Optional[int] = None
