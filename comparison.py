import cv2
import numpy as np
import math
import matplotlib.pyplot as plt

# function untuk mse dan psnr
def calculate_mse(frame1, frame2) :
    return np.mean((frame1.astype("float") - frame2.astype("float")) ** 2)

def calculate_psnr(mse) :
    if mse == 0:
        return float('inf')
    return 10 * math.log10((255 ** 2) / mse)

# membandingkan rgb dari frame video asli vs frame stegovideo
def compare_videos(video1, video2) :
    capture1 = cv2.VideoCapture(video1)
    capture2 = cv2.VideoCapture(video2)

    total_mse = 0
    total_psnr = 0
    frame_count = 0

    while True :
        ret1, frame1 = capture1.read()
        ret2, frame2 = capture2.read()

        if not ret1 or not ret2 :
            break

        mse = calculate_mse(frame1, frame2)
        psnr = calculate_psnr(mse)

        total_mse += mse
        total_psnr += psnr
        frame_count += 1

    capture1.release()
    capture2.release()

    avg_mse = total_mse/ frame_count
    avg_psnr = total_psnr / frame_count

    print("Average MSE :", avg_mse)
    print("Average PSNR:", avg_psnr, "dB")

    return avg_mse, avg_psnr

# fungsi untuk membuat dan menampilkan histogram RGB
def plot_histogram(frame1, frame2) :
    colors = ('b', 'g', 'r')

    plt.figure(figsize=(10,5))

    for i, color in enumerate(colors) :
        hist1 = cv2.calcHist([frame1], [i], None, [256], [0, 256])
        hist2 = cv2.calcHist([frame2], [i], None, [256], [0, 256])
        
        plt.subplot(1,2,1)
        plt.plot(hist1, color = color)
        plt.title("Original Video")

        plt.subplot(1,2,2)
        plt.plot(hist2, color = color)
        plt.title("Stego Video")

    plt.show()

# membandingkan histogram dari kedua video
def compare_hist(video1, video2) :
    capture1 = cv2.VideoCapture(video1)
    capture2 = cv2.VideoCapture(video2)

    ret1, frame1 = capture1.read()
    ret2, frame2 = capture2.read()

    if ret1 and ret2 :
        plot_histogram(frame1, frame2)

if __name__ == "__main__" :
    original = "dummy_files/sample.avi"
    stego = "sample_txt.avi"

    compare_videos(original, stego)
    compare_hist(original, stego)



