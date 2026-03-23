import cv2
import numpy as np

# konversi antara string (pesan) menjadi bits, dan sebaliknya
def string_to_bits(string):
    return''.join(format(ord(char), '08b') for char in string)

def bits_to_string(bits):
    chars = [bits[i:i+8] for i in range(0, len(bits), 8)]
    return ''.join(chr(int(char,2)) for char in chars)

# embedding pesan ke dalam video
def embed_video(input_video, output_video, message) :
    capture = cv2.VideoCapture(input_video)

    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = capture.get(cv2.CAP_PROP_FPS)

    # codec menggunakan yang lossless atua minim komporesi
    fourcc = cv2.VideoWriter_fourcc(*'HFYU')
    out = cv2.VideoWriter(output_video, fourcc, fps, (width, height))

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
        max_capacity += height * width * 3

        for i in range(height) :
            for j in range(width) :
                for k in range(3) :
                    if bit_idx < total_bits :
                        bit = int(full_bits[bit_idx])
                        frame[i, j][k] = (frame[i, j][k] & 254) | bit
                        bit_idx += 1

        out.write(frame)

    capture.release()
    out.release()

    print("Total capacity:", max_capacity, "bits")
    print("Message size:", total_bits, "bits")

    if total_bits > max_capacity : 
        print("Kapasitas berlebih!")
    else :
        print("Embeding selesai!")

# mengekstrak video 
def extract_video(stego_video) :
    capture = cv2.VideoCapture(stego_video)

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
                for k in range(3) :
                    bits += str(frame[i, j][k] & 1)

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

    embed_video(input_video, output_video, message)

    result = extract_video(output_video)
    print("Extracted message :", result)
