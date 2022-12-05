import pytest

from descan.core.db.knowledge_graph import KnowledgeGraph
from descan.core.db.triplet import Triplet


@pytest.fixture
def knowledge_graph():
    return KnowledgeGraph()


def test_add_triplet(knowledge_graph):
    knowledge_graph.add_triplet(Triplet(b"a", b"b", b"c"))
    assert knowledge_graph.get_num_edges() == 1


def test_get_triplets_of_node(knowledge_graph):
    assert not knowledge_graph.get_triplets_of_node(b"abc")

    knowledge_graph.add_triplet(Triplet(b"a", b"b", b"c"))
    triplets = knowledge_graph.get_triplets_of_node(b"a")
    assert len(triplets) == 1
    assert triplets[0].head == b"a"
    assert triplets[0].relation == b"b"
    assert triplets[0].tail == b"c"

    # Add an edge in the other direction
    knowledge_graph.add_triplet(Triplet(b"c", b"b", b"a"))
    triplets = knowledge_graph.get_triplets_of_node(b"a")
    assert len(triplets) == 2


def test_get_storage_costs(knowledge_graph):
    knowledge_graph.add_triplet(Triplet(b"a", b"b", b"c"))
    s1 = knowledge_graph.get_storage_costs()
    assert s1

    knowledge_graph.add_triplet(Triplet(b"abc", b"def", b"ghi"))
    s2 = knowledge_graph.get_storage_costs()
    assert s2 > s1
