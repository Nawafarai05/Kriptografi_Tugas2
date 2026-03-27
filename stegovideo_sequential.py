import cv2
import numpy as np
from converter import * 

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

    # membedakan handling pesan langsung atau menggunakan berkas berdasarkan mode
    if mode == "text" :
        data_bits = string_to_bits(data)
        mode_bit = "0"
        extra_bits = ""
    elif mode == "file" :
        data_bits = file_to_bits(data)
        ext = get_extension(data)
        ext_bits = string_to_bits(ext)
        ext_len_bits = format(len(ext_bits), '08b')

        mode_bit = "1"
        extra_bits = ext_len_bits + ext_bits
    else :
        raise ValueError("Pesan dalam teks langsung atau berksas file")
    
    length_bits = format(len(data_bits), '032b')
    full_bits = mode_bit + length_bits + extra_bits + data_bits

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

                # mengambil mode
                if mode is None and len(bits) >= 1 :
                    mode = bits[0]

                # mengambil panjang pesan 32 bit
                if length is None and len(bits) >= 33:
                    length = int(bits[1:33], 2)
                    total_needed = 1 + 32 + length
                    print("DEBUG length :", length)

                if mode == "0" and length is not None :
                    total_needed = 1 + 32 + length
                    
                    if len(bits) >= total_needed :
                        capture.release()
                        message_bits = bits[33:33+length]
                        return bits_to_string(message_bits)
                    
                if mode == "1" and len(bits) >= 41 :
                    ext_len = int(bits[33:41], 2)

                    total_needed = 1 + 32 + 8 + ext_len + length
                    
                    if len(bits) >= total_needed :
                        capture.release()

                        ext_bits = bits[41:41+ext_len]
                        extension = bits_to_string(ext_bits)

                        file_bits = bits[41 + ext_len : 41 + ext_len + length]

                        output_name = input("Masukkan nama file output (tanpa ekstensi): ")
                        filename = output_name + extension
                        bits_to_file(file_bits, filename)

                        print("File berhasil diectract : ", filename)
                        return filename
                
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
