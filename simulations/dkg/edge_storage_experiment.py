from asyncio import ensure_future
from multiprocessing.context import Process

from simulations.dkg import create_aggregate_result_files
from simulations.dkg.dkg_simulation import DKGSimulation
from simulations.dkg.settings import DKGSimulationSettings, Dataset

PEERS = [100, 200, 400, 800, 1600, 3200, 6400, 12800]
EXPERIMENT_REPLICATION = 5
EXP_NAME = "storage"


def run(settings):
    simulation = DKGSimulation(settings)
    simulation.MAIN_OVERLAY = "DKGCommunity"
    ensure_future(simulation.run())
    simulation.loop.run_forever()


if __name__ == "__main__":
    create_aggregate_result_files(EXP_NAME)

    for num_peers in PEERS:
        processes = []
        for fix_sg_key_distribution in [True, False]:
            for exp_num in range(EXPERIMENT_REPLICATION):
                print("Running experiment with %d peers (num: %d)..." % (num_peers, exp_num))
                settings = DKGSimulationSettings()
                settings.peers = num_peers
                settings.name = EXP_NAME
                settings.offline_fraction = 0
                settings.malicious_fraction = 0
                settings.replication_factor = 5
                settings.duration = 3600
                settings.nb_size = 1
                settings.fast_data_injection = True
                settings.num_searches = 0
                settings.skip_graphs = 1
                settings.fix_sg_key_distribution = fix_sg_key_distribution
                settings.identifier = "%d_%s" % (exp_num, "fixed" if fix_sg_key_distribution else "random")
                settings.logging_level = "ERROR"
                settings.enable_community_statistics = True
                settings.enable_ipv8_ticker = False

                p = Process(target=run, args=(settings,))
                p.start()
                processes.append(p)

        for p in processes:
            p.join()
