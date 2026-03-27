import cv2
import numpy as np

# konversi antara string (pesan) menjadi bits, dan sebaliknya
def string_to_bits(string):
    return''.join(format(ord(char), '08b') for char in string)

def bits_to_string(bits):
    chars = [bits[i:i+8] for i in range(0, len(bits), 8)]
    return ''.join(chr(int(char,2)) for char in chars)

def set_n_lsb(value, bits, n) :
    mask = (1 << n) - 1
    value = value & (255 - mask)
    value = value | int(bits, 2)
    return value

def get_n_lsb(value, n) :
    return format(value & ((1 << n) - 1), f'0{n}b')

# embedding pesan ke dalam video secara sequential
def embed_video(input_video, output_video, message, scheme) :
    capture = cv2.VideoCapture(input_video)

    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = capture.get(cv2.CAP_PROP_FPS)

    # codec menggunakan yang lossless atua minim komporesi
    fourcc = cv2.VideoWriter_fourcc(*'HFYU')
    out = cv2.VideoWriter(output_video, fourcc, fps, (width, height))

    r_n, g_n, b_n = scheme

    # mengubah message jadi bits
    message_bits = string_to_bits(message)
    length_bits = format(len(message_bits), '032b')
    full_bits = length_bits + message_bits

    total_bits = len(full_bits)
    bit_idx = 0
    max_capacity = 0

    while True:
        ret, frame = capture.read()
        if not ret :
            break

        height, width, _ = frame.shape
        max_capacity += height * width * 8

        for i in range(height) :
            for j in range(width) :
                if bit_idx + 8 <= total_bits :
                    chunk = full_bits[bit_idx:bit_idx + 8]

                    r_bits = chunk[0:r_n]
                    g_bits = chunk[r_n:r_n + g_n]
                    b_bits = chunk[r_n + g_n:r_n + g_n + b_n]

                    frame[i, j][0] = set_n_lsb(frame[i, j][0], r_bits, r_n)
                    frame[i, j][1] = set_n_lsb(frame[i, j][1], g_bits, g_n)
                    frame[i, j][2] = set_n_lsb(frame[i, j][2], b_bits, b_n)

                    bit_idx += 8

                if bit_idx >= total_bits :
                    break

        out.write(frame)

    capture.release()
    out.release()

    print("Scheme digunakan: ", scheme)
    print("Total capacity:", max_capacity, "bits")
    print("Message size:", total_bits, "bits")

    if total_bits > max_capacity : 
        print("Kapasitas berlebih!")
    else :
        print("(Sequencial) Embeding selesai!")

# mengekstrak video 
def extract_video(stego_video, scheme) :
    capture = cv2.VideoCapture(stego_video)

    r_n, g_n, b_n = scheme

    bits = ""
    length = None
    total_needed = None # panjang total bit yang harus diambil dari video

    while True :
        ret, frame = capture.read()
        if not ret :
            break

        height, width, _ = frame.shape

        for i in range(height) :
            for j in range(width) :
                r_bits = get_n_lsb(frame[i, j][0], r_n)
                g_bits = get_n_lsb(frame[i, j][1], g_n)
                b_bits = get_n_lsb(frame[i, j][2], b_n)

                bits += r_bits + g_bits + b_bits

                # mengambil panjang pesan 32 bit
                if length is None and len(bits) >= 32:
                    length = int(bits[:32], 2)
                    total_needed = 32 + length
                    print("DEBUG length :", length)

                # kalau sudah, distop
                if total_needed is not None and len(bits) >= total_needed:
                    capture.release()

                    message_bits = bits[32:32+length]
                    message_bits = message_bits[:len(message_bits)//8 * 8]

                    return bits_to_string(message_bits)

    capture.release()
    return ""

# testing
if __name__ == "__main__":
    input_video = "input.avi"
    output_video = "output.avi"
    message = "Ini dia hasil dari stegovideo anjay anjay anjay!"
    scheme_input = input("Scheme (contoh 3,3,2): ")
    scheme = tuple(map(int, scheme_input.split(',')))

    embed_video(input_video, output_video, message, scheme)

    result = extract_video(output_video, scheme)
    print("Extracted message :", result)
