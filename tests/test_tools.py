import pytest
import math
from lament_mod import tools


@pytest.mark.parametrize("equip_list, equip_type", [
    (['stuff', 'things', 'more_stuff'], "NonEnc"),
    (['foo', 'bar', 'foobar'], "Normal"),
    (['Shield', 'Giant pole', 'ROUS'], "Oversized")])
def test_add_PDF_field_names(equip_list, equip_type):
    equip_dict = tools.add_PDF_field_names(equip_list, equip_type)
    assert isinstance(equip_dict, dict)
    for prefix in equip_dict.keys():
        assert equip_type in prefix


@pytest.mark.parametrize("modifiers", [
    {'STR': '0', 'DEX': '0', 'CON': '0', 'INT': '0', 'WIS': '0', 'CHA': '0'},
    {'STR': '-1', 'DEX': '-2', 'CON': '-1', 'INT': '-2', 'WIS': '0', 'CHA': '-1'},
    {'STR': '+1', 'DEX': '+2', 'CON': '+1', 'INT': '+2', 'WIS': '+1', 'CHA': '0'},
    {'STR': '-2', 'DEX': '+3', 'CON': '0', 'INT': '0', 'WIS': '+1', 'CHA': '-1'},
    {'STR': '+1', 'DEX': '+1', 'CON': '+1', 'INT': '+1', 'WIS': '+1', 'CHA': '+1'}])
def test_clear_mod_zeroes(modifiers):
    zeroes_cleared = tools.clear_mod_zeroes(modifiers)
    assert '0' not in zeroes_cleared.values()


@pytest.mark.parametrize("pcClass, expected", [
    ('Magic-User', 'Summon'),
    ('Cleric', 'Bless'),
    ('Elf', 'Read Magic')])
def test_create_spell_list(pcClass, expected):
    spell_list = tools.create_spell_list([], pcClass, level=1)
    assert expected in spell_list
    assert "Magic Missle" not in spell_list


@pytest.mark.parametrize("filename, prefix, does_not_belong, splitter", [
    (tools.OVERSIZED_ITEMS, "Over", "Tiny Kitten", tools.split_over),
    (tools.TINY_ITEMS, "NonEnc", "Full-size Tiger", tools.split_tiny)])
def test_split_over_and_tiny(filename, prefix, does_not_belong, splitter):
    """Are we splitting oversized/tiny items from a list and returning a prefixed dict?"""
    with open(filename, 'r') as file:
        to_be_split = file.read().splitlines()
    to_be_split.append(does_not_belong)
    to_be_split, split_items = splitter(to_be_split)
    assert isinstance(split_items, dict)
    for key, value in split_items.items():
        assert prefix in key
        assert value not in to_be_split
    assert does_not_belong in to_be_split


@pytest.mark.parametrize("money", ["1 sp 11 Cp", "1 Cp"])
def test_split_money(money):
    """Are we splitting money from a list and returning two lists?"""
    equipment = ["Hitchhiker's Guide to the Galaxy", "Towel"]
    equipment.append(money)
    equipment, money = tools.split_money(equipment)
    for item in equipment:
        assert ' Cp' not in item
        assert ' sp' not in item
    for item in money:
        assert item.find(' Cp') or item.find(' sp')


def test_get_encumbrance(normal_equipment, oversized_equipment):
    """Is encumbrance calculated correctly for normal and oversized items?"""
    encumbrance = tools.get_encumbrance(
        normal_equipment,
        oversized_equipment,
        pc_class="Dwarf")
    assert encumbrance >= 0
    assert encumbrance == 5


@pytest.mark.parametrize("level", list(range(2, 21)))
def test_list_number_of_random_spells_by_level(level):
    """Are the number of random spells Magic-Users must add calculated correctly?"""
    highest_spell_level = min(math.ceil(level / 2), 9)

    number_of_spells_by_level = [0 for i in range(highest_spell_level)]
    number_of_spells_by_level = tools.list_number_of_random_spells_by_level(
        number_of_spells_by_level,
        level)

    # Always ONE level 1 spell
    assert number_of_spells_by_level[0] == 1
    # Always TWO of every spell level except the last (highest)
    for item in number_of_spells_by_level[1:-1]:
        assert item == 2

    # Even levels (other than 2) below 19 have TWO spells of the highest level,
    # odd levels have ONE.
    if 2 < level < 19:
        if level % 2 == 0:
            assert number_of_spells_by_level[-1] == 2
        else:
            assert number_of_spells_by_level[-1] == 1

    # Levels 19 and 20 are special cases - they each add ONE to the highest spell level.
    elif level > 19:
        assert number_of_spells_by_level[-1] == 2 + (level - 18)
