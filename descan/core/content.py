import hashlib
from typing import List, Optional


class Content:
    custom_keys: Optional[List[int]] = None  # For testing purposes

    def __init__(self, identifier: bytes, data: bytes) -> None:
        self.identifier: bytes = identifier
        self.data: bytes = data

    @staticmethod
    def get_keys(identifier: bytes, num_keys: int = 1) -> List[int]:
        """
        Return the keys of this content item, an integer between 0 and 2^32.
        We can generate multiple keys, e.g., when we want to store this content at multiple nodes.
        """
        if Content.custom_keys:
            return Content.custom_keys

        keys: List[int] = []
        for ind in range(num_keys):
            h = hashlib.sha1()
            h.update(identifier)
            h.update(b"%d" % ind)
            keys.append(int.from_bytes(h.digest(), 'big') % (2 ** 32))

        return keys

    @staticmethod
    def verify_key(content_identifier: bytes, content_key: int, replication_factor: int) -> bool:
        for ind in range(replication_factor):
            h = hashlib.sha1()
            h.update(content_identifier)
            h.update(b"%d" % ind)
            derived_key = int.from_bytes(h.digest(), 'big') % (2 ** 32)
            if derived_key == content_key:
                return True
        return False
