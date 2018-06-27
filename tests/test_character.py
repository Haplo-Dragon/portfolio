import pytest


@pytest.mark.parametrize("character_class, expected_alignment", [
    ("Halfling", None),
    ("Cleric", "Lawful"),
    ("Magic-User", "Chaotic"),
    ("Elf", "Chaotic")])
def test_align(halfling, character_class, expected_alignment):
    """Is alignment assigned correctly based on class?"""
    alignment = halfling.align(character_class)
    assert alignment == expected_alignment
