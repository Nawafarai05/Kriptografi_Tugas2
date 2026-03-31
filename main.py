import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import re
from stegovideo_random import embed_video_random, extract_video_random
from stegovideo_sequential import embed_video, extract_video
from comparison import *
from converter import *

# =========================
# GLOBAL STATE
# =========================
input_video_path = ""
file_to_embed_path = ""

# =========================
# HELPER FUNCTIONS
# =========================
def browse_input_video(label):
    global input_video_path
    path = filedialog.askopenfilename(filetypes=[("AVI files", "*.avi")])
    if path:
        input_video_path = path
        label.config(text=os.path.basename(path))

def browse_file_to_embed(label):
    global file_to_embed_path
    path = filedialog.askopenfilename()
    if path:
        file_to_embed_path = path
        label.config(text=os.path.basename(path))

def clear_window():
    for widget in root.winfo_children():
        widget.destroy()

def sanitize_filename(name):
    # Menghapus karakter yang tidak diperbolehkan dalam nama file Windows
    return "".join(re.findall(r'[a-zA-Z0-9._-]', name))

def header_checker(video, scheme) :
    capture = cv2.VideoCapture(video)

    r_n, g_n, b_n = scheme

    bits = ""

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

                if len(bits) >= 35 :
                    break
            if len(bits) >= 35 :
                break
        if len(bits) >= 35 :
            break

    mode = bits[0]
    method = bits[1]
    encrypt_flag = bits[2]

    return mode, method, encrypt_flag

# =========================
# UI SCREENS
# =========================

def show_main_menu():
    clear_window()
    root.geometry("400x350")
    tk.Label(root, text="Steganografi Video App", font=("Arial", 16, "bold"), pady=20).pack()

    tk.Button(root, text="Embedding (Sisipkan Pesan)", width=30, height=2, bg="#2ecc71", fg="white",
              command=show_embed_screen).pack(pady=10)

    tk.Button(root, text="Extracting (Ambil Pesan)", width=30, height=2, bg="#f39c12", fg="white",
              command=show_extract_screen).pack(pady=10)

    tk.Button(root, text="Comparing (Analisis Video)", width=30, height=2, bg="#3498db", fg="white",
              command=run_compare).pack(pady=10)

def show_embed_screen():
    clear_window()
    root.geometry("500x700")

    global input_video_path, file_to_embed_path
    input_video_path = ""
    file_to_embed_path = ""

    tk.Label(root, text="Menu Embedding", font=("Arial", 14, "bold")).pack(pady=10)

    # 1. Input Video Asli
    tk.Label(root, text="1. Pilih Video Asli (.avi):", font=("Arial", 10, "bold")).pack(anchor="w", padx=50)
    btn_video = tk.Button(root, text="Cari Video", command=lambda: browse_input_video(lbl_video))
    btn_video.pack(pady=5)
    lbl_video = tk.Label(root, text="Belum ada video dipilih", fg="gray")
    lbl_video.pack()

    # 2. Pilihan Tipe Embedding (Text vs File)
    tk.Label(root, text="\n2. Tipe Pesan:", font=("Arial", 10, "bold")).pack(anchor="w", padx=50)
    embed_type_var = tk.StringVar(value="text")

    frame_type = tk.Frame(root)
    frame_type.pack()

    text_container = tk.Frame(root)
    file_container = tk.Frame(root)

    def toggle_type():
        if embed_type_var.get() == "text":
            file_container.pack_forget()
            text_container.pack(pady=5)
        else:
            text_container.pack_forget()
            file_container.pack(pady=5)

    tk.Radiobutton(frame_type, text="Text", variable=embed_type_var, value="text", command=toggle_type).pack(side="left", padx=10)
    tk.Radiobutton(frame_type, text="File", variable=embed_type_var, value="file", command=toggle_type).pack(side="left", padx=10)

    tk.Label(text_container, text="Masukkan Pesan:").pack()
    text_entry = tk.Entry(text_container, width=40)
    text_entry.pack()

    btn_file = tk.Button(file_container, text="Pilih File", command=lambda: browse_file_to_embed(lbl_file))
    btn_file.pack()
    lbl_file = tk.Label(file_container, text="Belum ada file dipilih", fg="gray")
    lbl_file.pack()

    text_container.pack(pady=5)

    # 3. Metode LSB
    tk.Label(root, text="\n3. Metode LSB:", font=("Arial", 10, "bold")).pack(anchor="w", padx=50)
    method_var = tk.StringVar(value="sequential")
    key_container = tk.Frame(root)
    tk.Label(key_container, text="Stego Key:").pack()
    key_entry = tk.Entry(key_container, width=30)
    key_entry.pack()

    def toggle_method():
        if method_var.get() == "randomize":
            key_container.pack(pady=5)
        else:
            key_container.pack_forget()

    tk.Radiobutton(root, text="LSB Sequential", variable=method_var, value="sequential", command=toggle_method).pack()
    tk.Radiobutton(root, text="LSB Randomize", variable=method_var, value="randomize", command=toggle_method).pack()

    # 4. Scheme Dropdown
    tk.Label(root, text="\n4. Scheme (R,G,B):", font=("Arial", 10, "bold")).pack(anchor="w", padx=50)
    scheme_var = tk.StringVar(value="3,3,2")
    tk.OptionMenu(root, scheme_var, "3,3,2", "4,3,1", "2,2,4").pack(pady=5)

    # 5. Nama File Output
    tk.Label(root, text="\n5. Nama File Output (opsional):", font=("Arial", 10, "bold")).pack(anchor="w", padx=50)
    output_name_entry = tk.Entry(root, width=40)
    output_name_entry.pack(pady=5)

    def run_embed_process():
        try:
            if not input_video_path: raise Exception("Pilih video asli!")
            out_filename = output_name_entry.get().strip()
            if not out_filename:
                base = os.path.splitext(os.path.basename(input_video_path))[0]
                out_filename = f"{base}_embedded.avi"
            if not out_filename.endswith(".avi"): out_filename += ".avi"

            final_output_path = os.path.join(os.getcwd(), out_filename)
            mode = embed_type_var.get()
            data = text_entry.get() if mode == "text" else file_to_embed_path
            if mode == "file" and not file_to_embed_path: raise Exception("Pilih file!")

            scheme = tuple(map(int, scheme_var.get().split(',')))
            if method_var.get() == "randomize":
                if not key_entry.get(): raise Exception("Key tidak boleh kosong!")
                embed_video_random(input_video_path, final_output_path, data, mode, key_entry.get(), scheme)
            else:
                embed_video(input_video_path, final_output_path, data, mode, scheme)

            messagebox.showinfo("Sukses", f"Embedding Selesai!\nDisimpan di: {out_filename}")
            show_main_menu()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    tk.Button(root, text="Jalankan Embedding", command=run_embed_process, bg="#27ae60", fg="white", width=25, height=2).pack(pady=20)
    tk.Button(root, text="Kembali ke Menu", command=show_main_menu).pack()

def show_extract_screen():
    clear_window()
    root.geometry("600x650")
    global input_video_path
    input_video_path = ""

    tk.Label(root, text="Menu Extracting", font=("Arial", 14, "bold")).pack(pady=10)

    # 1. Pilih Video
    tk.Label(root, text="1. Pilih Video Stego (.avi):", font=("Arial", 10, "bold")).pack(anchor="w", padx=50)
    btn_video = tk.Button(root, text="Cari Video", command=lambda: browse_input_video(lbl_video))
    btn_video.pack(pady=5)
    lbl_video = tk.Label(root, text="Belum ada video dipilih", fg="gray")
    lbl_video.pack()

    # 2. Metode
    tk.Label(root, text="\n2. Metode LSB:", font=("Arial", 10, "bold")).pack(anchor="w", padx=50)
    method_var = tk.StringVar(value="sequential")
    key_container = tk.Frame(root)
    tk.Label(key_container, text="Stego Key:").pack()
    key_entry = tk.Entry(key_container, width=30)
    key_entry.pack()

    def toggle_method():
        if method_var.get() == "randomize": key_container.pack(pady=5)
        else: key_container.pack_forget()

    tk.Radiobutton(root, text="LSB Sequential", variable=method_var, value="sequential", command=toggle_method).pack()
    tk.Radiobutton(root, text="LSB Randomize", variable=method_var, value="randomize", command=toggle_method).pack()

    # 3. Scheme
    tk.Label(root, text="\n3. Scheme (R,G,B):", font=("Arial", 10, "bold")).pack(anchor="w", padx=50)
    scheme_var = tk.StringVar(value="3,3,2")
    tk.OptionMenu(root, scheme_var, "3,3,2", "4,3,1", "2,2,4").pack(pady=5)

    # Area Hasil
    result_container = tk.LabelFrame(root, text="Hasil Ekstraksi", padx=10, pady=10)
    text_result_area = tk.Text(result_container, height=5, width=50)
    
    file_res_frame = tk.Frame(result_container)
    file_info_label = tk.Label(file_res_frame, text="", fg="blue")
    file_name_entry = tk.Entry(file_res_frame, width=30)
    
    extracted_data_store = {"ext": "", "bits": ""}

    def save_file_final():
        raw_name = file_name_entry.get().strip()
        if not raw_name:
            messagebox.showwarning("Peringatan", "Masukkan nama file!")
            return
        
        # Bersihkan ekstensi dari karakter sampah
        clean_ext = "".join(re.findall(r'[a-zA-Z0-9.]', extracted_data_store["ext"]))
        if not clean_ext.startswith("."): clean_ext = "." + clean_ext
        
        final_name = sanitize_filename(raw_name) + clean_ext
        save_path = os.path.join(os.getcwd(), final_name)
        
        try:
            bits_to_file(extracted_data_store["bits"], save_path)
            messagebox.showinfo("Sukses", f"File disimpan di:\n{final_name}")
            show_main_menu()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def run_extract_process():
        text_result_area.pack_forget()
        file_res_frame.pack_forget()
        result_container.pack_forget()

        try:
            if not input_video_path: raise Exception("Pilih video!")
            scheme = tuple(map(int, scheme_var.get().split(',')))
            
            if method_var.get() == "randomize":
                res_type, res_data = extract_video_random(input_video_path, key_entry.get(), scheme)
            else:
                res_type, res_data = extract_video(input_video_path, scheme)

            result_container.pack(pady=10, fill="x", padx=40)
            if res_type == "text":
                text_result_area.pack()
                text_result_area.delete("1.0", tk.END)
                text_result_area.insert(tk.END, res_data)
            else:
                ext, bits = res_data
                extracted_data_store["ext"] = ext
                extracted_data_store["bits"] = bits
                
                file_res_frame.pack(fill="x")
                file_info_label.config(text=f"File ditemukan! (Ekstensi asli: {ext})")
                file_info_label.pack()
                tk.Label(file_res_frame, text="Nama file baru (tanpa ekstensi):").pack()
                file_name_entry.pack(pady=5)
                tk.Button(file_res_frame, text="Simpan Ke Repository", bg="#2ecc71", fg="white", command=save_file_final).pack(pady=5)

        except Exception as e:
            messagebox.showerror("Error", str(e))

    tk.Button(root, text="Jalankan Ekstraksi", command=run_extract_process, bg="#e67e22", fg="white", width=25, height=2).pack(pady=20)
    tk.Button(root, text="Kembali ke Menu", command=show_main_menu).pack()

def run_compare():
    try:
        v1 = filedialog.askopenfilename(title="Video Asli", filetypes=[("AVI files", "*.avi")])
        if not v1: return
        v2 = filedialog.askopenfilename(title="Video Stego", filetypes=[("AVI files", "*.avi")])
        if not v2: return
        mse, psnr = compare_videos(v1, v2)
        messagebox.showinfo("Hasil", f"MSE: {mse:.4f}\nPSNR: {psnr:.2f} dB")
    except Exception as e:
        messagebox.showerror("Error", str(e))

root = tk.Tk()
root.title("Steganografi Video App")
show_main_menu()
root.mainloop()
