from typing import List

from ipv8.messaging.payload_dataclass import dataclass


@dataclass
class RulePayload:
    rule: bytes


@dataclass
class TripletPayload:
    head: bytes
    relation: bytes
    tail: bytes
    rules: List[RulePayload]


@dataclass
class TripletsPayload:
    triplets: List[TripletPayload]


@dataclass(msg_id=21)
class StorageRequestPayload:
    identifier: int
    content_identifier: bytes
    key: int


@dataclass(msg_id=22)
class StorageResponsePayload:
    identifier: int
    response: bool


@dataclass(msg_id=23)
class TripletsRequestPayload:
    identifier: int
    content: bytes
