import subprocess
import os
import re

# --- CONFIGURARE ---
# Asigura-te ca aceasta cale este corecta
EAC3TO_PATH = r"D:\Encode\eac3to\eac3to.exe"
# --- SFARSIT CONFIGURARE ---

def main():
    """ Functia principala a scriptului. """
    if not os.path.exists(EAC3TO_PATH):
        print(f"EROARE: eac3to.exe nu a fost gasit la calea: {EAC3TO_PATH}")
        input("Apasati Enter pentru a inchide...")
        return

    bluray_path = input("--> Trageti folderul Blu-ray in aceasta fereastra si apasati Enter: ").strip('"')
    if not os.path.isdir(bluray_path):
        print("EROARE: Calea introdusa nu este un folder valid.")
        input("Apasati Enter pentru a inchide...")
        return

    print("\n--- Se scaneaza discul pentru playlist-uri...")
    try:
        result = subprocess.run([EAC3TO_PATH, bluray_path], capture_output=True, text=True, check=True, encoding='utf-8')
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"EROARE la scanarea discului:\n{e.stderr}")
        input("Apasati Enter pentru a inchide...")
        return
        
    selected_playlist = input("--> Alegeti numarul playlist-ului dorit: ")

    print(f"\n--- Se analizeaza piesele din playlist-ul {selected_playlist}...")
    try:
        result = subprocess.run([EAC3TO_PATH, bluray_path, f"{selected_playlist})"], capture_output=True, text=True, check=True, encoding='utf-8')
        track_lines = result.stdout.splitlines()
    except subprocess.CalledProcessError as e:
        print(f"EROARE la analizarea playlist-ului {selected_playlist}:\n{e.stderr}")
        input("Apasati Enter pentru a inchide...")
        return

    # Adaugam ghilimele in jurul cailor care pot contine spatii
    final_command_args = [f'"{EAC3TO_PATH}"', f'"{bluray_path}"', f"{selected_playlist})"]
    subtitle_counters = {}
    commentary_counter = 0
    
    # Pre-procesare pentru a numara totalul de subtitrari pe limba
    total_subtitle_counts = {}
    for line in track_lines:
        if "Subtitle (PGS)" in line:
            lang_match = re.search(r'Subtitle \(PGS\),\s*(\w+)', line)
            if lang_match:
                lang_full = lang_match.group(1)
                lang_code = lang_full[:3].lower()
                total_subtitle_counts[lang_code] = total_subtitle_counts.get(lang_code, 0) + 1

    for line in track_lines:
        match = re.match(r'^\s*(\d+):\s+(.*)', line)
        if not match:
            continue

        track_num, description = match.groups()
        
        if "Chapters" in description:
            print(f"  [+] Gasit: Capitole (Track {track_num})")
            final_command_args.append(f'{track_num}: "{os.path.join(bluray_path, "chapters.txt")}"')
        
        elif track_num == '2' and ("h264" in description.lower() or "hevc" in description.lower() or "vc-1" in description.lower()):
            print(f"  [+] Gasit: Video (Track {track_num})")
            final_command_args.append(f'{track_num}: "{os.path.join(bluray_path, "video.*")}"')
        
        # --- ORDINEA CORECTA A LOGICII ---
        # 1. Verificam INTÂI daca este o subtitrare, indiferent de limba.
        elif "Subtitle (PGS)" in description:
            lang_match = re.search(r'Subtitle \(PGS\),\s*(\w+)', description)
            if lang_match:
                lang_full = lang_match.group(1)
                lang_code = lang_full[:3].lower()
                
                subtitle_counters[lang_code] = subtitle_counters.get(lang_code, 0) + 1
                count = subtitle_counters[lang_code]
                
                if total_subtitle_counts.get(lang_code, 1) > 1:
                    filename = f"{lang_code}{count}.sup"
                else:
                    filename = f"{lang_code}.sup"

                print(f"  [+] Gasit: Subtitrare {lang_full} (Track {track_num}) -> {filename}")
                final_command_args.append(f'{track_num}: "{os.path.join(bluray_path, filename)}"')
        
        # 2. ABIA APOI aplicam regula pentru AUDIO in Engleza la ce a mai ramas.
        elif "English" in description:
            if "TrueHD" in description:
                print(f"  [+] Gasit: Audio ENGLISH TrueHD (Track {track_num})")
                final_command_args.append(f'{track_num}: "{os.path.join(bluray_path, "audio.thd+ac3")}"')
            elif "DTS Master Audio" in description:
                print(f"  [+] Gasit: Audio ENGLISH DTS-HD MA (Track {track_num})")
                final_command_args.append(f'{track_num}: "{os.path.join(bluray_path, "audio.dtsma")}"')
            elif "AC3" in description:
                commentary_counter += 1
                filename = f"commentary{commentary_counter}.ac3"
                print(f"  [+] Gasit: Comentariu ENGLISH AC3 (Track {track_num}) -> {filename}")
                final_command_args.append(f'{track_num}: "{os.path.join(bluray_path, filename)}"')
    
    print("\n--- Comanda finala care va fi executata:")
    final_command_string = " ".join(final_command_args)
    print(final_command_string)
    print("---")
    
    try:
        subprocess.run(final_command_string, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"EROARE la executia finala eac3to:\n{e}")

    print("\nProces terminat.")
    input("Apasati Enter pentru a inchide...")

if __name__ == "__main__":
    main()