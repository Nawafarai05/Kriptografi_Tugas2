import cv2
import numpy as np
import random
import os
from converter import *

def key_to_seed(key) :
    seed = 0
    for char in key :
        seed = seed * 31 + ord(char)
    return seed
    
def get_pixels(idx, width) :
    i = idx // width
    j = idx % width
    return i, j

# embedding pesan ke dalam video secara random berdasarkan seeds dari stego key
def embed_video_random(input_video, output_video, data, mode, stego_key, scheme) :
    capture = cv2.VideoCapture(input_video)

    r_n, g_n, b_n = scheme
    if r_n + g_n + b_n != 8:
        raise ValueError("Scheme harus total 8 bit")

    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = capture.get(cv2.CAP_PROP_FPS)

    fourcc = cv2.VideoWriter_fourcc(*'HFYU')
    out = cv2.VideoWriter(output_video, fourcc, fps, (width, height))

    # menentukan mode dalam teks atau berkas file
    if mode == "text" :
        data_bits = string_to_bits(data)
        mode_bit = "0"
        ext_bits = ""
        ext_len_bits = "00000000"

    elif mode == "file" :
        data_bits = file_to_bits(data)
        ext = get_extension(data)
        ext_bits = string_to_bits(ext)
        ext_len_bits = format(len(ext_bits), '08b')
        mode_bit = "1"

    else :
        raise ValueError("Mode harus text/file")
    
    length_bits = format(len(data_bits), '032b')

    header_bits = mode_bit + length_bits + ext_len_bits
    random_bits = ext_bits + data_bits

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
            if idx + 8 <= len(header_bits):
                chunk = header_bits[idx:idx+8]
                
                r_bits = chunk[0:r_n]
                g_bits = chunk[r_n:r_n + g_n]
                b_bits = chunk[r_n + g_n:r_n + g_n + b_n]

                frame[i, j][0] = set_n_lsb(frame[i, j][0], r_bits, r_n)
                frame[i, j][1] = set_n_lsb(frame[i, j][1], g_bits, g_n)
                frame[i, j][2] = set_n_lsb(frame[i, j][2], b_bits, b_n)

                idx += 8
            else :
                break
        if idx >= len(header_bits) :
            break

    # embeding pesan secara random berdasarkan seed dari stego key
    random.seed(key_to_seed(stego_key))

    start_pixel = idx // 8
    needed_pixels = (len(random_bits) + 7) // 8

    all_indices = list(range(start_pixel, total_pixels))
    random.shuffle(all_indices)
    indices = all_indices[:needed_pixels]

    bit_idx = 0

    for px_idx in indices :
        i, j = get_pixels(px_idx, w)

        chunk = random_bits[bit_idx:bit_idx + 8]

        if len(chunk) < 8 :
            chunk = chunk.ljust(8, '0')

        r_bits = chunk[0:r_n]
        g_bits = chunk[r_n:r_n + g_n]
        b_bits = chunk[r_n + g_n:r_n + g_n + b_n]
        
        frame[i, j][0] = set_n_lsb(frame[i, j][0], r_bits, r_n)
        frame[i, j][1] = set_n_lsb(frame[i, j][1], g_bits, g_n)
        frame[i, j][2] = set_n_lsb(frame[i, j][2], b_bits, b_n)

        bit_idx += 8

        if bit_idx >= len(random_bits) :
            break

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

    # membaca bagian header
    bits = ""
    idx = 0

    for i in range(h):
        for j in range(w):
            r_bits = get_n_lsb(frame[i, j][0], r_n)
            g_bits = get_n_lsb(frame[i, j][1], g_n)
            b_bits = get_n_lsb(frame[i, j][2], b_n)

            bits += r_bits + g_bits + b_bits

            if len(bits) >= 41 :
                bits = bits[:41]
                break
        if len(bits) >=  41 :
            break

    # mengambil bagian header 33 bits pertama
    mode = bits[0]
    length = int(bits[1:33], 2)
    ext_len = int(bits[33:41], 2)
    print("DEBUG length:", length)

    start_pixel = 5

    # mengekstrak bagian message
    random.seed(key_to_seed(stego_key))
    all_indices = list(range(start_pixel, total_pixels))
    random.shuffle(all_indices)

    message_bits = ""

    indices = all_indices[:(ext_len + length + 7) // 8]

    for px_idx in indices :
        i, j = get_pixels(px_idx, w)

        r_bits = get_n_lsb(frame[i, j][0], r_n)
        g_bits = get_n_lsb(frame[i, j][1], g_n)
        b_bits = get_n_lsb(frame[i, j][2], b_n)

        message_bits += r_bits + g_bits+ b_bits

        # berhenti kalau sudah
        total_needed = ext_len + length 
        if len(message_bits) >= 8 :
            if len(message_bits) >= total_needed:
                message_bits = message_bits[:total_needed]
                break

    # kalau message bentuk text langsung
    if mode == "0" :
        return bits_to_string(message_bits[:length])

    # kalau message dalam bentuk berkas file
    if mode == "1" :
        ext_bits = message_bits[:ext_len]
        extension = bits_to_string(ext_bits)

        extension = ''.join(c for c in extension if c.isalnum() or c == '.')

        print("DEBUG extension :", extension)

        file_bits = message_bits[ext_len : ext_len + length]
        file_bits = file_bits[:length]

        # metode save as extracted file
        output_folder = "extracted"
        os.makedirs(output_folder, exist_ok = True)
        output_name = input("Nama file output (tanpa extensi) : ")

        if output_name == "" :
            filename = "extracted" + extension
        else :
            filename = output_name + extension

        filepath = os.path.join(output_folder, filename)
        
        bits_to_file(file_bits, filepath)

        print("File berhas" \
        "il diextract : ", filepath)
        return filepath

# testing
if __name__ == "__main__":
    input_video = "input.avi"
    output_video = "output_random.avi"
    message = "TESTING TESTING RANDOM!!"

    mode = input("Mode (text/file): ")

    if mode == "text":
        data = input("Masukkan pesan: ")
    else:
        data = input("Masukkan nama file: ")

    key = input("Masukkan key : ")

    scheme_input = input("Scheme (contoh 3,3,2): ")
    scheme = tuple(map(int, scheme_input.split(',')))

    embed_video_random(input_video, output_video, data, mode, key, scheme)

    result = extract_video_random(output_video, key, scheme)
    print("Extracted : ", result)
