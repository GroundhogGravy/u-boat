import random as __random
import binascii as __binascii

def random_pw(byte_len):
    """Generates a non-memorable, ascii-only password using `byte_len`
    bytes read from /dev/urandom

    """
    
    bs = __random._urandom(byte_len)
    
    # don't add newlines to generated ascii
    return __binascii.b2a_base64(bs, newline=False).decode("ascii")


if __name__ == "__main__":
    for i in range(1, 11):
        print(random_pw(i * 10))
