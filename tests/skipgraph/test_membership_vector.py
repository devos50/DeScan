import pytest

from descan.skipgraph.membership_vector import MembershipVector


@pytest.fixture
def membership_vector() -> MembershipVector:
    return MembershipVector()


def test_init(membership_vector):
    assert membership_vector.val
    assert len(membership_vector.val) == MembershipVector.LENGTH

    # Custom initialization
    vector = MembershipVector([0, 0, 0, 0, 0, 1])
    assert vector.val[5] == 1  # This bit should be set


def test_to_bytes(membership_vector):
    assert isinstance(membership_vector.to_bytes(), bytes)
    assert len(membership_vector.to_bytes()) == membership_vector.LENGTH


def test_from_bytes():
    mv = MembershipVector.from_bytes(b"\x00\x01\x00\x01")
    assert mv.val[0] == 0
    assert mv.val[1] == 1
    assert mv.val[2] == 0
    assert mv.val[3] == 1


def test_str(membership_vector):
    assert isinstance(str(membership_vector), str)
