"""
Implementasi A5/1 Stream Cipher untuk Steganografi Video AVI.
Referensi: GSM A5/1 Specification (ETSI TS 100 922)

Konvensi register:
  - Index 0 = bit paling kiri (newest input / MSB sisi input)
  - Index N-1 = bit paling kanan (oldest / output bit)
  - Bit feedback masuk di index 0, dishift ke kanan
  - Output diambil dari index terbesar (r1[18], r2[21], r3[22])

Register:
  R1: 19 bit, tap feedback di bit 18, 17, 16, 13  | clocking bit: bit 8
  R2: 22 bit, tap feedback di bit 21, 20          | clocking bit: bit 10
  R3: 23 bit, tap feedback di bit 22, 21, 20, 7   | clocking bit: bit 10
"""

BLOCK_SIZE_BITS  = 228  
BLOCK_SIZE_BYTES = 28   

class A5_1:
    R1_LEN = 19
    R2_LEN = 22
    R3_LEN = 23

    R1_TAPS = [18, 17, 16, 13]
    R2_TAPS = [21, 20]
    R3_TAPS = [22, 21, 20, 7]

    R1_CLOCK = 8
    R2_CLOCK = 10
    R3_CLOCK = 10

    def __init__(self, key_64bit: str, frame_number: int = 0):
        """
        Args:
            key_64bit:     String biner 64-bit (mis. "101010...").
            frame_number:  Nomor frame 22-bit (0 s.d. 2^22-1).
                           Setiap blok 228-bit harus menggunakan Fn berbeda.
        """
        if len(key_64bit) != 64 or not all(c in '01' for c in key_64bit):
            raise ValueError("Kunci A5/1 harus berupa string biner 64 karakter.")
        if not (0 <= frame_number < (1 << 22)):
            raise ValueError("Frame number harus bernilai 0 s.d. 2^22 - 1.")

        self.key_64bit = key_64bit
        self.frame_number = frame_number

        self.r1 = [0] * self.R1_LEN
        self.r2 = [0] * self.R2_LEN
        self.r3 = [0] * self.R3_LEN

        self._initialize()

    # inisialisasi
    def _clock_all_no_stop(self):
        # tanpa stop-clock
        fb1 = 0
        for t in self.R1_TAPS:
            fb1 ^= self.r1[t]
        self.r1 = [fb1] + self.r1[:-1]

        fb2 = 0
        for t in self.R2_TAPS:
            fb2 ^= self.r2[t]
        self.r2 = [fb2] + self.r2[:-1]

        fb3 = 0
        for t in self.R3_TAPS:
            fb3 ^= self.r3[t]
        self.r3 = [fb3] + self.r3[:-1]

    def _initialize(self):
        # key loading
        key_bits = [int(b) for b in self.key_64bit]
        for bit in key_bits:
            self.r1[-1] ^= bit
            self.r2[-1] ^= bit
            self.r3[-1] ^= bit
            self._clock_all_no_stop()

        # frame number loading
        fn_bits = [(self.frame_number >> i) & 1 for i in range(21, -1, -1)]
        for bit in fn_bits:
            self.r1[-1] ^= bit
            self.r2[-1] ^= bit
            self.r3[-1] ^= bit
            self._clock_all_no_stop()

        # warm-up
        for _ in range(100):
            self._clock_with_majority()

    # keystream generation
    def _majority(self):
        # hitung bit mayoritas
        b1 = self.r1[self.R1_CLOCK]
        b2 = self.r2[self.R2_CLOCK]
        b3 = self.r3[self.R3_CLOCK]
        return (b1 & b2) | (b1 & b3) | (b2 & b3)

    def _clock_with_majority(self):
        """Clock register yang clocking bit-nya == mayoritas (stop-clock rule)."""
        m = self._majority()

        if self.r1[self.R1_CLOCK] == m:
            fb = 0
            for t in self.R1_TAPS:
                fb ^= self.r1[t]
            self.r1 = [fb] + self.r1[:-1]

        if self.r2[self.R2_CLOCK] == m:
            fb = 0
            for t in self.R2_TAPS:
                fb ^= self.r2[t]
            self.r2 = [fb] + self.r2[:-1]

        if self.r3[self.R3_CLOCK] == m:
            fb = 0
            for t in self.R3_TAPS:
                fb ^= self.r3[t]
            self.r3 = [fb] + self.r3[:-1]

        # Output = XOR dari bit paling kanan tiap register
        return self.r1[-1] ^ self.r2[-1] ^ self.r3[-1]

    def generate_keystream(self, length_bits: int) -> list[int]:
        # generate keystream
        return [self._clock_with_majority() for _ in range(length_bits)]

    # enkrip dekrip
    def crypt(self, data: bytes) -> bytes:
        # XOR data dengan keystream
        keystream = self.generate_keystream(len(data) * 8)
        result = bytearray()
        for i, byte in enumerate(data):
            ks_byte = 0
            for j in range(8):
                ks_byte = (ks_byte << 1) | keystream[i * 8 + j]
            result.append(byte ^ ks_byte)
        return bytes(result)


# enkrip blok 228-bit w/ Fn otomatis
def encrypt_payload(data: bytes, key_64bit: str, start_fn: int = 0) -> bytes:
    output = bytearray()
    fn = start_fn
    i = 0
    while i < len(data):
        block = data[i: i + BLOCK_SIZE_BYTES]
        i += BLOCK_SIZE_BYTES
        cipher = A5_1(key_64bit, fn % (1 << 22))
        output.extend(cipher.crypt(block))
        fn += 1
    return bytes(output)

# dekrip hasil enkrip payload tadi
def decrypt_payload(data: bytes, key_64bit: str, original_length_bytes: int,
                    start_fn: int = 0) -> bytes:
    # XOR simetris
    decrypted = encrypt_payload(data[:original_length_bytes], key_64bit, start_fn)
    return decrypted


# testing
if __name__ == "__main__":
    print("=== Test A5/1 ===\n")

    KEY = "1010101011110000101010101111000010101010111100001010101011110000"

    # test 1: teks pendek
    plaintext = "Halo Dunia! Ini pesan rahasia untuk steganografi."
    print(f"[Test 1] Plaintext : {plaintext}")

    enc = encrypt_payload(plaintext.encode(), KEY)
    print(f"[Test 1] Ciphertext (hex): {enc.hex()}")

    dec = decrypt_payload(enc, KEY, len(plaintext.encode()))
    print(f"[Test 1] Decrypted : {dec.decode()}")
    assert dec.decode() == plaintext, "Test 1 GAGAL"
    print("[Test 1] Berhasil\n")

    # test 2: blok besar (> 228 bit, multi-blok)
    long_msg = "A" * 200  
    enc2 = encrypt_payload(long_msg.encode(), KEY)
    dec2 = decrypt_payload(enc2, KEY, len(long_msg.encode()))
    assert dec2.decode() == long_msg, "Test 2 GAGAL"
    print(f"[Test 2] Pesan 200 karakter multi-blok: Berhasil\n")

    # test 3: bytes arbitrary
    binary_data = bytes(range(256))
    enc3 = encrypt_payload(binary_data, KEY)
    dec3 = decrypt_payload(enc3, KEY, len(binary_data))
    assert dec3 == binary_data, "Test 3 GAGAL"
    print(f"[Test 3] Data binary 256 byte: Berhasil\n")

    # test 4: Fn berbeda menghasilkan keystream berbeda
    c1 = A5_1(KEY, frame_number=0)
    c2 = A5_1(KEY, frame_number=1)
    ks1 = c1.generate_keystream(64)
    ks2 = c2.generate_keystream(64)
    assert ks1 != ks2, "Test 4 GAGAL: Fn 0 dan Fn 1 hasilkan keystream sama"
    print("[Test 4] Fn berbeda → keystream berbeda: Berhasil\n")

    print("=== Semua test lulus ===")