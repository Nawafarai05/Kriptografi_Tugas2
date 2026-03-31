import cv2
from converter import *
import os
from a5_1 import * 

# embedding pesan ke dalam video secara sequential
def embed_video(input_video, output_video, data, mode, scheme, encrypt, enc_key) :
    capture = cv2.VideoCapture(input_video)

    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = capture.get(cv2.CAP_PROP_FPS)

    # codec menggunakan yang lossless atua minim komporesi
    fourcc = cv2.VideoWriter_fourcc(*'HFYU')
    out = cv2.VideoWriter(output_video, fourcc, fps, (width, height))

    r_n, g_n, b_n = scheme
    if r_n + g_n + b_n != 8 :
        raise ValueError("Bit scheme harus berjumlah 8")

    # handling bagian informasi yang akan disimpan dalam header
    if mode == "text" :
        mode_bit = "0"
    else :
        mode_bit = "1"
    method_bit = "0" # pada metode LSB sequential
    encrypt_bit = "1" if encrypt == "y" else "0"

    header_prefix = mode_bit + method_bit + encrypt_bit

    # membedakan berdasarkan jenis pesan yang di-embed
    if mode == "text" :
        data_bytes = data.encode()
        extra_bits = ""

    elif mode == "file" :
        data_bytes = open(data, "rb").read()

        extension = get_extension(data)
        filename = os.path.splitext(os.path.basename(data))[0]

        ext_bits = string_to_bits(extension)
        ext_len_bits = format(len(ext_bits), '08b')

        name_bits = string_to_bits(filename)
        name_len_bits = format(len(name_bits), '08b')

        extra_bits = ext_len_bits + ext_bits + name_len_bits + name_bits
    else :
        raise ValueError("Pesan dalam teks langsung atau berksas file")
    
    # proses apabila pesan dienkripsi
    if encrypt_bit == "1" :
        key_bin = key_to_64bit(enc_key)
        data_bytes = encrypt_payload(data_bytes, key_bin)

    # menymipan informasi lainnya
    file_size_bits = format(len(data_bytes), '032b')
    data_bits = bytes_to_bits(data_bytes)
    length_bits = format(len(data_bits), '032b')

    if mode == "text" :
        header_bits = header_prefix + length_bits + file_size_bits
    else :
        header_bits = header_prefix + length_bits + file_size_bits + extra_bits

    full_bits = header_bits + data_bits

    # embedding pesan secara sequential
    bit_idx = 0

    while True:
        ret, frame = capture.read()
        if not ret :
            break

        height, width, _ = frame.shape

        for i in range(height) :
            for j in range(width) :
                if bit_idx >= len(full_bits) :
                    break

                chunk = full_bits[bit_idx:bit_idx + 8]
                chunk = chunk.ljust(8, '0')

                r_bits = chunk[0:r_n]
                g_bits = chunk[r_n:r_n + g_n]
                b_bits = chunk[r_n + g_n:r_n + g_n + b_n]

                frame[i, j][0] = set_n_lsb(frame[i, j][0], r_bits, r_n)
                frame[i, j][1] = set_n_lsb(frame[i, j][1], g_bits, g_n)
                frame[i, j][2] = set_n_lsb(frame[i, j][2], b_bits, b_n)

                bit_idx += 8
        out.write(frame)
    capture.release()
    out.release()

    print("Scheme digunakan :", scheme)
    print("Mode :", mode)
    print("(Sequential) Embedding selesai!")

# mengekstrak video
def extract_video(stego_video, enc_key, scheme) :
    capture = cv2.VideoCapture(stego_video)

    ret, frame = capture.read()
    if not ret :
        raise ValueError("Video kosong")

    height, width, _ = frame.shape
    r_n, g_n, b_n = scheme

    bits = ""
    pixel_idx = 0

    def read_next_pixel() :
        nonlocal pixel_idx
        i, j = get_pixels(pixel_idx, width)
        pixel_idx += 1

        r_bits = get_n_lsb(frame[i, j][0], r_n)
        g_bits = get_n_lsb(frame[i, j][1], g_n)
        b_bits = get_n_lsb(frame[i, j][2], b_n)

        return r_bits + g_bits + b_bits

    while len(bits) < 67 :
        bits += read_next_pixel()

    mode = bits[0]
    method = bits[1]
    encrypt_flag = bits[2]

    length = int(bits[3:35], 2)
    file_size = int(bits[35:67], 2)
                
    print("DEBUG encrypt :", encrypt_flag)

    # ngambil header
    if mode == "1" :
        while len(bits) < 75 :
            bits += read_next_pixel()
        ext_len = int(bits[67:75], 2)

        while len(bits) < 75 + ext_len + 8 :
            bits += read_next_pixel()
        extension = bits_to_string(bits[75 : 75 + ext_len])
        name_len = int(bits[75 + ext_len : 75 + ext_len + 8], 2)

        while len(bits) < 75 + ext_len + 8 + name_len : 
            bits += read_next_pixel()
        name_start = 75 + ext_len + 8
        filename = bits_to_string(bits[name_start : name_start + name_len])

        print("DEBUG extension :", extension)
        print("DEBUG filename :", filename)

        total_header = 75 + ext_len + 8 + name_len

    else :
        total_header = 67

    # mengambil pesan
    while len(bits) < total_header + length :
        bits += read_next_pixel()
    message_bits = bits[total_header : total_header + length]

    data_bytes = bits_to_bytes(message_bits)

    # mendekripsi apabila didekripsi
    if encrypt_flag == "1" :
        key_bin = key_to_64bit(enc_key)
        data_bytes = decrypt_payload(data_bytes, key_bin, len(data_bytes))
    data_bytes = data_bytes[:file_size] # dipotong sesuai ukuran asli file

    # mengolah hasil 
    if mode == "0" :
        return data_bytes.decode()
    else :
        output_name = input("Nama file output (tanpa extensi) : ")

        if output_name == "" :
            filename = filename + extension
        else :
            filename = output_name + extension

        with open(filename, "wb") as f :
            f.write(data_bytes)

        print("File berhasil diextract : ", filename)
        return filename

# testing
if __name__ == "__main__":
    input_video = "input.avi"
    output_video = "output.avi"

    mode = input("Masukkan mode text/file : ")

    if mode == "text" :
        data = input("Masukkan pesan : ")
    else :
        data = input("Masukkan nama file : ")

    encrypt = input("Pesan ingin dienkripsi? (y/n) : ")

    if encrypt == "y" :
        enc_key = input("Masukkan kunci enkripsi pesan : ")

    scheme_input = input("Scheme (contoh 3,3,2): ")
    scheme = tuple(map(int, scheme_input.split(',')))

    embed_video(input_video, output_video, data, mode, scheme, encrypt, enc_key)

    result = extract_video(output_video, enc_key, scheme)
    print("Extracted message :", result)