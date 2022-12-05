from typing import List, Dict

from descan.core.content import Content


class ContentDatabase:

    def __init__(self):
        self.content: Dict[bytes, Content] = {}

    def add_content(self, content: Content):
        self.content[content.identifier] = content

    def has_content(self, content_hash: bytes) -> bool:
        return content_hash in self.content

    def get_content(self, content_hash: bytes):
        return self.content[content_hash] if content_hash in self.content else None

    def get_all_content(self) -> List[Content]:
        return list(self.content.values())

    def size(self) -> int:
        return len(self.content)
