from __future__ import annotations

from descan.skipgraph.membership_vector import MembershipVector
from descan.skipgraph.payload import NodeInfoPayload

from ipv8.peer import Peer
from ipv8.types import Address


class SGNode:
    """
    Represents a node in the Skip Graph.
    """
    def __init__(self, address: Address, public_key: bytes, key: int, mv: MembershipVector):
        self.address: Address = address
        self.public_key: bytes = public_key
        self.key = key
        self.mv = mv

    @staticmethod
    def from_payload(payload) -> SGNode:
        return SGNode(payload.address, payload.public_key, payload.key, MembershipVector.from_bytes(payload.mv))

    @staticmethod
    def empty() -> SGNode:
        return SGNode(("0.0.0.0", 0), b"", 0, MembershipVector.from_bytes(b""))

    def is_empty(self) -> bool:
        return len(self.public_key) == 0

    def get_peer(self) -> Peer:
        return Peer(self.public_key, address=self.address)

    def to_payload(self) -> NodeInfoPayload:
        return NodeInfoPayload(self.address, self.public_key, self.key, self.mv.to_bytes())

    def __str__(self):
        return f"Node({self.key} => address: {self.address})"

    def __repr__(self):
        return f"Node(key={self.key}, mv={self.mv})"

    def __eq__(self, other):
        return other.key == self.key

    def __hash__(self):
        return self.key
