import cv2
import numpy as np
import random
from test_video import string_to_bits, bits_to_string

def get_positions(idx, width, height) :
    pixel_idx = idx // 3
    k = idx % 3
    i = pixel_idx // width
    j = pixel_idx % width
    return i, j, k

# embedding pesan ke dalam video secara random berdasarkan seeds dari stego key
def embed_video_random(input_video, output_video, message, stego_key) :
    capture = cv2.VideoCapture(input_video)

    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = capture.get(cv2.CAP_PROP_FPS)

    fourcc = cv2.VideoWriter_fourcc(*'MJPG')
    out = cv2.VideoWriter(output_video, fourcc, fps, (width, height))

    # mengubah message menjadi bits
    message_bits = string_to_bits(message)
    length_bits = format(len(message_bits), '032b')

    # mengambil semua frame dari video
    ret, frame = capture.read()
    if not ret :
        raise ValueError("Video kosong")
    
    h, w, _ = frame.shape
    total_pixels = h * w * 3

    # simpan header sequencial
    idx = 0
    for i in range(h) :
        for j in range(w) :
            for k in range(3) :
                if idx < 32 :
                    frame[i, j][k] = (frame[i, j][k] & 254) | int(length_bits[idx])
                    idx += 1
                else :
                    break
            if idx >= 32 :
                break
        if idx >= 32 :
            break

    # embeding pesan secara random berdasarkan seed dari stego key
    random.seed(stego_key)
    header_size = 32  # 32 bit pertama

    indices = random.sample(
        range(header_size, total_pixels),  # bagian header diskip, dan pesan dimasukkan ke pixel setelah header
        len(message_bits)
    )

    for bit_idx, rand_idx in enumerate(indices) :
        i, j, k = get_positions(rand_idx, w, h)
        frame[i, j][k] = (frame[i, j][k] & 254) | int(message_bits[bit_idx])

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
def extract_video_random(stego_video, stego_key) :
    capture = cv2.VideoCapture(stego_video)

    ret, frame = capture.read()
    if not ret:
        raise ValueError("Video kosong!")

    h, w, _ = frame.shape
    total_pixels = h * w * 3

    # mengambil header secara sequential
    bits = ""
    idx = 0
    for i in range(h):
        for j in range(w):
            for k in range(3):
                if idx < 32:
                    bits += str(frame[i, j][k] & 1)
                    idx += 1
                else:
                    break
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
    indices = random.sample(range(total_pixels), length)

    message_bits = ""
    for idx in indices:
        i, j, k = get_positions(idx, w, h)
        message_bits += str(frame[i, j][k] & 1)

    message_bits = message_bits[:len(message_bits)//8 * 8]

    return bits_to_string(message_bits)

# testing
if __name__ == "__main__":
    input_video = "input.avi"
    output_video = "output_random.avi"
    message = "TESTING TESTING RANDOM!!"
    key = 12345

    embed_video_random(input_video, output_video, message, key)

    result = extract_video_random(output_video, key)
    print("Extracted : ", result)
