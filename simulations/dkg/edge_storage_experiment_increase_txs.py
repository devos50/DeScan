from asyncio import ensure_future
from multiprocessing.context import Process

from simulations.dkg import create_aggregate_result_files
from simulations.dkg.dkg_simulation import DKGSimulation
from simulations.dkg.settings import DKGSimulationSettings

NUM_PEERS = 1600
EXP_NAME = "storage"


def run(settings):
    simulation = DKGSimulation(settings)
    simulation.MAIN_OVERLAY = "DKGCommunity"
    ensure_future(simulation.run())
    simulation.loop.run_forever()


if __name__ == "__main__":
    create_aggregate_result_files(EXP_NAME)

    for batch in [(0, 1, 2, 3, 4), (5, 6, 7, 8, 9)]:
        processes = []
        for exp_num in batch:
            print("Running experiment with %d peers (num: %d)..." % (NUM_PEERS, exp_num))
            settings = DKGSimulationSettings()
            settings.peers = NUM_PEERS
            settings.name = EXP_NAME
            settings.offline_fraction = 0
            settings.malicious_fraction = 0
            settings.replication_factor = 1
            settings.duration = 3600
            settings.nb_size = 1
            settings.identifier = "%d" % exp_num
            settings.fast_data_injection = True
            settings.num_searches = 0
            settings.skip_graphs = 1
            settings.logging_level = "ERROR"
            settings.track_storage_interval = 1000000
            settings.data_file_name = "scripts/blocks.json"
            settings.enable_community_statistics = True
            settings.enable_ipv8_ticker = False

            p = Process(target=run, args=(settings,))
            p.start()
            processes.append(p)

        for p in processes:
            p.join()
