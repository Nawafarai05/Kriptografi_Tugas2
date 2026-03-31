import hashlib

def calculate_sha256(filepath):
    # ngitung hash SHA-256 dari file yang diberikan
    sha256_hash = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            # Membaca file dalam blok untuk menghemat memori
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        return None

def verify_integrity(original_file, extracted_file):
    # bandingkan hash SHA-256 antara file sisip asli dan file hasil ektraksi
    hash_original = calculate_sha256(original_file)
    hash_extracted = calculate_sha256(extracted_file)
    
    if hash_original is None or hash_extracted is None:
        return False, hash_original, hash_extracted
        
    is_match = hash_original == hash_extracted
    return is_match, hash_original, hash_extracted

if __name__ == "__main__":
    file_ori = input("Masukkan file sisip original : ")
    file_ext = input("Masukkan file sisi hasil ekstraksi : ")
    
    file_ori = "dummy_files/" + file_ori
    
    match, h1, h2 = verify_integrity(file_ori, file_ext)
    
    print(f"Hash File Asli    : {h1}")
    print(f"Hash File Ekstrak : {h2}")
    
    if match:
        print("Integritas Terjamin: File Identik!")
    else:
        print("Peringatan: File Telah Berubah atau Korup!")
