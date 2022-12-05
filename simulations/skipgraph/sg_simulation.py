import hashlib
import os
import random
from asyncio import sleep
from typing import Dict, List

from descan.skipgraph import LEFT, RIGHT
from descan.skipgraph.community import SkipGraphCommunity
from descan.skipgraph.node import SGNode
from descan.skipgraph.util import verify_skip_graph_integrity

from ipv8.configuration import ConfigBuilder

from simulations.simulation import BaseSimulation
from simulations.skipgraph.settings import SkipGraphSimulationSettings


class SkipgraphSimulation(BaseSimulation):

    def __init__(self, settings: SkipGraphSimulationSettings) -> None:
        super().__init__(settings)
        self.node_keys_sorted = []
        self.searches_done = 0
        self.invalid_searches = 0
        self.target_frequency: Dict[int, int] = {}
        self.key_to_node_ind: Dict[int, int] = {}
        self.online_nodes = None
        self.offline_nodes = []

    def get_skip_graphs(self, node) -> List[SkipGraphCommunity]:
        return [overlay for overlay in node.overlays if overlay.__class__.__name__ == "SkipGraphCommunity"]

    def extend_skip_graph_neighbourhood(self, neighbourhood_size):
        # First, clear everything except the first NB
        for node in self.nodes:
            for skip_graph in self.get_skip_graphs(node):
                for level in range(skip_graph.routing_table.height()):
                    for side in [LEFT, RIGHT]:
                        nbs = skip_graph.routing_table.levels[level].neighbors[side]
                        if not nbs:
                            continue  # We cannot extend it

                        cur_nbs = nbs[0 if side == RIGHT else len(nbs) - 1]

                        # Clear everything except the first NB
                        skip_graph.routing_table.levels[level].neighbors[side] = [cur_nbs]

        # Extend the neighbourhoods
        for node in self.nodes:
            for sg_ind, skip_graph in enumerate(self.get_skip_graphs(node)):
                for level in range(skip_graph.routing_table.height()):
                    for side in [LEFT, RIGHT]:
                        nbs = skip_graph.routing_table.levels[level].neighbors[side]
                        if not nbs:
                            continue  # We cannot extend it

                        cur_nbs = nbs[0 if side == RIGHT else len(nbs) - 1]

                        while len(nbs) < neighbourhood_size:
                            # Get the left/right neighbour of the current neighbour
                            ipv8_nb_node = self.nodes[self.key_to_node_ind[cur_nbs.key]]
                            ipv8_nb_node_sg = self.get_skip_graphs(ipv8_nb_node)[sg_ind]
                            nb_nbs = ipv8_nb_node_sg.routing_table.levels[level].neighbors[side]
                            if not nb_nbs:
                                break  # Unable to extend further

                            nb_nb = ipv8_nb_node_sg.routing_table.levels[level].neighbors[side][
                                0 if side == RIGHT else len(nb_nbs) - 1]
                            skip_graph.routing_table.set(level, side, nb_nb)
                            cur_nbs = nb_nb

    def get_responsible_node_for_key(self, search_key: int):
        """
        Find the responsible node that is responsible for a particular key.
        """
        if search_key < self.node_keys_sorted[0]:
            target_node_key = self.node_keys_sorted[0]
        else:
            # Perform a search through the keys
            ind = len(self.node_keys_sorted) - 1
            while ind >= 0:
                if self.node_keys_sorted[ind] <= search_key:
                    target_node_key = self.node_keys_sorted[ind]
                    break
                ind -= 1

        return self.nodes[self.key_to_node_ind[target_node_key]]

    async def do_search(self, delay, node, search_key):
        await sleep(delay)
        results: List[SGNode] = []
        for sg_ind in range(self.settings.skip_graphs):
            res = await self.get_skip_graphs(node)[sg_ind].search(search_key)
            if res:
                results.append(res)

        if not results:
            # Search failed
            self.invalid_searches += 1
            self.searches_done += 1
            return False, None

        # Verify that this is the right search result
        res = results[0]  # TODO just take the first result for now
        if res.key not in self.node_keys_sorted:
            assert False, "We got a key result that is not registered in the Skip List!"

        search_result_is_correct = True
        if search_key < self.node_keys_sorted[0] and res.key != self.node_keys_sorted[0]:
            search_result_is_correct = False
        elif search_key >= self.node_keys_sorted[0]:
            res_ind = self.node_keys_sorted.index(res.key)
            if res_ind == len(self.node_keys_sorted) - 1:
                if search_key <= self.node_keys_sorted[res_ind - 1]:
                    search_result_is_correct = False
            else:
                if self.node_keys_sorted[res_ind + 1] <= search_key:
                    search_result_is_correct = False

        self.target_frequency[self.key_to_node_ind[res.key]] += 1
        if not search_result_is_correct:
            self.invalid_searches += 1

        self.searches_done += 1
        if self.searches_done % 100 == 0:
            print("Completed %d searches..." % self.searches_done)

        return search_result_is_correct, res

    def get_ipv8_builder(self, peer_id: int) -> ConfigBuilder:
        builder = super().get_ipv8_builder(peer_id)
        for sg_ind in range(self.settings.skip_graphs):
            cid: bytes = (b"%d" % sg_ind) * 20
            builder.add_overlay("SkipGraphCommunity", "my peer", [], [], {"community_id": cid}, [], allow_duplicate=True)

        return builder

    async def ipv8_discover_peers(self) -> None:
        """
        Ignore peer discovery. We don't use IPv8 peers.
        """
        pass

    def initialize_routing_table(self, ind: int, node) -> None:
        skip_graphs: List[SkipGraphCommunity] = self.get_skip_graphs(node)
        for sg_ind in range(self.settings.skip_graphs):
            int_pk = ind + 1
            if not self.settings.assign_sequential_sg_keys:
                if self.settings.fix_sg_key_distribution:
                    int_pk = (2 ** 32) // len(self.nodes) * ind
                else:
                    # Create a hash from the PK
                    h = hashlib.md5()
                    h.update(node.overlay.my_peer.public_key.key_to_bin())
                    int_pk = int.from_bytes(h.digest(), 'big') % (2 ** 32)

            if sg_ind == 0:
                self.node_keys_sorted.append(int_pk)
            skip_graphs[sg_ind].initialize_routing_table(int_pk)

    async def start_ipv8_nodes(self) -> None:
        await super().start_ipv8_nodes()

        # Initialize the routing tables of each node after starting the IPv8 nodes.
        for ind, node in enumerate(self.nodes):
            self.initialize_routing_table(ind, node)

        self.node_keys_sorted = sorted(self.node_keys_sorted)

    async def on_ipv8_ready(self) -> None:
        # Initialize the key to node map and target frequency map
        for ind, node in enumerate(self.nodes):
            self.key_to_node_ind[self.get_skip_graphs(node)[0].routing_table.key] = ind
            self.target_frequency[ind] = 0

        # Nodes are now joining the Skip Graph.
        # For better performance and load balancing, we keep track of the nodes that have already joined, and the
        # nodes that still need to join. We choose the node with id 0 as introducer peer.
        introducer_node = self.nodes[0]
        introducer_peer = self.get_skip_graphs(introducer_node)[0].my_peer
        introducer_node_sgs: List[SkipGraphCommunity] = self.get_skip_graphs(introducer_node)

        node_ids = list(range(1, len(self.nodes)))
        random.shuffle(node_ids)
        count = 0
        for ind in node_ids:
            if count % 100 == 0:
                print("%d nodes joined the Skip Graphs!" % count)

            joining_node_sgs: List[SkipGraphCommunity] = self.get_skip_graphs(self.nodes[ind])
            for sg_ind in range(self.settings.skip_graphs):
                # Make sure this node knows about the introducer peer
                self.logger.info("Node %d will join the Skip Graph", ind)
                joining_node_sgs[sg_ind].peers_info[introducer_peer] = introducer_node_sgs[sg_ind].get_my_node()
                await joining_node_sgs[sg_ind].join(introducer_peer=introducer_peer)
                await sleep(0.1)
            self.logger.info("Node %d joined %d Skip Graphs...", self.settings.skip_graphs, ind)
            count += 1

        # Verify the integrity of the Skip Graph
        if not verify_skip_graph_integrity(self.nodes):
            print("Skip Graph not valid!!")
            for ind, node in enumerate(self.nodes):
                print("=== node %d (key: %d) ===\n%s\n" % (ind, node.overlay.routing_table.key, node.overlay.routing_table))
            exit(1)
        else:
            print("Skip Graph valid!")

        self.online_nodes = [n for n in self.nodes]

        print("Extending Skip Graph neighbourhood size to %d" % self.settings.nb_size)
        self.extend_skip_graph_neighbourhood(self.settings.nb_size)

    def get_message_statistics(self, node):
        """
        Compute statistics on messages sent for a particular IPv8 node.
        """
        msg_stats_for_node: Dict[int, List] = {}
        for skip_graph in self.get_skip_graphs(node):
            for msg_id, network_stats in node.endpoint.statistics[skip_graph.get_prefix()].items():
                if msg_id not in msg_stats_for_node:
                    msg_stats_for_node[msg_id] = [0, 0, 0, 0]
                msg_stats_for_node[msg_id][0] += network_stats.num_up
                msg_stats_for_node[msg_id][1] += network_stats.num_down
                msg_stats_for_node[msg_id][2] += network_stats.bytes_up
                msg_stats_for_node[msg_id][3] += network_stats.bytes_down

        return msg_stats_for_node

    def on_simulation_finished(self):
        """
        The experiment is finished. Write the results away.
        """
        # Bandwidth statistics
        # with open(os.path.join(self.data_dir, "bw_usage.csv"), "w") as bw_file:
        #     bw_file.write("peer,bytes_up,bytes_down\n")
        #     for ind, node in enumerate(self.nodes):
        #         bw_file.write("%d,%d,%d\n" % (ind, node.overlay.endpoint.bytes_up, node.overlay.endpoint.bytes_down))

        # Message statistics
        if self.settings.enable_community_statistics:
            with open(os.path.join(self.data_dir, "tot_bw_statistics.csv"), "w") as tot_bw_stats_file:
                tot_bw_stats_file.write("peer,bytes_up,bytes_down\n")
                with open(os.path.join(self.data_dir, "msg_statistics.csv"), "w") as msg_stats_file:
                    msg_stats_file.write("peer,msg_id,num_up,num_down,bytes_up,bytes_down\n")
                    for ind, node in enumerate(self.nodes):
                        msg_stats_for_node = self.get_message_statistics(node)
                        tot_up = 0
                        tot_down = 0
                        for msg_id, msg_info in msg_stats_for_node.items():
                            tot_up += msg_info[2]
                            tot_down += msg_info[3]
                            msg_stats_file.write("%d,%d,%d,%d,%d,%d\n" % (ind, msg_id, msg_info[0], msg_info[1],
                                                                          msg_info[2], msg_info[3]))

                        tot_bw_stats_file.write("%d,%d,%d\n" % (ind, tot_up, tot_down))

            # Aggregated bw statistics
            with open(os.path.join(self.data_dir, "aggregate_msg_statistics.csv"), "w") as msg_stats_file:
                msg_stats_file.write("peers,peer,bytes_up,bytes_down\n")
                for ind, node in enumerate(self.nodes):
                    tot_up, tot_down = 0, 0
                    for skip_graph in self.get_skip_graphs(node):
                        for msg_id, network_stats in node.endpoint.statistics[skip_graph.get_prefix()].items():
                            tot_up += network_stats.bytes_up
                            tot_down += network_stats.bytes_down
                    msg_stats_file.write("%d,%d,%d,%d\n" % (self.settings.peers, ind, tot_up, tot_down))

        # Search hops statistics
        hops_freq = {}
        for node in self.nodes:
            for skip_graph in self.get_skip_graphs(node):
                for num_hops, freq in skip_graph.search_hops.items():
                    if num_hops not in hops_freq:
                        hops_freq[num_hops] = 0
                    hops_freq[num_hops] += freq

        tot_count = 0
        tot = 0
        with open(os.path.join(self.data_dir, "search_hops.csv"), "w") as search_hops_file:
            search_hops_file.write("peers,nb_size,hops,freq\n")
            for num_hops, freq in hops_freq.items():
                tot += num_hops * freq
                tot_count += freq
                search_hops_file.write("%d,%d,%d,%d\n" % (self.settings.peers, self.settings.nb_size, num_hops, freq))

        if tot_count > 0:
            print("Average search hops: %f" % (tot / tot_count))

        # Skip graph search latencies
        with open(os.path.join(self.data_dir, "latencies.csv"), "w") as latencies_file:
            latencies_file.write("peers,nb_size,operation,time\n")
            for node in self.nodes:
                for skip_graph in self.get_skip_graphs(node):
                    for latency in skip_graph.search_latencies:
                        latencies_file.write("%d,%d,%s,%f\n" % (self.settings.peers, self.settings.nb_size, "search", latency))

                    for latency in skip_graph.join_latencies:
                        latencies_file.write("%d,%d,%s,%f\n" % (self.settings.peers, self.settings.nb_size, "join", latency))

                    for latency in skip_graph.leave_latencies:
                        latencies_file.write("%d,%d,%s,%f\n" % (self.settings.peers, self.settings.nb_size, "leave", latency))

        # Write statistics on search targets
        with open(os.path.join(self.data_dir, "search_targets.csv"), "w") as out_file:
            out_file.write("peer,target_count\n")
            for peer_id, target_count in self.target_frequency.items():
                out_file.write("%d,%d\n" % (peer_id, target_count))
