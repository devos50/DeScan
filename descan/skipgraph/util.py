from typing import List

from descan.skipgraph import LEFT, RIGHT
from descan.skipgraph.community import SkipGraphCommunity
from descan.skipgraph.membership_vector import MembershipVector


def verify_skip_graph_integrity(nodes) -> bool:
    """
    Verify the integrity of the Skip Graph by iterating through each skip graph, level, and by verifying the links.
    """
    def get_skip_graphs(node) -> List[SkipGraphCommunity]:
        return [overlay for overlay in node.overlays if overlay.__class__.__name__ == "SkipGraphCommunity"]

    keys_to_nodes = {}
    for node in nodes:
        node_sgs: List[SkipGraphCommunity] = get_skip_graphs(node)
        if not node_sgs[0].routing_table:
            continue
        keys_to_nodes[node_sgs[0].routing_table.key] = node

    # At every level, the key of the left neighbour should be less than the node's key.
    # Vice versa, the key of the right neighbour should be larger than the node's key.

    # Verify the links
    for node in nodes:
        for sg_ind, skip_graph in enumerate(get_skip_graphs(node)):
            if not skip_graph.routing_table:
                continue

            for level in range(MembershipVector.LENGTH + 1):
                left_neighbour = skip_graph.routing_table.get(level, LEFT)
                if left_neighbour:
                    if left_neighbour.key >= skip_graph.routing_table.key:
                        print("Left neighbour of node with key %d should be smaller (is: %d)!" %
                              (skip_graph.routing_table.key, left_neighbour.key))
                        return False

                    n = keys_to_nodes[left_neighbour.key]
                    rn = get_skip_graphs(n)[sg_ind].routing_table.get(level, RIGHT)
                    if not rn:
                        print("Right neighbour of node with key %d on level %d not set while it should be" % (rn.key, level))
                        return False
                    if rn.key != skip_graph.routing_table.key:
                        print("Right neighbour of node on level %d with key %d not as it should be (%d)" % (level, rn.key, left_neighbour.key))
                        return False

                right_neighbour = skip_graph.routing_table.get(level, RIGHT)
                if right_neighbour:
                    if right_neighbour.key <= skip_graph.routing_table.key:
                        print("Right neighbour of node with key %d should be larger (is: %d)!" %
                              (skip_graph.routing_table.key, right_neighbour.key))
                        return False

                    n = keys_to_nodes[right_neighbour.key]
                    ln = get_skip_graphs(n)[sg_ind].routing_table.get(level, LEFT)
                    if not ln:
                        print("Left neighbour of node on with key %d level %d not set while it should be" % (ln.key, level))
                        return False
                    if ln.key != skip_graph.routing_table.key:
                        print("Left neighbour of node on level %d with key %d not as it should be (%d)" % (level, ln.key, right_neighbour.key))
                        return False
    return True
