import sys


MAX_LENGTH = 4
BIT_SHIFT = 4


def encode(string):
    """
    Encode the given string into a list of 32-bit integers according to the
    scheme in the specification. Returns a list of 32-bit integers.
    """
    integers = []

    # Break the string into chunks of MAX_LENGTH characters or less, then
    # encode each chunk.
    for str_chunk in chunk(string, MAX_LENGTH):
        integers.append(_encode(str_chunk))

    return integers


def _encode(string):
    """
    Encode a 0-MAX_LENGTH character string into a 32-bit integer according to
    the scheme in the specification. Returns a 32-bit integer.
    """
    if len(string) > MAX_LENGTH:
        raise ValueError("Can only encode strings of 0-{} characters.".format(MAX_LENGTH))

    # Get a byte array from the given string.
    # We're using the default encoding of UTF-8 because it matches the examples
    # given in the specification.
    byte_values = string.encode()

    # Take each byte and distribute its bits along the 32-bit result at
    # BIT_SHIFT length intervals.
    result = 0
    for i in range(len(byte_values)):
        current_byte = byte_values[i]
        bit_pos = i

        while current_byte:
            # Get the lowest-order bit from the current byte.
            current_bit = current_byte & 1
            # If the current bit is 1, set the corresponding bit in the result.
            # Otherwise, we can leave the result bit as 0.
            if current_bit:
                result = setBit(result, bit_pos)

            # Shift the lowest-order bit off the end.
            current_byte >>= 1
            # Move BIT_SHIFT bits along the result.
            bit_pos += BIT_SHIFT

    return result


def decode(integers):
    """
    Decode the given list of 32-bit integers into a string according to the
    scheme in the specification. Returns a string.
    """
    string_chunks = []

    # Each 32-bit integer represents a 0-MAX_LENGTH character chunk of the
    # original input string.
    for integer in integers:
        string_chunks.append(_decode(integer))

    return "".join(string_chunks)


def _decode(integer):
    """
    Decode the given 32-bit integer into a MAX_LENGTH character string according
    to the scheme in the specification. Returns a string.
    """
    if integer.bit_length() > 32:
        raise ValueError("Can only decode 32-bit integers.")

    decoded_int = 0

    # Since each byte has its bits distributed along the given integer at
    # BIT_SHIFT intervals, we'll get the bits from one byte at a time.
    for input_start in range(4):
        # Move to the beginning of the correct output byte.
        output_pos = input_start * 8

        # Read the bits from the input at BIT_SHIFT intervals, lowest-order
        # bits first.
        for input_bit in range(input_start, integer.bit_length(), BIT_SHIFT):
            current_bit = getBit(integer, input_bit)
            # If the current bit is 1, set the corresponding bit in the result.
            # Otherwise, we can leave the result bit as 0.
            if current_bit:
                decoded_int = setBit(decoded_int, output_pos)
            # Move to the next position in the output byte.
            output_pos += 1

    # Get a byte array from the decoded integer. We're reversing the byte order
    # because we read the input integer from lowest-order bit to highest-order.
    decoded_bytes = decoded_int.to_bytes(4, byteorder="little")

    # Get the characters represented by each byte, ignoring empty bytes.
    chars = []
    for byte in decoded_bytes:
        if byte:
            chars.append(chr(byte))

    return "".join(chars)


def getBit(num, n):
    """
    Return the nth bit (0-indexed) of num.
    """
    shifted = num >> n
    return shifted & 1


def setBit(num, n):
    """
    Return num with the nth bit set to 1.
    """
    # Make a mask of all 0s with the nth bit set to 1.
    mask = 1 << n
    return num | mask


def chunk(string, n):
    """
    Split string into chunks of length <= n. Returns a generator.
    """
    for i in range(0, len(string), n):
        yield string[i : i + n]


if __name__ == "__main__":
    if len(sys.argv) > 1:
        print(encode(sys.argv[1]))
