"""
Simulation that conducts some churn, e.g., nodes joining and leaving.
"""
import random
from asyncio import ensure_future

from descan.skipgraph.util import verify_skip_graph_integrity

from simulations.settings import SimulationSettings
from simulations.skipgraph.sg_simulation import SkipgraphSimulation


class ChurnSkipgraphSimulation(SkipgraphSimulation):

    def __init__(self, settings: SimulationSettings) -> None:
        super().__init__(settings)
        self.inactive_node_ids = set()
        self.active_node_ids = set()
        self.joining_node_ids = set()
        self.leaving_node_ids = set()

    async def on_ipv8_ready(self) -> None:
        await super().on_ipv8_ready()

        # Reset all search hops statistics (since introduction will also conduct a search)
        print("Resetting churn statistics")
        for node in self.nodes:
            node.overlay.search_hops = {}
            node.overlay.search_latencies = []
            node.overlay.join_latencies = []

        for ind in range(len(self.nodes)):
            self.active_node_ids.add(ind)

        # Start the churn loop
        self.register_task("churn", self.do_churn, interval=1)

    async def join_random_node(self):
        random_inactive_node_id = random.choice(list(self.inactive_node_ids))
        print("Node %d will join the Skip Graph" % random_inactive_node_id)
        random_active_node = self.nodes[random_inactive_node_id]
        self.inactive_node_ids.remove(random_inactive_node_id)
        self.joining_node_ids.add(random_inactive_node_id)
        introducer_node_id = random.choice(list(self.active_node_ids))
        introducer_node = self.nodes[introducer_node_id]
        self.initialize_routing_table(random_inactive_node_id, random_active_node)
        random_active_node.overlay.peers_info[introducer_node.overlay.my_peer] = introducer_node.overlay.get_my_node()

        await random_active_node.overlay.join(introducer_peer=introducer_node.overlay.my_peer)

        self.active_node_ids.add(random_inactive_node_id)
        self.joining_node_ids.remove(random_inactive_node_id)

    async def leave_random_node(self):
        random_active_node_id = random.choice(list(self.active_node_ids))
        print("Node %d will leave the Skip Graph" % random_active_node_id)
        random_active_node = self.nodes[random_active_node_id]
        self.active_node_ids.remove(random_active_node_id)
        self.leaving_node_ids.add(random_active_node_id)

        await random_active_node.overlay.leave()

        self.leaving_node_ids.remove(random_active_node_id)
        self.inactive_node_ids.add(random_active_node_id)

    async def do_churn(self):
        """
        Do some churn.
        """
        if len(self.active_node_ids) == 1:
            # There are too few nodes active - one node should join
            await self.join_random_node()
        elif len(self.inactive_node_ids) == 0:
            # There are no inactive nodes - make a random node leave
            await self.leave_random_node()
        else:
            should_join = bool(random.randint(0, 1))
            if should_join:
                await self.join_random_node()
            else:
                await self.leave_random_node()

        if not verify_skip_graph_integrity(self.nodes):
            print("Skip Graph not valid!!")
            for ind, node in enumerate(self.nodes):
                print("=== node %d (key: %d) ===\n%s\n" % (
                    ind, node.overlay.routing_table.key, node.overlay.routing_table))
            exit(1)


if __name__ == "__main__":
    settings = SimulationSettings()
    settings.peers = 1000
    settings.duration = 3600
    settings.logging_level = "ERROR"
    settings.profile = False
    settings.enable_community_statistics = True
    settings.enable_ipv8_ticker = False
    settings.latencies_file = "data/latencies.txt"
    simulation = ChurnSkipgraphSimulation(settings)
    simulation.MAIN_OVERLAY = "SkipGraphCommunity"

    ensure_future(simulation.run())

    simulation.loop.run_forever()
