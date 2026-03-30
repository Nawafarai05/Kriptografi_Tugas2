import cv2
from converter import *
import os
from a5_1 import * 

# embedding pesan ke dalam video secara sequential
def embed_video(input_video, output_video, data, mode, scheme) :
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
    encrypt_bit = "0" # kalau tidak dienkripsi

    header_prefix = mode_bit + method_bit + encrypt_bit

    # membedakan berdasarkan jenis pesan yang di-embed
    if mode == "text" :
        data_bits = string_to_bits(data)
        extra_bits = ""

    elif mode == "file" :
        data_bits = file_to_bits(data)

        ext = get_extension(data)
        filename = os.path.splitext(os.path.basename(data))[0]

        ext_bits = string_to_bits(ext)
        ext_len_bits = format(len(ext_bits), '08b')

        name_bits = string_to_bits(filename)
        name_len_bits = format(len(name_bits), '08b')

        extra_bits = ext_len_bits + ext_bits + name_len_bits + name_bits
    else :
        raise ValueError("Pesan dalam teks langsung atau berksas file")

    length_bits = format(len(data_bits), '032b')
    full_bits = header_prefix + length_bits + extra_bits + data_bits

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
                if bit_idx >= total_bits :
                    break

                chunk = full_bits[bit_idx:bit_idx + 8]

                if len(chunk) < 8 :
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
    mode = None
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

                # mengambil dan membaca informasi bagian header
                if mode is None and len(bits) >= 3 :
                    mode = bits[0]
                    method = bits[1]
                    encrypt_flag = bits[2]

                    print("DEBUG mode :", mode)
                    print("DEBUG method :", method)
                    print("DEBUG encrypt :", encrypt_flag)

                if length is None and len(bits) >= 35:
                    length = int(bits[3:35], 2)
                    print("DEBUG length :", length)

                # ngambil kalau teks
                if mode == "0" and length is not None :
                    total_needed = 3 + 32 + length

                    if len(bits) >= total_needed :
                        capture.release()
                        message_bits = bits[35:35+length]
                        return bits_to_string(message_bits)

                # ngambil kalau file
                if mode == "1" and len(bits) >= 43 :
                    ext_len = int(bits[35:43], 2)

                    if len(bits) >= 43 + ext_len + 8 :
                        name_len = int(bits[43 + ext_len : 43 + ext_len + 8], 2)
                        total_needed = 3 + 32 + 8 + ext_len + 8 + name_len + length

                        if len(bits) >= total_needed :
                            capture.release()

                            ext_bits = bits[43:43 + ext_len]
                            extension = bits_to_string(ext_bits)

                            print("DEBUG extension :", extension)

                            name_start = 43 + ext_len + 8
                            name_bits = bits[name_start : name_start + name_len]
                            filename = bits_to_string(name_bits)

                            print("DEBUG filename :", filename)

                            file_bits = bits[name_start + name_len : name_start + name_len + length]
                
                            output_folder = "extracted"
                            os.makedirs(output_folder, exist_ok = True)
                            output_name = input("Nama file output (tanpa extensi) : ")

                            if output_name == "" :
                                filename = filename + extension
                            else :
                                filename = output_name + extension

                            filepath = os.path.join(output_folder, filename)

                            bits_to_file(file_bits, filepath)

                            print("File berhasil diectract : ", filename)
                            return filepath

    capture.release()
    return None

# testing
if __name__ == "__main__":
    input_video = "input.avi"
    output_video = "output.avi"

    mode = input("Masukkan mode text/file : ")

    if mode == "text" :
        data = input("Masukkan pesan : ")
    else :
        data = input("Masukkan nama file : ")

    scheme_input = input("Scheme (contoh 3,3,2): ")
    scheme = tuple(map(int, scheme_input.split(',')))

    embed_video(input_video, output_video, data, mode, scheme)

    result = extract_video(output_video, scheme)
    print("Extracted message :", result)