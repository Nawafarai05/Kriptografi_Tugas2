import cv2
import numpy as np

# konversi antara string (pesan) menjadi bits, dan sebaliknya
def string_to_bits(string):
    return''.join(format(ord(char), '08b') for char in string)

def bits_to_string(bits):
    chars = [bits[i:i+8] for i in range(0, len(bits), 8)]
    return ''.join(chr(int(char,2)) for char in chars)

# menyisipkan pesan teks ke dalam gambar
def embed_message(image_path, output_path, message) :
    img = cv2.imread(image_path)
    height, width, _ = img.shape

    # mengubah pesan ke bit
    message_bits = string_to_bits(message)

    # panjang message diubah ke dalam 32 bit
    length = len(message_bits)
    length_bits = format(length, '032b')

    full_bits = length_bits + message_bits
    total_bits = len(full_bits)

    idx = 0

    for i in range(height) :
        for j in range(width) :
            pixel = img[i, j]

            for k in range(3): #3 adalah untuk RGB
                if idx < total_bits:
                    bit = int(full_bits[idx])
                    pixel[k] = (pixel[k] & ~1) | bit
                    idx += 1

            img[i, j] = pixel

            if idx >= total_bits :
                break
        if idx >= total_bits :
            break

    cv2.imwrite(output_path, img)
    print("Pesan berhasil disisipkan!")

# mengekstrak pesan yang telah disisipkan
def extract_message(image_path):
    img = cv2.imread(image_path)
    height, width, _ = img.shape

    bits = ""

    for i in range(height) :
        for j in range(width) :
            for k in range(3):
                bits += str(img[i,j][k] & 1)
    
    # ambil panjang pesan di 32 bit pertama
    length = int(bits[:32], 2)

    # DEBUG (penting!)
    print("DEBUG length:", length)

    # ambil pesan
    message_bits = bits[32:32+length]

    # Pastikan kelipatan 8
    message_bits = message_bits[:len(message_bits)//8 * 8]

    message = bits_to_string(message_bits)
    return message

# testing

if __name__ == "__main__" :
    input_img = "input.png"
    output_img = "output.png"
    message = "hello world!"

    embed_message(input_img, output_img, message)

    extracted = extract_message(output_img)
    print("extracted message : ", extracted)
