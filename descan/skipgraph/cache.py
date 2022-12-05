from asyncio import Future, get_event_loop

from descan.skipgraph.node import SGNode
from descan.skipgraph.payload import SearchPayload

from ipv8.requestcache import RandomNumberCache
from ipv8.types import Peer


class NeighbourRequestCache(RandomNumberCache):

    def __init__(self, community):
        super().__init__(community.request_cache, "neighbour")
        self.future = Future()


class LinkRequestCache(RandomNumberCache):

    def __init__(self, community):
        super().__init__(community.request_cache, "link")
        self.future = Future()


class BuddyCache(RandomNumberCache):

    def __init__(self, community):
        super().__init__(community.request_cache, "buddy")
        self.future = Future()


class SearchRequestCache(RandomNumberCache):

    def __init__(self, community):
        super().__init__(community.request_cache, "search")
        self.future = Future()
        self.start_time = get_event_loop().time()

    @property
    def timeout_delay(self):
        return 20.0

    def on_timeout(self):
        self.future.set_result(None)


class SearchForwardRequestCache(RandomNumberCache):
    """
    Cache to keep track of search forwards.
    """
    SEARCH_TIMEOUT = 1.0

    def __init__(self, community, payload: SearchPayload, from_peer: Peer, to_node: SGNode):
        super().__init__(community.request_cache, "forward-search")
        self.community = community
        self.payload = payload
        self.from_peer: Peer = from_peer
        self.to_node: SGNode = to_node

    @property
    def timeout_delay(self):
        return self.SEARCH_TIMEOUT

    def on_timeout(self):
        self.community.on_search_forward_timeout(self)


class DeleteCache(RandomNumberCache):

    def __init__(self, community):
        super().__init__(community.request_cache, "delete")
        self.future = Future()


class SetNeighbourNilCache(RandomNumberCache):

    def __init__(self, community):
        super().__init__(community.request_cache, "set-neighbour-nil")
        self.future = Future()


class FindNewNeighbourCache(RandomNumberCache):

    def __init__(self, community):
        super().__init__(community.request_cache, "find-new-neighbour")
        self.future = Future()
