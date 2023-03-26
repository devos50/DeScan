from dataclasses import dataclass
from typing import Optional


@dataclass
class SimulationSettings:
    """
    Generic settings related to simulations.
    """

    # The total number of IPv8 peers.
    peers: int = 100

    # The name of the experiment.
    name: str = ""

    # Whether to run the Yappi profiler. This is useful to detect bottlenecks in the code.
    profile: bool = False

    # An optional identifier for the experiment, appended to the working directory name.
    identifier: Optional[str] = None

    # The total duration of the simulation in seconds. Note that this duration is in virtual time, e.g., if set to 120,
    # the experiment will end after 120 virtual seconds.
    duration: int = 120

    # The logging level during the experiment.
    logging_level: str = "INFO"

    # Whether we enable statistics like message sizes and frequencies.
    enable_community_statistics: bool = False

    # Optional CSV file with a latency matrix (space-separated).
    latencies_file: Optional[str] = None

    # The IPv8 ticker is responsible for community walking and discovering other peers, but can significantly limit
    # performance. Setting this option to False cancels the IPv8 ticker, improving performance.
    enable_ipv8_ticker: bool = True
