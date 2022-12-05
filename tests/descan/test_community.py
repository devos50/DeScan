from typing import List

from descan.core.community import DKGCommunity
from descan.core.content import Content
from descan.core.db.triplet import Triplet
from descan.skipgraph.community import SkipGraphCommunity
from descan.skipgraph.membership_vector import MembershipVector
from descan.skipgraph.util import verify_skip_graph_integrity

from ipv8.test.base import TestBase


class CustomKeyContent(Content):

    def get_keys(self, num_keys: int = 1) -> List[int]:
        return [int.from_bytes(self.identifier, 'big') % (2 ** 32)]


class TestDKGCommunityBase(TestBase):
    NUM_SKIP_GRAPHS = 1

    def initialize_skip_graphs(self):
        for node in self.nodes:
            for i in range(self.NUM_SKIP_GRAPHS):
                cid: bytes = (b"%d" % i) * 20
                sg: SkipGraphCommunity = SkipGraphCommunity(node.overlay.my_peer, node.overlay.endpoint,
                                                            node.overlay.network, community_id=cid)
                sg.my_estimated_wan = node.overlay.endpoint.wan_address
                sg.my_estimated_lan = node.overlay.endpoint.lan_address
                node.overlay.skip_graphs.append(sg)

    def initialize_routing_tables(self, nodes_info):
        for sg_ind in range(self.NUM_SKIP_GRAPHS):
            for ind, node_info in enumerate(nodes_info):
                # Pad the list until we have sufficient bits
                bin_list = node_info[1][sg_ind]
                while len(bin_list) != MembershipVector.LENGTH:
                    bin_list += [0]
                self.nodes[ind].overlay.skip_graphs[sg_ind].initialize_routing_table(node_info[0],
                                                                                     mv=MembershipVector(bin_list))

    async def setup_skip_graphs(self):
        # Make sure peers know each other in the DKG community
        await self.introduce_nodes()

        # Make sure peers know each other in the skip graphs
        for sg_ind in range(self.NUM_SKIP_GRAPHS):
            for node in self.nodes:
                for other in self.nodes:
                    if other != node:
                        node.overlay.skip_graphs[sg_ind].walk_to(other.endpoint.wan_address)
            await self.deliver_messages()

        for node in self.nodes[1:]:
            for skip_graph in node.overlay.skip_graphs:
                await skip_graph.join(introducer_peer=self.nodes[0].overlay.my_peer)


class TestDKGCommunitySingleReplication(TestDKGCommunityBase):
    NUM_NODES = 2
    COMMUNITY = DKGCommunity
    NUM_SKIP_GRAPHS = 1

    def setUp(self):
        super(TestDKGCommunitySingleReplication, self).setUp()
        self.initialize(DKGCommunity, self.NUM_NODES)

        MembershipVector.LENGTH = 2
        nodes_info = [
            (0, [[0, 0], [0, 0]]),
            (1, [[0, 1], [0, 1]]),
        ]

        for node in self.nodes:
            node.overlay.should_verify_key = False
            node.overlay.replication_factor = 1
            node.overlay.start_rule_execution_engine()

        self.initialize_skip_graphs()
        self.initialize_routing_tables(nodes_info)

    async def test_store_graph_node(self):
        """
        Test generating, storing and retrieving a graph node in the network.
        """
        await self.setup_skip_graphs()

        # Test the situation where no edges are returned
        triplets = await self.nodes[0].overlay.search_edges(b"abcdefg")
        assert len(triplets) == 0

        triplet = Triplet(b"abcdefg", b"b", b"c")
        await self.nodes[0].overlay.on_new_triplets_generated(Content(b"abcdefg", b""), [triplet])
        await self.deliver_messages()
        assert self.nodes[1].overlay.knowledge_graph.get_num_edges() == 1

        # Now we try to fetch all edges from node 1
        triplets = await self.nodes[0].overlay.search_edges(b"abcdefg")
        assert len(triplets) == 1

        # Test searching locally
        triplets = await self.nodes[1].overlay.search_edges(b"abcdefg")
        assert len(triplets) == 1

    async def test_storage_request(self):
        """
        Test sending storage requests.
        """
        await self.setup_skip_graphs()

        content1 = CustomKeyContent(b"", b"")
        content2 = CustomKeyContent(b"\x01", b"")

        target_node = self.nodes[0].overlay.skip_graphs[0].get_my_node()
        assert await self.nodes[0].overlay.send_storage_request(target_node, content1.identifier, content1.get_keys(1)[0])
        assert not await self.nodes[1].overlay.send_storage_request(target_node, content2.identifier, content2.get_keys(1)[0])

        target_node = self.nodes[1].overlay.skip_graphs[0].get_my_node()
        assert not await self.nodes[1].overlay.send_storage_request(target_node, content1.identifier, content1.get_keys(1)[0])
        assert await self.nodes[1].overlay.send_storage_request(target_node, content2.identifier, content2.get_keys(1)[0])


class TestDKGCommunityDoubleReplication(TestDKGCommunityBase):
    NUM_NODES = 4
    NUM_SKIP_GRAPHS = 1

    async def setUp(self):
        super(TestDKGCommunityDoubleReplication, self).setUp()
        self.initialize(DKGCommunity, self.NUM_NODES)

        MembershipVector.LENGTH = 4
        nodes_info = [
            (99, [[0, 0], [0, 0]]),
            (21, [[1, 0], [1, 0]]),
            (33, [[0, 1], [0, 1]]),
            (36, [[1, 1], [1, 1]])
        ]

        for node in self.nodes:
            node.overlay.should_verify_key = False
            node.overlay.replication_factor = 2
            node.overlay.start_rule_execution_engine()

        self.initialize_skip_graphs()
        self.initialize_routing_tables(nodes_info)

    async def test_store_graph_node(self):
        """
        Test generating, storing and retrieving a graph node in the network.
        """
        await self.setup_skip_graphs()
        Content.custom_keys = [20, 50]
        triplet = Triplet(b"abcdefg", b"b", b"c")

        await self.nodes[0].overlay.on_new_triplets_generated(Content(b"abcdefg", b""), [triplet])
        await self.deliver_messages()

        # At least two nodes should store this triplet
        cnt = 0
        for node in self.nodes:
            if node.overlay.knowledge_graph.get_num_edges() == 1:
                cnt += 1
        assert cnt == 2

        # Now we try to fetch all edges from node 1
        triplets = await self.nodes[0].overlay.search_edges(b"abcdefg")
        assert len(triplets) == 1
        Content.custom_keys = None


class TestDKGCommunityDoubleReplicationDoubleSkipGraph(TestDKGCommunityDoubleReplication):
    NUM_NODES = 4
    NUM_SKIP_GRAPHS = 2
