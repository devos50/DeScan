from asyncio import Future
from binascii import hexlify
from typing import List

import pytest

from descan.core.content import Content
from descan.core.db.content_database import ContentDatabase
from descan.core.db.knowledge_graph import KnowledgeGraph
from descan.core.db.rules_database import RulesDatabase
from descan.core.db.triplet import Triplet
from descan.core.rule_execution_engine import RuleExecutionEngine
from descan.core.rules.dummy import DummyRule


@pytest.fixture
def content_db():
    db = ContentDatabase()

    # Add some content
    db.add_content(Content(b"a", b"test1"))
    db.add_content(Content(b"b", b"test2"))
    return db


@pytest.fixture
def rules_db():
    db = RulesDatabase()
    db.add_rule(DummyRule())
    return db


@pytest.fixture
def knowledge_graph():
    kg = KnowledgeGraph()
    return kg


@pytest.fixture
def rule_execution_engine(content_db, rules_db, knowledge_graph):
    return RuleExecutionEngine(content_db, rules_db, knowledge_graph, None)


@pytest.mark.asyncio
@pytest.mark.timeout(3)
async def test_dummy_rule(rule_execution_engine):
    """
    Test a very simple dummy rule.
    """
    test_future: Future = Future()

    def on_result(content: Content, triplets: List[Triplet]):
        on_result.triplets_generated += triplets
        if len(on_result.triplets_generated) == 2:
            identifiers: List[bytes] = []
            for triplet in on_result.triplets_generated:
                identifiers.append(triplet.head)
            assert hexlify(b"a") in identifiers
            assert hexlify(b"b") in identifiers
            test_future.set_result(None)

    on_result.triplets_generated = []
    rule_execution_engine.callback = on_result
    rule_execution_engine.start(0.1)
    await test_future
