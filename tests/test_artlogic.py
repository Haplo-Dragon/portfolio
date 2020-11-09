import artlogic.artlogic as artlogic
import pytest


@pytest.mark.parametrize(
    "example, expected",
    [
        ("A", "16777217"),
        ("FRED", "251792692"),
        (" :^)", "79094888"),
        ("foo", "124807030"),
        (" foo", "250662636"),
        ("foot", "267939702"),
        ("BIRD", "251930706"),
        ("....", "15794160"),
        ("^^^^", "252706800"),
        ("Woot", "266956663"),
        ("no", "53490482"),
        ("tacocat", "267487694 125043731"),
        ("never odd or even", "267657050 233917524 234374596 250875466 17830160"),
        ("lager, sir, is regal", "267394382 167322264 66212897 200937635 267422503"),
        (
            "go hang a salami, I'm a lasagna hog",
            "200319795 133178981 234094669 267441422 78666124 99619077 "
            + "267653454 133178165 124794470",
        ),
        (
            "egad, a base tone denotes a bad age",
            "267389735 82841860 267651166 250793668 233835785 267665210 "
            + "99680277 133170194 124782119",
        ),
    ],
)
def test_handleData(example, expected):
    """
    Does handleData() correctly distinguish between strings and lists of
    integers?
    """
    assert artlogic.handleData(example) == expected
    assert artlogic.handleData(expected) == example


def test_handleData_too_long_integer():
    """
    Does handleData() correctly interpret integers over 32 bits as strings?
    """
    over_32_bits = 1659684413514848461451648
    assert over_32_bits.bit_length() > 32
    assert (
        artlogic.handleData(str(over_32_bits))
        == "16746029 16723216 16712751 16753920 16714532 16715075 1118208"
    )
