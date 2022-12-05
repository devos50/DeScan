"""
Copied and adapted from https://github.com/abelab/sgsim/blob/main/src/sg.py.
"""
from __future__ import annotations

import random
from typing import Optional, List

ALPHA = 2  # base of a membership vector


class MembershipVector:
    LENGTH = 32

    def __init__(self, value: Optional[List[int]] = None):
        self.val: list[int] = value or []
        if value is None:
            for i in range(MembershipVector.LENGTH):
                self.val.append(random.randint(0, ALPHA - 1))

    def to_bytes(self) -> bytes:
        return bytes(self.val)

    @staticmethod
    def from_bytes(bytes_data: bytes) -> MembershipVector:
        return MembershipVector([int(b) for b in bytes_data])

    def __str__(self):
        return "".join(map(str, self.val))
