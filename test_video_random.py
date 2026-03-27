import cv2
import numpy as np
import random
from test_video import string_to_bits, bits_to_string, set_n_lsb, get_n_lsb

def get_pixels(idx, width) :
    i = idx // width
    j = idx % width
    return i, j

# embedding pesan ke dalam video secara random berdasarkan seeds dari stego key
def embed_video_random(input_video, output_video, message, stego_key, scheme) :
    capture = cv2.VideoCapture(input_video)

    r_n, g_n, b_n = scheme

    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = capture.get(cv2.CAP_PROP_FPS)

    fourcc = cv2.VideoWriter_fourcc(*'HFYU')
    out = cv2.VideoWriter(output_video, fourcc, fps, (width, height))

    # mengubah message menjadi bits
    message_bits = string_to_bits(message)
    length_bits = format(len(message_bits), '032b')

    # mengambil semua frame dari video
    ret, frame = capture.read()
    if not ret :
        raise ValueError("Video kosong")
    
    h, w, _ = frame.shape
    total_pixels = h * w

    # simpan header sequencial
    idx = 0
    for i in range(h) :
        for j in range(w) :
            if idx + 8 <= 32 :
                chunk = length_bits[idx:idx+8]
                
                r_bits = chunk[0:r_n]
                g_bits = chunk[r_n:r_n + g_n]
                b_bits = chunk[r_n + g_n:r_n + g_n + b_n]

                frame[i, j][0] = set_n_lsb(frame[i, j][0], r_bits, r_n)
                frame[i, j][1] = set_n_lsb(frame[i, j][1], g_bits, g_n)
                frame[i, j][2] = set_n_lsb(frame[i, j][2], b_bits, b_n)

                idx += 8
            else :
                break
        if idx >= 32 :
            break

    # embeding pesan secara random berdasarkan seed dari stego key
    random.seed(stego_key)

    indices = random.sample(
        range(4, total_pixels),  # bagian header diskip, dan pesan dimasukkan ke pixel setelah header
        len(message_bits) // 8
    )

    bit_idx = 0

    for idx in indices :
        i, j = get_pixels(idx, w)

        chunk = message_bits[bit_idx:bit_idx + 8]

        r_bits = chunk[0:r_n]
        g_bits = chunk[r_n:r_n + g_n]
        b_bits = chunk[r_n + g_n:r_n + g_n + b_n]
        
        frame[i, j][0] = set_n_lsb(frame[i, j][0], r_bits, r_n)
        frame[i, j][1] = set_n_lsb(frame[i, j][1], g_bits, g_n)
        frame[i, j][2] = set_n_lsb(frame[i, j][2], b_bits, b_n)

        bit_idx += 8

    out.write(frame)

    # dicopy ke frame lain
    while True :
        ret, frame = capture.read()
        if not ret :
            break
        out.write(frame)

    capture.release()
    out.release()

    print("(Random) Embedding pesan selesai!")

# mengekstrak pesan dari video hasil stego random
def extract_video_random(stego_video, stego_key, scheme) :
    capture = cv2.VideoCapture(stego_video)

    ret, frame = capture.read()
    if not ret:
        raise ValueError("Video kosong!")
    
    r_n, g_n, b_n = scheme

    h, w, _ = frame.shape
    total_pixels = h * w

    # mengambil header secara sequential
    bits = ""
    idx = 0
    for i in range(h):
        for j in range(w):
            r_bits = get_n_lsb(frame[i, j][0], r_n)
            g_bits = get_n_lsb(frame[i, j][1], g_n)
            b_bits = get_n_lsb(frame[i, j][2], b_n)

            bits += r_bits + g_bits + b_bits
            idx += 8

            if idx >= 32:
                break
        if idx >= 32:
            break

    length = int(bits, 2)
    print("DEBUG length:", length)

    if length > total_pixels:
        raise ValueError("Header rusak!")

    # mengambil random pesan
    random.seed(stego_key)

    indices = random.sample(range(4, total_pixels), length // 8)

    message_bits = ""
    for idx in indices:
        i, j = get_pixels(idx, w, )
        
        r_bits = get_n_lsb(frame[i, j][0], r_n)
        g_bits = get_n_lsb(frame[i, j][1], g_n)
        b_bits = get_n_lsb(frame[i, j][2], b_n)

        message_bits += r_bits + g_bits + b_bits

    message_bits = message_bits[:len(message_bits)//8 * 8]

    return bits_to_string(message_bits)

# testing
if __name__ == "__main__":
    input_video = "input.avi"
    output_video = "output_random.avi"
    message = "TESTING TESTING RANDOM!!"
    key = 12345
    scheme_input = input("Scheme (contoh 3,3,2): ")
    scheme = tuple(map(int, scheme_input.split(',')))

    embed_video_random(input_video, output_video, message, key, scheme)

    result = extract_video_random(output_video, key, scheme)
    print("Extracted : ", result)
