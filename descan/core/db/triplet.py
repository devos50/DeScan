from typing import List

from descan.core.payloads import TripletPayload, RulePayload


class Triplet:

    def __init__(self, head: bytes, relation: bytes, tail: bytes):
        self.head: bytes = head
        self.relation: bytes = relation
        self.tail: bytes = tail
        self.rules: List[bytes] = []  # The rules that generated the triplet

    def add_rule(self, rule: bytes) -> None:
        self.rules.append(rule)

    def to_payload(self) -> TripletPayload:
        rules = [RulePayload(rule_name) for rule_name in self.rules]
        payload = TripletPayload(self.head, self.relation, self.tail, rules)
        return payload

    @staticmethod
    def from_payload(payload: TripletPayload):
        triplet = Triplet(payload.head, payload.relation, payload.tail)
        triplet.rules = [pl.rule for pl in payload.rules]
        return triplet

    def __str__(self) -> str:
        return "<%s, %s, %s>" % (self.head.decode(), self.relation.decode(), self.tail.decode())

    def __eq__(self, other):
        return self.head == other.head and self.relation == other.relation and self.tail == other.tail

    def __hash__(self):
        return hash(self.head + self.relation + self.tail)
