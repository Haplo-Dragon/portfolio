import artlogic.encode as encode
import pytest


@pytest.mark.parametrize("example, expected", [
    ("A", 16777217),
    ("FRED", 251792692),
    (" :^)", 79094888),
    ("foo", 124807030),
    (" foo", 250662636),
    ("foot", 267939702),
    ("BIRD", 251930706),
    ("....", 15794160),
    ("^^^^", 252706800),
    ("Woot", 266956663),
    ("no", 53490482)])
def test_given_examples_part_1(example, expected):
    """
    Do the example strings given in part 1 of the specification output the
    correct integers, and vice versa?
    """
    assert encode.encode(example)[0] == expected
    assert encode.decode([expected]) == example
    # Does encoding and then decoding give us back the same string?
    assert example == encode.decode(encode.encode(example))


@pytest.mark.parametrize("example, expected", [
    ("tacocat",
        [267487694, 125043731]),
    ("never odd or even",
        [267657050, 233917524, 234374596, 250875466, 17830160]),
    ("lager, sir, is regal",
        [267394382, 167322264, 66212897, 200937635, 267422503]),
    ("go hang a salami, I'm a lasagna hog",
        [200319795, 133178981, 234094669, 267441422, 78666124, 99619077,
         267653454, 133178165, 124794470]),
    ("egad, a base tone denotes a bad age",
        [267389735, 82841860, 267651166, 250793668, 233835785, 267665210,
         99680277, 133170194, 124782119])])
def test_given_examples_part_2(example, expected):
    """
    Do the example integers and strings given in part 2 of the specification
    output the correct values in both directions (encode and decode)?
    """
    assert encode.encode(example) == expected
    assert encode.decode(expected) == example
    # Does encoding and then decoding give us back the same string?
    assert example == encode.decode(encode.encode(example))


def test_too_long_integer():
    """
    Does the decoding process correctly handle integers over 32 bits in length?
    """
    over_32_bits = 1659684413514848461451648
    assert over_32_bits.bit_length() > 32
    with pytest.raises(ValueError):
        encode.decode([over_32_bits])


def test_chunk():
    """
    Does chunk() divide a string into chunks of the correct size without
    modifying it?
    """
    string = "This must be Thursday. I never could get the hang of Thursdays."
    result = []
    for chunk in encode.chunk(string, 4):
        assert len(chunk) <= 4
        result.append(chunk)

    assert string == ''.join(result)


def test_setBit():
    """
    Does setBit() set the correct bit in a number, regardless of the bit's
    previous value?
    """
    num = 0
    assert encode.setBit(num, 3) == 8

    num = 8
    assert encode.setBit(num, 3) == 8
    assert encode.setBit(num, 2) == 12


def test_getBit():
    """
    Does getBit() return the nth bit of a number?
    """
    num = 32
    for i in range(5):
        assert encode.getBit(num, i) == 0
    assert encode.getBit(num, 5) == 1
    num += 1
    assert encode.getBit(num, 0) == 1
