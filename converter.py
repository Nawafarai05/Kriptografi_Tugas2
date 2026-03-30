import os

# konversi antara string (pesan) menjadi bits, dan sebaliknya
def string_to_bits(string):
    return''.join(format(ord(char), '08b') for char in string)

def bits_to_string(bits):
    chars = [bits[i:i+8] for i in range(0, len(bits), 8)]
    return ''.join(chr(int(char,2)) for char in chars)

# fungsi untuk menentukan posisi bit yang diubah dalam lsb
def set_n_lsb(value, bits, n) :
    mask = (1 << n) - 1
    value = value & (255 - mask)
    value = value | int(bits, 2)
    return value

def get_n_lsb(value, n) :
    return format(value & ((1 << n) - 1), f'0{n}b')

# mengubah berkas file menjadi bits dan sebaliknya
def file_to_bits(filename) :
    with open(filename, 'rb') as f:
        data = f.read()

    bits = ''.join(format(byte, '08b') for byte in data)
    return bits

def bits_to_file(bits, output_filename) :
    bytes_data = bytearray()

    for i in range(0, len(bits), 8):
        byte = bits[i:i+8]
        bytes_data.append(int(byte, 2))

    with open(output_filename, 'wb') as f:
        f.write(bytes_data)

# mengambil bagian extension berkas file
def get_extension(filename) :
    return os.path.splitext(filename)[1]

# mengubah bit pesan menjadi byte dan sebalikanya
def bits_to_bytes(bits) :
    return bytes(int(bits[i:i+8], 2) for i in range(0, len(bits), 8))

def bytes_to_bits(data) :
    return ''.join(format(b, '08b') for b in data)

# mengubah key untuk enkripsi ke dalam bit
def key_to_seed(key) :
    seed = 0
    for char in key :
        seed = seed * 31 + ord(char)
    return seed

def key_to_64bit(key) :
    seed = key_to_seed(key)
    return format(seed, '064b')[:64]
