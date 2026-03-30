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

    # handling bagian informasi yang akan disimpan dalam header
    if mode == "text" :
        mode_bit = "0"
    else :
        mode_bit = "1"
    method_bit = "1" # pada metode LSB random
    encrypt_bit = "0" # kalau tidak dienkripsi
    
    header_prefix = mode_bit + method_bit + encrypt_bit

    if mode == "text" :
        data_bits = string_to_bits(data)
        extra_bits = ""

    elif mode == "file" :
        data_bits = file_to_bits(data)
        ext = get_extension(data)
        filename = os.path.splitext(os.path.basename(data))[0]

        # menyimpan extension file yang disisipkan
        ext_bits = string_to_bits(ext)
        ext_len_bits = format(len(ext_bits), '08b')

        # menyimpan nama file yang disisipkan
        name_bits = string_to_bits(filename)
        name_len_bits  = format(len(name_bits), '08b')

        extra_bits = ext_len_bits + ext_bits + name_len_bits + name_bits

    else :
        raise ValueError("Mode harus text/file")
    
    length_bits = format(len(data_bits), '032b')

    header_bits = header_prefix + length_bits + extra_bits
    random_bits = data_bits

    # mengambil semua frame dari video
    ret, frame = capture.read()
    if not ret :
        raise ValueError("Video kosong")
    
    h, w, _ = frame.shape
    total_pixels = h * w

    # simpan header sequencial
    idx = 0
    done = False
    for i in range(h) :
        for j in range(w) :
            if idx >= len(header_bits) :
                done = True
                break 

            chunk = header_bits[idx : idx + 8]
            if len(chunk) < 8:
                chunk = chunk.ljust(8, '0')
                
            r_bits = chunk[0:r_n]
            g_bits = chunk[r_n:r_n + g_n]
            b_bits = chunk[r_n + g_n:r_n + g_n + b_n]

            frame[i, j][0] = set_n_lsb(frame[i, j][0], r_bits, r_n)
            frame[i, j][1] = set_n_lsb(frame[i, j][1], g_bits, g_n)
            frame[i, j][2] = set_n_lsb(frame[i, j][2], b_bits, b_n)

            idx += 8
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
    pixel_idx = 0

    def read_next_pixel() :
        nonlocal pixel_idx
        i, j = get_pixels(pixel_idx, w)
        pixel_idx += 1

        r_bits = get_n_lsb(frame[i, j][0], r_n)
        g_bits = get_n_lsb(frame[i, j][1], g_n)
        b_bits = get_n_lsb(frame[i, j][2], b_n)

        return r_bits + g_bits + b_bits
    
    while len(bits) < 43 : 
        bits += read_next_pixel()

    mode = bits[0]
    method = bits[1]
    encrypt_flag = bits[2]

    length = int(bits[3:35], 2)
    ext_len = int(bits[35:43], 2)

    print("DEBUG mode :", mode)
    print("DEBUG length:", length)
    print("DEBUG method :", method)

    # mengambil bagian extension file
    while len(bits) < 43 + ext_len : 
        bits += read_next_pixel()

    ext_bits = bits[43 : 43 + ext_len]
    extension = bits_to_string(ext_bits)

    # mengambil bagian panjang name file
    while len(bits) < 43 + ext_len + 8 : 
        bits += read_next_pixel()

    name_len = int(bits[43 + ext_len : 43 + ext_len + 8], 2)

    # mengambil bagian nama file
    while len(bits) < 43 + ext_len +  8 + name_len :
        bits += read_next_pixel()

    name_start = 43 + ext_len + 8
    name_bits = bits[name_start : name_start + name_len]
    filename = bits_to_string(name_bits)

    print("DEBUG extension :", extension)
    print("DEBUG filename :", filename)

    total_header = 43 + ext_len + 8 + name_len

    # mengekstrak bagian message
    start_pixel = (total_header + 7) // 8

    random.seed(key_to_seed(stego_key))
    all_indices = list(range(start_pixel, total_pixels))
    random.shuffle(all_indices)

    message_bits = ""

    indices = all_indices[:(length + 7) // 8]

    for px_idx in indices :
        i, j = get_pixels(px_idx, w)

        r_bits = get_n_lsb(frame[i, j][0], r_n)
        g_bits = get_n_lsb(frame[i, j][1], g_n)
        b_bits = get_n_lsb(frame[i, j][2], b_n)

        message_bits += r_bits + g_bits+ b_bits

        if len(message_bits) >= length:
            message_bits = message_bits[:length]
            break

    # kalau message bentuk text langsung
    if mode == "0" :
        return bits_to_string(message_bits[:length])

    # kalau message dalam bentuk berkas file
    else :
        output_folder = "extracted"
        os.makedirs(output_folder, exist_ok = True)

        output_name = input("Nama file output (tanpa extensi) : ")

        if output_name == "" :
            filename = filename + extension
        else :
            filename = output_name + extension

        filepath = os.path.join(output_folder, filename)
        
        bits_to_file(message_bits, filepath)

        print("File berhasil diextract : ", filepath)
        return filepath

# testing
if __name__ == "__main__":
    input_video = "input.avi"
    output_video = "output_random.avi"

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