from asyncio import Future, ensure_future, get_event_loop
from typing import Dict, Tuple, Set

from descan.skipgraph.cache import SearchRequestCache
from descan.skipgraph.node import SGNode

from ipv8.requestcache import RandomNumberCache
from ipv8.util import succeed


class StorageRequestCache(RandomNumberCache):

    def __init__(self, community):
        super().__init__(community.request_cache, "store")
        self.future = Future()


class TripletsRequestCache(RandomNumberCache):

    def __init__(self, community):
        super().__init__(community.request_cache, "triplets")
        self.future = Future()

    @property
    def timeout_delay(self):
        return 5.0

    def on_timeout(self):
        self.future.set_result(None)


class EdgeSearchCache(RandomNumberCache):

    def __init__(self, community, content_hash: bytes):
        super().__init__(community.request_cache, "edge-search")
        self.community = community
        self.content_hash: bytes = content_hash
        self.sg_searches: Dict[Tuple[int, int], Future] = {}
        self.pending_triplets_requests: Dict[int, Future] = {}
        self.completed_triplets_requests: Set[int] = set()
        self.sg_search_results: Set[SGNode] = set()
        self.node_key_to_sg_search: Dict[int, Tuple[int, int]] = {}
        self.future = Future()

        # Request latencies
        self.sg_searches_times: Dict[Tuple[int, int], float] = {}
        self.sg_searches_start_times: Dict[Tuple[int, int], float] = {}
        self.triplets_requests_start_times: Dict[int, float] = {}

        self.latency = (-1, -1)  # The final latency for the SG search and triplets request

    def on_triplet_request_result(self, key: int, result: Future):
        triplets = result.result()
        self.pending_triplets_requests.pop(key)
        self.completed_triplets_requests.add(key)
        if triplets and not self.future.done():
            # Compute the final latency of this (successful) search
            triplets_request_time = get_event_loop().time() - self.triplets_requests_start_times[key]
            sg_ind, key = self.node_key_to_sg_search[key]
            sg_search_time = self.sg_searches_times[(sg_ind, key)]
            self.latency = (sg_search_time, triplets_request_time)

            # Complete the search
            self.future.set_result(triplets)

        self.check_search_finished()

    def check_search_finished(self):
        """
        Check whether the search is finished (e.g., there are no outstanding SG searches/triplet requests).
        """
        if not self.sg_searches and not self.pending_triplets_requests and not self.future.done():
            self.future.set_result([])

    def on_skip_graph_result(self, sg_ind: int, key: int, result: Future):
        sg_search_time = get_event_loop().time() - self.sg_searches_start_times[(sg_ind, key)]
        self.sg_searches.pop((sg_ind, key))
        self.sg_searches_times[(sg_ind, key)] = sg_search_time
        node: SGNode = result.result()
        if not node:
            # The search failed to return anything useful
            self.check_search_finished()
            return

        if node.key not in self.node_key_to_sg_search:
            # Record which skip graph search resulted in this node - used to track E2E latency of edge searches.
            self.node_key_to_sg_search[node.key] = (sg_ind, key)

        if node.key not in self.pending_triplets_requests and node.key not in self.completed_triplets_requests:
            # Perform a triplets request
            if node.key == self.community.get_sg_key():
                triplets_request_future: Future = Future()
                triplets_request_future.add_done_callback(lambda r: self.on_triplet_request_result(node.key, r))
                self.pending_triplets_requests[node.key] = triplets_request_future
                self.triplets_requests_start_times[node.key] = get_event_loop().time()
                triplets = self.community.knowledge_graph.get_triplets_of_node(self.content_hash)
                triplets_request_future.set_result(triplets)
            else:
                triplets_request_future: Future = ensure_future(self.community.request_triplets(node, self.content_hash))
                triplets_request_future.add_done_callback(lambda r: self.on_triplet_request_result(node.key, r))
                self.pending_triplets_requests[node.key] = triplets_request_future
                self.triplets_requests_start_times[node.key] = get_event_loop().time()

        self.check_search_finished()

    def perform_search(self, sg_ind: int, key: int):
        cache: SearchRequestCache = SearchRequestCache(self.community.skip_graphs[sg_ind])
        search_future = ensure_future(self.community.skip_graphs[sg_ind].search(key, cache=cache))
        search_future.add_done_callback(lambda r: self.on_skip_graph_result(sg_ind, key, r))
        self.sg_searches[(sg_ind, key)] = search_future
        self.sg_searches_start_times[(sg_ind, key)] = get_event_loop().time()
        self.community.sg_identifiers_for_edge_searches[self.number].add(cache.number)

    @property
    def timeout_delay(self):
        return 60.0

    def on_timeout(self):
        self.future.set_result([])
