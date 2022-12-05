from binascii import hexlify
from typing import Set

from descan.core.content import Content
from descan.core.rules.rule import Rule
from descan.core.db.triplet import Triplet


class DummyRule(Rule):
    """
    A dummy rule that generates fixed edges. Useful for testing.
    """
    RULE_NAME = b"DUMMY"

    def apply_rule(self, content: Content) -> Set[Triplet]:
        return {Triplet(hexlify(content.identifier), b"a", b"b")}
