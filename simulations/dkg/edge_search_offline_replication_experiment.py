from asyncio import ensure_future
from multiprocessing.context import Process

from simulations.dkg import create_aggregate_result_files
from simulations.dkg.dkg_simulation import DKGSimulation
from simulations.dkg.settings import DKGSimulationSettings, Dataset

PEERS = [1600]
OFFLINE_FRACTIONS = [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50]
MALICIOUS_FRACTIONS = [0]
SKIP_GRAPHS = [3]
REPLICATION_FACTORS = [1, 2, 3, 4, 5]
NB_SIZES = [3]
EXPERIMENT_REPLICATION = 1
EXP_NAME = "offline_replication"


def run(settings):
    simulation = DKGSimulation(settings)
    simulation.MAIN_OVERLAY = "DKGCommunity"
    ensure_future(simulation.run())
    simulation.loop.run_forever()


if __name__ == "__main__":
    create_aggregate_result_files(EXP_NAME)

    for num_peers in PEERS:
        for skip_graphs in SKIP_GRAPHS:
            for replication_factor in REPLICATION_FACTORS:
                processes = []
                for offline_fraction in OFFLINE_FRACTIONS:
                    for malicious_fraction in MALICIOUS_FRACTIONS:
                        for nb_size in NB_SIZES:
                            for exp_num in range(EXPERIMENT_REPLICATION):
                                print("Running experiment with %d peers (num: %d)..." % (num_peers, exp_num))
                                settings = DKGSimulationSettings()
                                settings.peers = num_peers
                                settings.name = EXP_NAME
                                settings.offline_fraction = offline_fraction
                                settings.malicious_fraction = malicious_fraction
                                settings.replication_factor = replication_factor
                                settings.duration = 3600
                                settings.nb_size = nb_size
                                settings.fast_data_injection = True
                                settings.dataset = Dataset.ETHEREUM
                                settings.num_searches = 1000
                                settings.max_eth_blocks = None
                                settings.skip_graphs = skip_graphs
                                settings.data_file_name = "blocks.json"
                                settings.identifier = "%d_%d_%d_%d_%d_%d" % (offline_fraction, malicious_fraction, skip_graphs, replication_factor, exp_num, nb_size)
                                settings.logging_level = "ERROR"
                                settings.enable_community_statistics = True
                                settings.enable_ipv8_ticker = False
                                settings.latencies_file = "data/latencies.txt"

                                p = Process(target=run, args=(settings,))
                                p.start()
                                processes.append(p)

                for p in processes:
                    p.join()
