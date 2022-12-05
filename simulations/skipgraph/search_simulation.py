"""
Simulation that initiates a number of searches in the Skip Graph.
"""
import random
from asyncio import ensure_future

from simulations.skipgraph.settings import SkipGraphSimulationSettings
from simulations.skipgraph.sg_simulation import SkipgraphSimulation


class SearchSkipgraphSimulation(SkipgraphSimulation):

    async def on_ipv8_ready(self) -> None:
        await super().on_ipv8_ready()

        # Reset all statistics (since introduction will also conduct a search)
        for node in self.nodes:
            for skip_graph in self.get_skip_graphs(node):
                skip_graph.search_hops = {}
                skip_graph.search_latencies = []
                node.endpoint.enable_community_statistics(skip_graph.get_prefix(), False)
                node.endpoint.enable_community_statistics(skip_graph.get_prefix(), True)

        malicious_nodes = set()
        if self.settings.malicious_fraction > 0:
            num_malicious: int = int(len(self.nodes) * (self.settings.malicious_fraction / 100))
            print("Making %d nodes malicious..." % num_malicious)
            for node in random.sample(self.nodes, num_malicious):
                for skip_graph in self.get_skip_graphs(node):
                    skip_graph.is_malicious = True
                malicious_nodes.add(node)
                self.online_nodes.remove(node)

        # Schedule some searches
        successful_searches = 0
        print(self.node_keys_sorted)
        for _ in range(self.settings.num_searches):
            results = []
            random_node = random.choice(self.online_nodes)
            for _ in range(1):
                search_target = random.randint(0, self.node_keys_sorted[-1])
                is_correct, res = await self.do_search(0, random_node, search_target)
                results.append(is_correct)

            if any(results):
                successful_searches += 1

            count = 0
            if self.settings.track_failing_nodes_in_rts:
                offline_sg_nodes = [node.overlay.get_my_node() for node in self.offline_nodes]
                for online_node in self.online_nodes:
                    for node_in_rt in online_node.overlay.routing_table.get_all_nodes():
                        if node_in_rt in offline_sg_nodes:
                            count += 1

        print("Searches with incorrect result: %d" % (self.settings.num_searches - successful_searches))


if __name__ == "__main__":
    settings = SkipGraphSimulationSettings()
    settings.name = "search"
    settings.peers = 1600
    settings.duration = 3600
    settings.logging_level = "ERROR"
    settings.profile = False
    settings.nb_size = 2
    settings.skip_graphs = 1
    settings.malicious_fraction = 0
    settings.enable_community_statistics = True
    settings.num_searches = 1000
    settings.enable_ipv8_ticker = False
    settings.latencies_file = "data/latencies.txt"
    settings.track_failing_nodes_in_rts = False
    settings.assign_sequential_sg_keys = True
    settings.identifier = "%d" % settings.nb_size
    simulation = SearchSkipgraphSimulation(settings)

    ensure_future(simulation.run())

    simulation.loop.run_forever()
