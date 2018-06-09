import pytest
from lament_mod import tools


@pytest.mark.parametrize("equip_list, equip_type", [
    (['stuff', 'things', 'more_stuff'], "NonEnc"),
    (['foo', 'bar', 'foobar'], "Normal"),
    (['Shield', 'Giant pole', 'ROUS'], "Oversized")])
def test_generate_dict(equip_list, equip_type):
    equip_dict = tools.generate_dict(equip_list, equip_type)
    assert type(equip_dict) is dict
    for item in equip_dict.items():
        assert equip_type in item[0]
