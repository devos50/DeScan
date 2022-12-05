from asyncio import ensure_future
from multiprocessing.context import Process

from simulations.dkg import create_aggregate_result_files
from simulations.dkg.dkg_simulation import DKGSimulation
from simulations.dkg.settings import DKGSimulationSettings, Dataset

PEERS = [800, 1600, 3200, 6400, 12800]
EXPERIMENT_REPLICATION = 1
EXP_NAME = "network_usage"


def run(settings):
    simulation = DKGSimulation(settings)
    simulation.MAIN_OVERLAY = "DKGCommunity"
    ensure_future(simulation.run())
    simulation.loop.run_forever()


if __name__ == "__main__":
    create_aggregate_result_files(EXP_NAME)

    for num_peers in PEERS:
        processes = []
        for exp_num in range(EXPERIMENT_REPLICATION):
            print("Running experiment with %d peers (num: %d)..." % (num_peers, exp_num))
            settings = DKGSimulationSettings()
            settings.peers = num_peers
            settings.name = EXP_NAME
            settings.offline_fraction = 0
            settings.malicious_fraction = 0
            settings.replication_factor = 5
            settings.duration = 3600
            settings.nb_size = 5
            settings.fast_data_injection = True
            settings.dataset = Dataset.ETHEREUM
            settings.num_searches = 10000
            settings.max_eth_blocks = None
            settings.skip_graphs = 5
            settings.data_file_name = "blocks.json"
            settings.identifier = "%d" % exp_num
            settings.logging_level = "ERROR"
            settings.enable_community_statistics = True
            settings.enable_ipv8_ticker = False

            p = Process(target=run, args=(settings,))
            p.start()
            processes.append(p)

        for p in processes:
            p.join()
