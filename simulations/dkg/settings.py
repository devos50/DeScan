from dataclasses import dataclass
from enum import Enum
from typing import Optional

from simulations.skipgraph.settings import SkipGraphSimulationSettings


class Dataset(Enum):
    TRIBLER = 0
    ETHEREUM = 1


@dataclass
class DKGSimulationSettings(SkipGraphSimulationSettings):
    replication_factor: int = 2
    data_file_name: str = "torrents_1000.txt"
    fast_data_injection: bool = False  # Whether we sidestep the content injection
    dataset = Dataset.TRIBLER
    max_eth_blocks: Optional[int] = None
