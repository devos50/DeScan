from typing import Set, List

import networkx as nx
from ipv8.messaging.serialization import default_serializer

from descan.core.db.triplet import Triplet


class KnowledgeGraph:
    """
    Represents the local knowledge graph.
    """

    def __init__(self) -> None:
        self.graph = nx.DiGraph()
        self.stored_content: Set[bytes] = set()

    def reset(self) -> None:
        self.graph = nx.DiGraph()
        self.stored_content = set()

    def add_triplet(self, triplet: Triplet) -> None:
        self.stored_content.add(triplet.head)
        if self.graph.has_edge(triplet.head, triplet.tail):
            edge = self.graph.edges[triplet.head, triplet.tail]
            if edge["attr"]["relation"] == triplet.relation:
                # Edge seems to exist - simply merge the rules
                for rule in triplet.rules:
                    if rule not in edge["attr"]["rules"]:
                        edge["attr"]["rules"].append(rule)

                return

        # Otherwise, add the adge as new
        self.graph.add_edge(triplet.head, triplet.tail, attr={"relation": triplet.relation, "rules": triplet.rules})

    def get_triplets_of_node(self, content: bytes) -> List[Triplet]:
        """
        Fetch the triplets around a particular node.
        """
        triplets = []
        for edge in list(self.graph.in_edges(content)) + list(self.graph.out_edges(content)):
            relation = self.graph.edges[edge]["attr"]["relation"]
            triplet = Triplet(edge[0], relation, edge[1])
            triplets.append(triplet)
        return triplets

    def get_num_edges(self) -> int:
        return len(self.graph.edges)

    def get_storage_costs(self) -> int:
        """
        Compute the storage cost of the knowledge graph by serializing each Triplet into a Payload and summing
        their lengths.
        """
        total_bytes = 0
        for edge in self.graph.edges:
            relation = self.graph.edges[edge]["attr"]["relation"]
            triplet = Triplet(edge[0], relation, edge[1])
            triplet.rules = self.graph.edges[edge]["attr"]["rules"]
            total_bytes += len(default_serializer.pack_serializable(triplet.to_payload()))

        return total_bytes
