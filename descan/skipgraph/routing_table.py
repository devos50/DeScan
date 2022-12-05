from __future__ import annotations

import logging
from typing import TYPE_CHECKING, List, Optional, Set

from descan.skipgraph import RIGHT, LEFT, Direction
from descan.skipgraph.membership_vector import MembershipVector

if TYPE_CHECKING:
    from descan.skipgraph.node import SGNode


class RoutingTable:

    def __init__(self, key: int, mv: MembershipVector):
        self.key: int = key
        self.mv: MembershipVector = mv
        self.max_level: int = 0
        self.levels: List[RoutingTableSingleLevel] = []
        self.logger = logging.getLogger(__name__)

        # Initialize all levels
        for level in range(MembershipVector.LENGTH + 1):
            self.levels.append(RoutingTableSingleLevel(self.key, level))

    def get(self, level: int, side: Direction) -> Optional[SGNode]:
        """
        Return the immediate neighbour on a particular level and a side.
        """
        if level >= len(self.levels):
            return None

        nbs = self.levels[level].neighbors[side]
        if not nbs:
            return None

        ind = 0 if side == RIGHT else len(self.levels[level].neighbors[side]) - 1
        return nbs[ind]

    def get_best(self, level: int, side: Direction, search_target: int) -> Optional[SGNode]:
        """
        Return the best search result.
        """
        nbs = self.levels[level].neighbors[side]
        if not nbs:
            return None

        best: Optional[SGNode] = nbs[0]
        if side == RIGHT:
            # Find the right neighbour with the largest key smaller than the search target
            cur_ind: int = 1
            while cur_ind <= len(nbs) - 1 and nbs[cur_ind].key <= search_target:
                best = nbs[cur_ind]
                cur_ind += 1
        elif side == LEFT:
            cur_ind: int = len(nbs) - 1
            while cur_ind >= 0 and nbs[cur_ind].key >= search_target:
                best = nbs[cur_ind]
                cur_ind -= 1
        return best

    def set(self, level: int, side: Direction, node: Optional[SGNode]) -> None:
        if node is None:
            return

        side_str = "left" if side == LEFT else "right"
        self.logger.debug("Node with key %d setting %s neighbour to %s at level %d", self.key, side_str, node, level)
        if node not in self.levels[level].neighbors[side]:
            self.levels[level].neighbors[side].append(node)
            self.levels[level].neighbors[side].sort(key=lambda x: x.key)

    def remove_node(self, key: int):
        """
        Remove the node with a particular key from the routing table, replacing it with None.
        """
        for lvl in range(self.height()):
            for side in [LEFT, RIGHT]:
                is_in = None
                for nb in self.levels[lvl].neighbors[side]:
                    if nb.key == key:
                        is_in = nb
                        break

                if is_in:
                    self.levels[lvl].neighbors[side].remove(nb)

    def get_all_nodes(self) -> Set[SGNode]:
        """
        Return all unique nodes in the routing table.
        """
        all_nodes = set()
        for level in self.levels:
            for nb_list in level.neighbors:
                for nb in nb_list:
                    all_nodes.add(nb)

        return all_nodes

    def height(self) -> int:
        """
        Return the height of the routing table, i.e., the number of levels.
        """
        return len(self.levels)

    def __str__(self) -> str:
        if not self.levels:
            return "<empty routing table>"

        buf = []
        for i in range(len(self.levels)):
            if self.levels[i].is_empty():
                continue
            buf.append(str(self.levels[i]))
        buf.append("=== RT node %d (MV: %s) ===" % (self.key, self.mv))
        return "\n".join(buf[::-1])


class RoutingTableSingleLevel:
    def __init__(self, own_key: int, level: int):
        self.own_key: int = own_key
        self.neighbors: list[Optional[List[SGNode]]] = [[], []]
        self.level = level

    def is_empty(self) -> bool:
        return all(not nb for nb in self.neighbors)

    def __str__(self) -> str:
        return "Level %d: LEFT=%s, RIGHT=%s" % (self.level, str(self.neighbors[LEFT]), str(self.neighbors[RIGHT]))
