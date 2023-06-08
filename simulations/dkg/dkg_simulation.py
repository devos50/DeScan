import json
import os
import random
from asyncio import sleep
from binascii import unhexlify, hexlify
from statistics import NormalDist
from typing import List, Dict

from numpy import average, std

from descan.core.content import Content
from descan.core.db.triplet import Triplet
from descan.core.rules.ethereum import EthereumBlockRule, EthereumTransactionRule
from descan.core.rules.ptn import PTNRule
from ipv8.configuration import ConfigBuilder

from simulations.dkg.settings import DKGSimulationSettings, Dataset
from simulations.skipgraph.sg_simulation import SkipgraphSimulation


class DKGSimulation(SkipgraphSimulation):

    def __init__(self, settings: DKGSimulationSettings) -> None:
        super().__init__(settings)
        self.searches_done: int = 0
        self.failed_searches: int = 0

    def get_ipv8_builder(self, peer_id: int) -> ConfigBuilder:
        builder = ConfigBuilder().clear_keys().clear_overlays()
        builder.add_key("my peer", "curve25519", None)
        builder.add_overlay("DKGCommunity", "my peer", [], [], {}, [])

        for sg_ind in range(self.settings.skip_graphs):
            cid: bytes = (b"%d" % sg_ind) * 20
            builder.add_overlay("SkipGraphCommunity", "my peer", [], [], {"community_id": cid}, [], allow_duplicate=True)

        return builder

    def on_triplets_generated(self, content: Content, triplets: List[Triplet]):
        """
        We generated some triplets. Directly get the responsible node and store the triplets on that node.
        """
        content_keys = Content.get_keys(content.identifier, num_keys=self.settings.replication_factor)
        for ind in range(self.settings.replication_factor):
            responsible_node = self.get_responsible_node_for_key(content_keys[ind])
            for triplet in triplets:
                responsible_node.overlay.knowledge_graph.add_triplet(triplet)

    def get_message_statistics(self, node):
        msg_stats_for_node = super().get_message_statistics(node)

        # Include the DKG overlay message statistics
        for msg_id, network_stats in node.endpoint.statistics[node.overlay.get_prefix()].items():
            if msg_id not in msg_stats_for_node:
                msg_stats_for_node[msg_id] = [0, 0, 0, 0]
            msg_stats_for_node[msg_id][0] += network_stats.num_up
            msg_stats_for_node[msg_id][1] += network_stats.num_down
            msg_stats_for_node[msg_id][2] += network_stats.bytes_up
            msg_stats_for_node[msg_id][3] += network_stats.bytes_down

        return msg_stats_for_node

    async def setup_tribler_experiment(self):
        # Give each node the PTN rule
        ptn_rule = PTNRule()
        for node in self.nodes:
            node.overlay.rules_db.add_rule(ptn_rule)

        # Read the torrents data file and assign them to different nodes
        print("Setting up Tribler experiment...")
        if self.settings.fast_data_injection:
            # First, change the callback of the rule execution engines so we don't spread edges in the network
            for node in self.nodes:
                node.overlay.rule_execution_engine.callback = self.on_triplets_generated

        with open(self.settings.data_file_name) as torrents_file:
            for ind, torrent_line in enumerate(torrents_file.readlines()):
                if ind % 1000 == 0:
                    print("Processed %d torrents..." % ind)

                parts = torrent_line.strip().split("\t")
                content_hash = unhexlify(parts[0])
                content_data = parts[1].encode()
                content = Content(content_hash, content_data)

                target_node = self.nodes[ind % len(self.nodes)]
                target_node.overlay.content_db.add_content(content)

                target_node.overlay.rule_execution_engine.process_queue.append(content)
                target_node.overlay.rule_execution_engine.process()

        if not self.settings.fast_data_injection:
            await sleep(20)  # Give some time to store the edges in the network

    def confidence_interval(self, data, confidence=0.95):
        dist = NormalDist.from_samples(data)
        z = NormalDist().inv_cdf((1 + confidence) / 2.)
        h = dist.stdev * z / ((len(data) - 1) ** .5)
        return h

    async def setup_ethereum_experiment(self):
        # Give each node the Ethereum rules
        eth_block_rule = EthereumBlockRule()
        eth_tx_rule = EthereumTransactionRule()
        for node in self.nodes:
            node.overlay.rules_db.add_rule(eth_block_rule)
            node.overlay.rules_db.add_rule(eth_tx_rule)

        print("Setting up Ethereum experiment...")
        if self.settings.fast_data_injection:
            # First, change the callback of the rule execution engines so we don't spread edges in the network
            for node in self.nodes:
                node.overlay.rule_execution_engine.callback = self.on_triplets_generated

        if self.settings.track_storage_interval:
            with open(os.path.join(self.data_dir, "kg_storage.csv"), "w") as out_file:
                out_file.write("peers,txs_indexed,avg_storage,min_storage,max_storage,stddev_storage,conf_storage\n")

        # Feed Ethereum blocks to the rule execution engines
        total_tx = 0
        blocks_processed = 0
        next_storage_analysis_checkpoint = self.settings.track_storage_interval

        with open(self.settings.data_file_name) as blocks_file:
            for ind, block_line in enumerate(blocks_file.readlines()):
                if self.settings.max_eth_blocks and blocks_processed >= self.settings.max_eth_blocks:
                    print("Done - processed %d ETH blocks (txs so far: %d)..." % (ind, total_tx))
                    break

                if ind % 100 == 0:
                    print("Processed %d ETH blocks (txs so far: %d)..." % (ind, total_tx))

                block_json = json.loads(block_line.strip())
                total_tx += len(block_json["transactions"])
                content_hash = unhexlify(block_json["hash"][2:])
                content_data = block_line.strip().encode()
                content = Content(content_hash, content_data)

                target_node = self.nodes[ind % len(self.nodes)]
                target_node.overlay.content_db.add_content(content)

                target_node.overlay.rule_execution_engine.process_queue.append(content)
                while target_node.overlay.rule_execution_engine.process_queue:
                    target_node.overlay.rule_execution_engine.process()

                # Do we need to analyse the storage?
                if self.settings.track_storage_interval and total_tx >= next_storage_analysis_checkpoint:
                    storage_costs: List[int] = []
                    for ind, node in enumerate(self.nodes):
                        storage_costs.append(node.overlay.knowledge_graph.get_storage_costs())

                    # Write away the knowledge graph statistics per node
                    with open(os.path.join(self.data_dir, "kg_storage.csv"), "a") as out_file:
                        out_file.write("%d,%d,%d,%d,%d,%f,%f\n" % (
                            self.settings.peers, total_tx, average(storage_costs), min(storage_costs),
                            max(storage_costs), std(storage_costs), self.confidence_interval(storage_costs)))

                    next_storage_analysis_checkpoint += self.settings.track_storage_interval

                blocks_processed += 1

        print("Total ETH transactions: %d" % total_tx)

    async def start_ipv8_nodes(self) -> None:
        await super().start_ipv8_nodes()

        # Make sure the DKGCommunity knows about the Skip Graph instances
        for node in self.nodes:
            node.overlay.skip_graphs = self.get_skip_graphs(node)

    async def on_ipv8_ready(self) -> None:
        await super().on_ipv8_ready()

        # Reset the search statistics since joining the SG will also conduct searches.
        self.reset_search_statistics()

        # Set the replication factor
        for node in self.nodes:
            node.overlay.replication_factor = self.settings.replication_factor

        if self.settings.dataset == Dataset.TRIBLER:
            await self.setup_tribler_experiment()
        elif self.settings.dataset == Dataset.ETHEREUM:
            await self.setup_ethereum_experiment()
        else:
            raise RuntimeError("Unknown dataset %s" % self.settings.dataset)

        # Take a few nodes offline
        if self.settings.offline_fraction > 0:
            num_offline: int = int(len(self.nodes) * (self.settings.offline_fraction / 100))
            print("Bringing %d nodes offline..." % num_offline)
            for node in random.sample(self.nodes, num_offline):
                node.overlay.is_offline = True
                for skip_graph in self.get_skip_graphs(node):
                    skip_graph.is_offline = True
                self.online_nodes.remove(node)
                self.offline_nodes.append(node)

        # Make some nodes malicious
        malicious_nodes = set()
        if self.settings.malicious_fraction > 0:
            num_malicious: int = int(len(self.nodes) * (self.settings.malicious_fraction / 100))
            print("Making %d nodes malicious..." % num_malicious)
            for node in random.sample(self.online_nodes, num_malicious):
                node.overlay.is_malicious = True
                for skip_graph in self.get_skip_graphs(node):
                    skip_graph.is_malicious = True
                malicious_nodes.add(node)

        # Determine content that has generated edges - we do not want to search for content that has no triplets
        content_with_triplets = set()
        for node in self.nodes:
            content_with_triplets = content_with_triplets.union(node.overlay.knowledge_graph.stored_content)

        print("%d content items with triplets" % len(content_with_triplets))

        print("Starting edge searches")

        async def do_search(node, content_hash):
            edges = await node.overlay.search_edges(content_hash)
            if not edges:
                self.failed_searches += 1

            self.searches_done += 1
            if self.searches_done % 100 == 0:
                print("Completed %d searches..." % self.searches_done)

        # Determine nodes eligible for search (that should be nodes that are online and not dishonest)
        eligible_nodes = []
        for node in self.nodes:
            if node not in self.offline_nodes and node not in malicious_nodes:
                eligible_nodes.append(node)

        list_content_with_triplets = list(content_with_triplets)
        for _ in range(self.settings.num_searches):
            content_hash = random.choice(list_content_with_triplets)
            random_node = random.choice(eligible_nodes)
            await do_search(random_node, content_hash)

        print("Total searches: %d, failed searches: %d" % (self.searches_done, self.failed_searches))

    def reset_search_statistics(self):
        """
        Reset all search statistics.
        """
        print("Resetting search statistics")
        for node in self.nodes:
            for skip_graph in self.get_skip_graphs(node):
                skip_graph.search_hops = {}
                skip_graph.search_latencies = []
                skip_graph.search_messages = {}
                node.endpoint.enable_community_statistics(skip_graph.get_prefix(), False)
                node.endpoint.enable_community_statistics(skip_graph.get_prefix(), True)

    def on_simulation_finished(self):
        super().on_simulation_finished()

        # Write away which node stores what
        with open(os.path.join(self.data_dir, "storage.csv"), "w") as out_file:
            out_file.write("content_id,peer_id\n")
            for ind, node in enumerate(self.nodes):
                for content_id in node.overlay.knowledge_graph.stored_content:
                    out_file.write("%s,%d\n" % (hexlify(content_id).decode(), ind))

        # Write away the knowledge graph statistics per node
        with open(os.path.join(self.data_dir, "kg_stats.csv"), "w") as out_file:
            out_file.write("peers,nb_size,offline_fraction,malicious_fraction,skip_graphs,replication_factor,peer,key,key_distribution,num_edges,storage_costs\n")
            for ind, node in enumerate(self.nodes):
                num_edges = node.overlay.knowledge_graph.get_num_edges()
                storage_costs = node.overlay.knowledge_graph.get_storage_costs()
                out_file.write("%d,%d,%d,%d,%d,%d,%d,%d,%s,%d,%d\n" %
                               (self.settings.peers, self.settings.nb_size, self.settings.offline_fraction,
                                self.settings.malicious_fraction, self.settings.skip_graphs,
                                self.settings.replication_factor, ind, node.overlay.get_sg_key(),
                                "fixed" if self.settings.fix_sg_key_distribution else "random",
                                num_edges, storage_costs))

        # Write away the edge search latencies
        num_edge_searches: int = 0
        tot_sg_search_latency: float = 0
        tot_triplets_requests_latency: float = 0
        tot_search_latency: float = 0
        with open(os.path.join(self.data_dir, "edge_search_latencies.csv"), "w") as latencies_file:
            latencies_file.write("peers,nb_size,offline_fraction,malicious_fraction,skip_graphs,replication_factor,part,time\n")
            for node in self.nodes:
                for latency in node.overlay.edge_search_latencies:
                    num_edge_searches += 1
                    tot_sg_search_latency += latency[0]
                    tot_triplets_requests_latency += latency[1]
                    tot_search_latency = latency[0] + latency[1]
                    latencies_file.write("%d,%d,%d,%d,%d,%d,sg,%f\n" %
                                         (self.settings.peers, self.settings.nb_size, self.settings.offline_fraction,
                                          self.settings.malicious_fraction, self.settings.skip_graphs,
                                          self.settings.replication_factor, latency[0]))
                    latencies_file.write("%d,%d,%d,%d,%d,%d,eva,%f\n" %
                                         (self.settings.peers, self.settings.nb_size, self.settings.offline_fraction,
                                          self.settings.malicious_fraction, self.settings.skip_graphs,
                                          self.settings.replication_factor, latency[1]))
                    latencies_file.write("%d,%d,%d,%d,%d,%d,total,%f\n" %
                                         (self.settings.peers, self.settings.nb_size, self.settings.offline_fraction,
                                          self.settings.malicious_fraction, self.settings.skip_graphs,
                                          self.settings.replication_factor, tot_search_latency))

        if num_edge_searches > 0:
            print("Average SG search latency: %f, triplets request latency: %f, E2E latency: %f" % (
                    tot_sg_search_latency / num_edge_searches,
                    tot_triplets_requests_latency / num_edge_searches,
                    tot_search_latency / num_edge_searches))

        # Determine individual search message statistics
        aggregated_search_message_statistics: Dict[int, Dict[int, int]] = {}
        for node in self.nodes:
            for skip_graph in node.overlay.skip_graphs:
                for search_id, msg_stats in skip_graph.search_messages.items():
                    if search_id not in aggregated_search_message_statistics:
                        aggregated_search_message_statistics[search_id] = {}

                    for msg_type, msg_freq in msg_stats.items():
                        if msg_type not in aggregated_search_message_statistics[search_id]:
                            aggregated_search_message_statistics[search_id][msg_type] = 0
                        aggregated_search_message_statistics[search_id][msg_type] += msg_freq

        # Now we combine these statistics to get the message statistics per edge search
        aggregated_edge_search_message_statistics: Dict[int, Dict[int, int]] = {}
        for node in self.nodes:
            for edge_search_id, sg_ids in node.overlay.sg_identifiers_for_edge_searches.items():
                aggregated_edge_search_message_statistics[edge_search_id] = {}
                for sg_id in sg_ids:
                    sg_msg_stats = aggregated_search_message_statistics[sg_id]
                    for msg_type, msg_freq in sg_msg_stats.items():
                        if msg_type not in aggregated_edge_search_message_statistics[edge_search_id]:
                            aggregated_edge_search_message_statistics[edge_search_id][msg_type] = 0
                        aggregated_edge_search_message_statistics[edge_search_id][msg_type] += msg_freq

        edge_search_bw_stats = {}
        msg_sizes = {2: 306, 3: 294, 4: 290}
        for edge_search_id, edge_search_stats in aggregated_edge_search_message_statistics.items():
            tot_bw = 0
            tot_msgs = 0
            for msg_type, msg_freq in edge_search_stats.items():
                tot_bw += msg_sizes[msg_type] * msg_freq
                tot_msgs += msg_freq

            edge_search_bw_stats[edge_search_id] = (tot_msgs, tot_bw)

        with open(os.path.join(self.data_dir, "edge_search_bw_stats.csv"), "w") as edge_search_bw_stats_file:
            edge_search_bw_stats_file.write("messages,bandwidth\n")
            for tot_msgs, tot_bw in edge_search_bw_stats.values():
                edge_search_bw_stats_file.write("%d,%d\n" % (tot_msgs, tot_bw))

        # Write aggregated statistics away
        aggregated_file_path = os.path.join("data", "edge_searches_exp_%s.csv" % self.settings.name)
        if os.path.exists(aggregated_file_path):
            with open(aggregated_file_path, "a") as out_file:
                out_file.write("%d,%d,%d,%d,%d,%d,%d,%d\n" % (self.settings.peers, self.settings.nb_size,
                                                              self.settings.offline_fraction,
                                                              self.settings.malicious_fraction,
                                                              self.settings.skip_graphs,
                                                              self.settings.replication_factor,
                                                              self.searches_done, self.failed_searches))

        aggregated_file_path = os.path.join("data", "edge_search_latencies_exp_%s.csv" % self.settings.name)
        if os.path.exists(aggregated_file_path):
            with open(aggregated_file_path, "a") as out_file:
                with open(os.path.join(self.data_dir, "edge_search_latencies.csv")) as latencies_file:
                    parsed_header = False
                    for line in latencies_file.readlines():
                        if not parsed_header:
                            parsed_header = True
                            continue

                        out_file.write(line)

        aggregated_file_path = os.path.join("data", "kg_stats_exp_%s.csv" % self.settings.name)
        if os.path.exists(aggregated_file_path):
            with open(aggregated_file_path, "a") as out_file:
                with open(os.path.join(self.data_dir, "kg_stats.csv")) as kg_stats_file:
                    parsed_header = False
                    for line in kg_stats_file.readlines():
                        if not parsed_header:
                            parsed_header = True
                            continue

                        out_file.write(line)

        aggregated_file_path = os.path.join("data", "search_hops_exp_%s.csv" % self.settings.name)
        if os.path.exists(aggregated_file_path):
            with open(aggregated_file_path, "a") as out_file:
                with open(os.path.join(self.data_dir, "search_hops.csv")) as kg_stats_file:
                    parsed_header = False
                    for line in kg_stats_file.readlines():
                        if not parsed_header:
                            parsed_header = True
                            continue

                        out_file.write(line)
