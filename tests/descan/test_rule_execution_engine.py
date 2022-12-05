import pytest

from descan.core.content import Content
from descan.core.db.content_database import ContentDatabase
from descan.core.db.knowledge_graph import KnowledgeGraph
from descan.core.db.rules_database import RulesDatabase
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


def test_dummy_rule(rule_execution_engine):
    rule_execution_engine.start()
    assert rule_execution_engine.knowledge_graph.get_num_edges() == 2
