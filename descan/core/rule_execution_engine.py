import random
from asyncio import ensure_future
from typing import List, Callable

from descan.core.content import Content

from ipv8.taskmanager import TaskManager
from ipv8.types import PrivateKey
from ipv8.util import maybe_coroutine


class RuleExecutionEngine(TaskManager):

    def __init__(self, content_db, rules_db, key: PrivateKey, callback: Callable):
        super().__init__()
        self.content_db = content_db
        self.rules_db = rules_db
        self.key = key
        self.process_queue: List[Content] = []
        self.callback: Callable = callback

    def start(self, process_interval: float = 1):
        # Put existing content in the process queue
        all_content = self.content_db.get_all_content()
        random.shuffle(all_content)
        for content in all_content:
            self.process_queue.append(content)

        self.register_task("process", self.process, interval=process_interval)

    def shutdown(self):
        self.cancel_all_pending_tasks()

    def process(self):
        # Take one item from the queue and apply the rules
        if not self.process_queue:
            return

        content = self.process_queue.pop()
        triplets = []
        for rule in self.rules_db.get_all_rules():
            rule_triplets = rule.apply_rule(self, content)
            for triplet in rule_triplets:
                triplet.add_rule(rule.RULE_NAME)
            triplets += rule_triplets

        # TODO we should probably create a Merkle root hash here

        # Invoke the callback with the new rules
        ensure_future(maybe_coroutine(self.callback, content, triplets))
