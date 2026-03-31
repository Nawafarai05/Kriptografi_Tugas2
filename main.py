import tkinter as tk
from tkinter import filedialog, messagebox, ttk, simpledialog
import os
import re
import cv2
import matplotlib.pyplot as plt
from stegovideo_random import *
from stegovideo_sequential import *
from comparison import *
from converter import *
from a5_1 import *

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

# memastikan nama file hanya berisikan karakter yang diperbolehkan dalam windows
def sanitize_filename(name):
    return "".join(re.findall(r'[a-zA-Z0-9._-]', name))

# mengambil header
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

# mengecek ukuran file, memastikan bisa disisipkan
def check_capacity(input_video, data, mode, scheme, encrypt, enc_key) :
    # mengambil size data video
    capture = cv2.VideoCapture(input_video)

    total_pixels = 0
    total_frames = 0

    while True :
        ret, frame = capture.read()
        if not ret :
            break
        h, w, _ = frame.shape
        total_pixels += h * w
        total_frames += 1

    capture.release()

    capacity_bits = total_pixels * 8

    # mengambil size data yang disisipkan
    if mode == "text" :
        data_bytes = data.encode()
        extra_bits = 0
    else :
        data_bytes = open(data, "rb").read()

        ext = get_extension(data)
        filename = os.path.splitext(os.path.basename(data))[0]

        ext_bits = len(string_to_bits(ext))
        name_bits = len(string_to_bits(filename))

        extra_bits = 8 + ext_bits + 8 + name_bits

    # menkripsi pesan kalau dienkripsi
    if encrypt == "y" :
        key_bin = key_to_64bit(enc_key)
        data_bytes = encrypt_payload(data_bytes, key_bin)
    data_bits = len(bytes_to_bits(data_bytes))

    # ukuran header
    base_header = 67

    if mode == "text" :
        header_bits = base_header
    else :
        header_bits = base_header + extra_bits
    
    total_needed = header_bits + data_bits

    print("DEBUG video size : ", capacity_bits)
    print("DEBUG file/text size :", total_needed)

    if total_needed > capacity_bits :
        return False
    else :
        return True

# custom input pop up
def input_dialog(title, prompt) :
    dialog = tk.Toplevel(root)
    dialog.title(title)
    
    width = 400
    height = 200

    root.update_idletasks()

    x = root.winfo_x() + (root.winfo_width() // 2) - (width // 2)
    y = root.winfo_y() + (root.winfo_height() // 2) - (height // 2)

    dialog.geometry(f"{width}x{height}+{x}+{y}")
    dialog.grab_set()

    tk.Label(dialog, text=prompt, font = ("Arial", 11)).pack(pady = 15)

    entry = tk.Entry(dialog, width = 40, font = ("Arial", 11))
    entry.pack(pady=10)
    entry.focus()

    result = {"value" : None}

    def submit() :
        result["value"] = entry.get()
        dialog.destroy()

    entry.bind("<Return>", lambda e: submit())

    tk.Button(dialog, text = "Ok", command = submit, width= 10).pack(pady = 10)

    dialog.wait_window()
    return result["value"]

# membuat loading pop up
def load_popup(text = "Processing...") :
    popup = tk.Toplevel(root)
    popup.title("Processing")

    width = 300
    height = 100

    root.update_idletasks()

    x = root.winfo_x() + (root.winfo_width() // 2) - (width // 2)
    y = root.winfo_y() + (root.winfo_height() // 2) - (height // 2)

    popup.geometry(f"{width}x{height}+{x}+{y}")
    popup.grab_set()

    label = tk.Label(popup, text = text, font = ("Arial", 11))
    label.pack(pady=20)

    return popup

# =========================
# UI SCREENS
# =========================

def show_main_menu():
    clear_window()
    root.geometry("900x700")

    tk.Label(root, text="Steganografi Video App", font=("Arial", 16, "bold"), pady=20).pack()

    tk.Button(root, text="Embedding (Sisipkan Pesan)", width=30, height=2, bg="#2ecc71", fg="white",
              command=show_embed_screen).pack(pady=10)

    tk.Button(root, text="Extracting (Ambil Pesan)", width=30, height=2, bg="#f39c12", fg="white",
              command=show_extract_screen).pack(pady=10)

    tk.Button(root, text="Comparing (Analisis Video)", width=30, height=2, bg="#3498db", fg="white",
              command=run_compare).pack(pady=10)

def show_embed_screen():
    clear_window()
    root.geometry("900x700")

    global input_video_path, file_to_embed_path
    input_video_path = ""
    file_to_embed_path = ""

    # set up bagian scrolling
    canvas = tk.Canvas(root)
    scrollbar = tk.Scrollbar(root, orient="vertical", command=canvas.yview)

    scroll_frame = tk.Frame(canvas)

    window_id = canvas.create_window((0,0), window = scroll_frame, anchor = "n")
    canvas.configure(yscrollcommand = scrollbar.set)

    canvas.pack(side = "left", fill = "both", expand = True)
    scrollbar.pack(side = "right", fill = "y")

    def on_configure(event) : 
        canvas.itemconfig(window_id, width = event.width)

    canvas.bind("<Configure>", on_configure)

    scroll_frame.bind("<Configure>", lambda e : canvas.configure(scrollregion = canvas.bbox("all")))

    def _on_mousewheel(event) :
        canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    canvas.bind_all("<MouseWheel>", _on_mousewheel)

    # set up halaman
    tk.Label(scroll_frame, text="Menu Embedding", font=("Arial", 14, "bold")).pack(pady=10)

    # 1. Input Video Asli
    frame_video = tk.Frame(scroll_frame)
    frame_video.pack(pady=10)

    tk.Label(frame_video, text="1. Pilih Video Asli (.avi):", font=("Arial", 10, "bold")).pack(pady=5)
    btn_video = tk.Button(frame_video, text="Cari Video", command=lambda: browse_input_video(lbl_video))
    btn_video.pack(pady=5)

    lbl_video = tk.Label(frame_video, text="Belum ada video dipilih", fg="gray")
    lbl_video.pack()

    # 2. Pilih Tipe Embedding (Text vs File)
    frame_mode = tk.Frame(scroll_frame)
    frame_mode.pack(pady=10)
    tk.Label(frame_mode, text="\n2. Tipe Pesan:", font=("Arial", 10, "bold")).pack(pady=5)
    embed_type_var = tk.StringVar(value="text")

    frame_type = tk.Frame(frame_mode)
    frame_type.pack()

    input_container = tk.Frame(frame_mode)
    input_container.pack(pady=5)

    text_container = tk.Frame(input_container)
    file_container = tk.Frame(input_container)

    text_container.pack()

    def toggle_type():
        for widget in input_container.winfo_children() :
            widget.pack_forget()

        if embed_type_var.get() == "text":
            text_container.pack()
        else:
            file_container.pack()

    tk.Radiobutton(frame_type, text="Text", variable=embed_type_var, value="text", command=toggle_type).pack(side="left", padx=10)
    tk.Radiobutton(frame_type, text="File", variable=embed_type_var, value="file", command=toggle_type).pack(side="left", padx=10)

    tk.Label(text_container, text="Masukkan Pesan:").pack()
    text_entry = tk.Entry(text_container, width=40)
    text_entry.pack()

    btn_file = tk.Button(file_container, text="Pilih File", command=lambda: browse_file_to_embed(lbl_file))
    btn_file.pack()
    lbl_file = tk.Label(file_container, text="Belum ada file dipilih", fg="gray")
    lbl_file.pack()

    text_container.pack()

    # 3. Pesan dienkripsi atau tidak
    frame_enc = tk.Frame(scroll_frame)
    frame_enc.pack(pady=10)

    tk.Label(frame_enc, text="\n3. Pesan dienkripsi? ", font=("Arial", 10, "bold")).pack(pady=5)
    encrypt_var = tk.StringVar(value="Tidak")

    enckey_container = tk.Frame(frame_enc)
    tk.Label(enckey_container, text="Encryption Key:").pack()
    enckey_entry = tk.Entry(enckey_container, width=30)
    enckey_entry.pack()

    def toggle_encrypt():
        if encrypt_var.get() == "Ya":
            enckey_container.pack(pady=5)
        else:
            enckey_container.pack_forget()

    tk.Radiobutton(frame_enc, text="Tidak", variable=encrypt_var, value="Tidak", command=toggle_encrypt).pack()
    tk.Radiobutton(frame_enc, text="Ya", variable=encrypt_var, value="Ya", command=toggle_encrypt).pack()

    # 4. Metode LSB
    frame_method = tk.Frame(scroll_frame)
    frame_method.pack(pady=10)

    tk.Label(frame_method, text="\n4. Metode LSB:", font=("Arial", 10, "bold")).pack(pady=5)
    method_var = tk.StringVar(value="sequential")

    key_container = tk.Frame(frame_method)
    tk.Label(key_container, text="Stego Key:").pack()
    key_entry = tk.Entry(key_container, width=30)
    key_entry.pack()

    def toggle_method():
        if method_var.get() == "randomize":
            key_container.pack(pady=5)
        else:
            key_container.pack_forget()

    tk.Radiobutton(frame_method, text="LSB Sequential", variable=method_var, value="sequential", command=toggle_method).pack()
    tk.Radiobutton(frame_method, text="LSB Randomize", variable=method_var, value="randomize", command=toggle_method).pack()

    # 5. Scheme Dropdown
    frame_scheme = tk.Frame(scroll_frame)
    frame_scheme.pack(pady=10)

    tk.Label(frame_scheme , text="\n5. Scheme (R,G,B):", font=("Arial", 10, "bold")).pack(pady=5)
    
    scheme_var = tk.StringVar(value="3,3,2")
    tk.OptionMenu(frame_scheme , scheme_var, "3,3,2", "2,2,4", "1,1,6").pack(pady=5)

    # 6. Nama File Output
    frame_output = tk.Frame(scroll_frame)
    frame_output.pack(pady=10)

    tk.Label(frame_output, text="\n5. Nama File Output (opsional):", font=("Arial", 10, "bold")).pack(pady=5)
    output_name_entry = tk.Entry(frame_output, width=40)
    output_name_entry.pack(pady=5)

    def run_embed_process():
        loading_popup = None
        try:
            loading_popup = load_popup("Embedding sedang berlangsung...")

            root.update()

            if not input_video_path: 
                raise Exception("Pilih video!")
            
            out_filename = output_name_entry.get().strip()
            if not out_filename:
                base = os.path.splitext(os.path.basename(input_video_path))[0]
                out_filename = f"{base}_embedded.avi"
            if not out_filename.endswith(".avi") : 
                out_filename += ".avi"

            final_output_path = os.path.join(os.getcwd(), out_filename)
            
            scheme = tuple(map(int, scheme_var.get().split(',')))

            mode = embed_type_var.get()
            data = text_entry.get() if mode == "text" else file_to_embed_path
            
            if mode == "file" and not file_to_embed_path : 
                raise Exception("Pilih file!")

            # memvalidasi enkripsi
            encrypt = "y" if encrypt_var.get() == "Ya" else "n"
            enc_key = enckey_entry.get() if encrypt == "y" else ""

            # validasi ukuran video dan file
            allowed = check_capacity(input_video_path, data, mode, scheme, encrypt, enc_key)
            if not allowed :
                loading_popup.destroy()
                messagebox.showerror("Error", "Ukuran file/pesan terlalu besar untuk disisipkan ke dalam video!")
                return
                
            # proses embedding
            if method_var.get() == "randomize":
                if not key_entry.get() : 
                    raise Exception("Key tidak boleh kosong!")
                embed_video_random(input_video_path, final_output_path, data, mode, key_entry.get(), scheme, encrypt, enc_key)
            else:
                embed_video(input_video_path, final_output_path, data, mode, scheme, encrypt, enc_key)

            loading_popup.destroy()

            messagebox.showinfo("Sukses", f"Embedding Selesai!\nDisimpan di: {out_filename}")
            show_main_menu()

        except Exception as e:
            if loading_popup:
                loading_popup.destroy()
            messagebox.showerror("Error", str(e))

    tk.Button(scroll_frame, text="Jalankan Embedding", command=run_embed_process, bg="#27ae60", fg="white", width=25, height=2).pack(pady=20)
    tk.Button(scroll_frame, text="Kembali ke Menu", command=show_main_menu).pack()

def show_extract_screen():
    clear_window()
    root.geometry("900x700")
    global input_video_path
    input_video_path = ""

    tk.Label(root, text="Menu Extracting", font=("Arial", 14, "bold")).pack(pady=10)

    # 1. Pilih Video
    tk.Label(root, text="1. Pilih Video Stego (.avi):", font=("Arial", 10, "bold")).pack(pady=5)
    btn_video = tk.Button(root, text="Cari Video", command=lambda: browse_input_video(lbl_video))
    btn_video.pack(pady=5)
    lbl_video = tk.Label(root, text="Belum ada video dipilih", fg="gray")
    lbl_video.pack()

    # 2. Scheme
    tk.Label(root, text="\n2. Scheme (R,G,B):", font=("Arial", 10, "bold")).pack(pady=5)
    scheme_var = tk.StringVar(value="3,3,2")
    tk.OptionMenu(root, scheme_var, "3,3,2", "2,2,4", "1,1,6").pack(pady=5)

    # Area Hasil
    result_container = tk.LabelFrame(root, text="Hasil Ekstraksi", padx=10, pady=10)
    text_result_area = tk.Text(result_container, height=5, width=50)
    
    file_res_frame = tk.Frame(result_container)

    def run_extract_process():
        text_result_area.pack_forget()
        file_res_frame.pack_forget()
        result_container.pack_forget()

        loading_popup = None

        try:
            loading_popup = load_popup("Ekstraksi sedang berjalan...")
            root.update()

            if not input_video_path: raise Exception("Pilih video!")
            scheme = tuple(map(int, scheme_var.get().split(',')))

            mode, method, encrypt_flag = header_checker(input_video_path, scheme)

            stego_key = ""
            enc_key = ""

            if method == "1" :
                stego_key = input_dialog("Stego Key", "Masukkan Stego Key : ")

            if encrypt_flag == "1" :
                enc_key = input_dialog("Encryption Key", "Masukan kunci enkripsi : ")

            if mode == "1" :
                output_name = input_dialog("Output", "Nama file (kosongkan jika ingin nama file asli) : ")
            else :
                output_name = ""

            if method == "1":
                res_data = extract_video_random(input_video_path, stego_key, enc_key, scheme, output_name)
            else:
                res_data = extract_video(input_video_path, enc_key, scheme, output_name)

            loading_popup.destroy()

            result_container.pack(pady=10, fill="x", padx=40)
            if mode == "0":
                text_result_area.pack()
                text_result_area.delete("1.0", tk.END)
                text_result_area.insert(tk.END, res_data)
            else:
                messagebox.showinfo("Sukses", f"Ekstraksi Selesai!\nDisimpan di: {res_data}")

        except Exception as e:
            if loading_popup:
                loading_popup.destroy()
            messagebox.showerror("Error", str(e))

    tk.Button(root, text="Jalankan Ekstraksi", command=run_extract_process, bg="#e67e22", fg="white", width=25, height=2).pack(pady=20)
    tk.Button(root, text="Kembali ke Menu", command=show_main_menu).pack()

def run_compare():
    clear_window()
    root.geometry("900x700")

    v1 = {"path": ""}
    v2 = {"path": ""}

    tk.Label(root, text = "Comparing", font = ("Arial", 14, "bold")).pack(pady = 10)

    # mengambil video asli
    frame1 = tk.Frame(root)
    frame1.pack(pady = 10)

    tk.Label(frame1, text = "Video Asli").pack()
    lbl1 = tk.Label(frame1, text = "Belum dipilih", fg = "gray")
    lbl1.pack()

    def browse_v1() :
        path = filedialog.askopenfilename(filetypes = [("AVI files", "*.avi")])
        if path :
            v1["path"] = path
            lbl1.config(text = os.path.basename(path))

    tk.Button(frame1, text = "Pilih Video Asli", command = browse_v1).pack(pady = 5)

    # mengambil video stego
    frame2 = tk.Frame(root)
    frame2.pack(pady = 10)

    tk.Label(frame1, text = "Video Stego").pack()
    lbl2 = tk.Label(frame1, text = "Belum dipilih", fg = "gray")
    lbl2.pack()

    def browse_v2() :
        path = filedialog.askopenfilename(filetypes = [("AVI files", "*.avi")])
        if path :
            v2["path"] = path
            lbl2.config(text = os.path.basename(path))

    tk.Button(frame1, text = "Pilih Video Stego", command = browse_v2).pack(pady = 5)

    # bagian hasil comparing dan histogram
    result_frame = tk.Frame(root)
    result_frame.pack(pady = 10)

    mse_label = tk.Label(result_frame, text = "MSE : -", font = ("Arial", 11))
    mse_label.pack()

    psnr_label = tk.Label(result_frame, text = "PSNR : -", font = ("Arial", 11))
    psnr_label.pack()

    hist_frame = tk.Frame(root)
    hist_frame.pack(pady = 10)

    # proses comparing
    def process():
        if not v1["path"] or not v2["path"] :
            messagebox.showerror("Error", "Pilih Video!")
            return
        
        mse, psnr = compare_videos(v1["path"], v2["path"])

        mse_label.config(text=f"MSE : {mse:.10f}")
        psnr_label.config(text=f"PSNR : {psnr:.10f} dB")

        # mengambil frame
        cap1 = cv2.VideoCapture(v1["path"])
        cap2 = cv2.VideoCapture(v2["path"])

        ret1, frame1 = cap1.read()
        ret2, frame2 = cap2.read()

        cap1.release()
        cap2.release()

        if not ret1 or not ret2:
            return

        # bikin histogram
        fig, axes = plt.subplots(1,2,figsize=(8,3))

        colors = ('b','g','r')

        # histogram video asli
        for i, color in enumerate(colors):
            hist1 = cv2.calcHist([frame1],[i],None,[256],[0,256])
            axes[0].plot(hist1, color = color)

        axes[0].set_title("Original Video")
        axes[0].set_xlim([0,256])

        for i, color in enumerate(colors) :
            hist2 = cv2.calcHist([frame2],[i],None,[256],[0,256])
            axes[1].plot(hist2, color = color)

        axes[1].set_title("Stego Video")
        axes[1].set_xlim([0, 256])

        # clear lama
        for w in hist_frame.winfo_children():
            w.destroy()

        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        canvas = FigureCanvasTkAgg(fig, master=hist_frame)
        canvas.draw()
        canvas.get_tk_widget().pack()

    tk.Button(root, text="Bandingkan", bg="#3498db", fg="white",
                command=process, width=25, height=2).pack(pady=15)

    tk.Button(root, text="Kembali ke Menu", command=show_main_menu).pack()

root = tk.Tk()
root.title("Steganografi Video App")
show_main_menu()
root.mainloop()
