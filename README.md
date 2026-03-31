Anggota Kelompok :
Nawaf Amjad R - 181223073
Zheannetta Apple Haihando - 18223105
Michael Jeremi Bungaran S - 18221136

# Steganografi Video App

Aplikasi ini merupakan implementasi **steganografi pada video (.avi)** menggunakan metode **Least Significant Bit (LSB)** dengan dukungan:

* LSB Sequential
* LSB Randomized (dengan stego-key)
* Enkripsi payload (A5/1)
* GUI interaktif (Tkinter)
* Analisis kualitas video (MSE & PSNR + Histogram)

---

# Fitur Utama

# 1. Embedding (Penyisipan Pesan)

* Mendukung **pesan teks dan file**
* Penyisipan menggunakan:

  * LSB Sequential
  * LSB Randomized (berbasis key)
* Enkripsi payload (opsional)
* Validasi kapasitas video sebelum embedding
* Penyimpanan metadata dalam header:

  * Tipe pesan (text/file)
  * Extension file
  * Nama file
  * Ukuran file
  * Status enkripsi
  * Metode embedding

---

# 2. Extracting (Ekstraksi Pesan)

* Otomatis membaca header
* Meminta input:

  * Stego key (jika random)
  * Encryption key (jika terenkripsi)
* Mendukung:

  * Output teks
  * Output file (dengan nama asli atau custom)

---

# 3. Comparing (Analisis Video)

* Menghitung:

  * **MSE (Mean Squared Error)**
  * **PSNR (Peak Signal-to-Noise Ratio)**
* Menampilkan histogram:
  * Video asli
  * Video stego

---

# Konsep yang Digunakan

# 1. LSB Steganography

Bit pesan disisipkan ke bit terakhir pixel RGB pada video.

# 2. Sequential vs Random

* **Sequential** → berurutan
* **Randomized** → berdasarkan stego-key (lebih aman)

# 3. Encryption (A5/1)

Payload dapat dienkripsi sebelum embedding untuk meningkatkan keamanan.

# 4. Header Metadata

Digunakan untuk memastikan proses ekstraksi berjalan benar.

---

# Struktur Project

```
.
├── main.py                  # GUI utama
├── stegovideo_sequential.py # LSB Sequential
├── stegovideo_random.py     # LSB Randomized
├── converter.py             # Konversi bits ↔ bytes
├── a5_1.py                  # Enkripsi A5/1
├── comparison.py            # MSE, PSNR, histogram
├── dummy_files/             # file uji coba
└── README.md
```

---

# Cara Menjalankan

# 1. Install Dependency

```bash
pip install opencv-python matplotlib numpy
```

---

# 2. Jalankan Program

```bash
python main.py
```

---

# Cara Penggunaan

# Embedding

1. Pilih video asli yang belum disisipi pesan (.avi)
2. Pilih tipe pesan (text/file)
3. Masukkan pesan / file
4. Pilih:
   * Enkripsi (masukan encryption key jika memilih dienkripsi)
   * Metode LSB (masukan stego key jika memilih LSB Randomize)
   * Scheme RGB
5. Klik **Jalankan Embedding**

---

# Extracting

1. Pilih video stego
2. Masukkan:
   * Stego key (jika LSB Randomize)
   * Encryption key (jika terenkripsi)
3. Pilih nama output (opsional, kalau kosong akan disimpan dalam nama file asli)
4. Klik **Jalankan Ekstraksi**

---

### Comparing

1. Pilih video asli
2. Pilih video stego
3. Klik **Bandingkan**
4. Lihat:

   * MSE
   * PSNR
   * Histogram

---

## Catatan Penting

* Format video: **.avi (disarankan lossless)**
* Kapasitas tergantung:

  * Resolusi video
  * Jumlah frame
  * Scheme LSB
* Jika file terlalu besar → embedding akan ditolak

---

## Known Issues

* GUI dapat freeze saat proses embedding (karena proses berat OpenCV)
* Belum menggunakan threading untuk background processing
* Codec tertentu mungkin tidak kompatibel

---

## 👨‍💻 Author

Dibuat untuk tugas **Kriptografi / Keamanan Informasi** oleh Nawaf Amjad R (18223073), Zheannetta Apple Haihando (18223105), dan Michael Jeremi Bungaran S (18221136)

---

## 🏁 Kesimpulan

Aplikasi ini berhasil mengimplementasikan:

* Steganografi berbasis video
* Enkripsi payload
* GUI interaktif
* Analisis kualitas

Dengan tingkat keberhasilan ekstraksi yang tinggi dan distorsi minimal.

---
