from dataclasses import dataclass

from simulations.settings import SimulationSettings


@dataclass
class SkipGraphSimulationSettings(SimulationSettings):
    skip_graphs: int = 1
    num_searches: int = 1000
    nb_size: int = 1
    offline_fraction: int = 0
    malicious_fraction: int = 0
    track_failing_nodes_in_rts: bool = False
    assign_sequential_sg_keys: bool = False
    fix_sg_key_distribution: bool = False
