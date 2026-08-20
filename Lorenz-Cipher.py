#!/usr/bin/env python3
import os
import sys 
import time 
import numpy as np 
import hashlib
from pathlib import Path
from numba import njit

C = "\033[96m" 
G = "\033[92m" 
R = "\033[91m" 
Y = "\033[93m" 
B = "\033[1m"  
W = "\033[0m"  

@njit
def rk4_step(state, dt, sigma, rho, beta):
    x, y, z = state

    k1x = sigma * (y - x)
    k1y = x * (rho - z) - y
    k1z = x * y - beta * z

    tx = x + k1x * 0.5 * dt
    ty = y + k1y * 0.5 * dt
    tz = z + k1z * 0.5 * dt

    k2x = sigma * (ty - tx)
    k2y = tx * (rho - tz) - ty
    k2z = tx * ty - beta * tz

    tx = x + k2x * 0.5 * dt
    ty = y + k2y * 0.5 * dt
    tz = z + k2z * 0.5 * dt

    k3x = sigma * (ty - tx)
    k3y = tx * (rho - tz) - ty
    k3z = tx * ty - beta * tz

    tx = x + k3x * dt
    ty = y + k3y * dt
    tz = z + k3z * dt

    k4x = sigma * (ty - tx)
    k4y = tx * (rho - tz) - ty
    k4z = tx * ty - beta * tz

    nx = x + (dt / 6.0) * (k1x + 2.0 * k2x + 2.0 * k3x + k4x)
    ny = y + (dt / 6.0) * (k1y + 2.0 * k2y + 2.0 * k3y + k4y)
    nz = z + (dt / 6.0) * (k1z + 2.0 * k2z + 2.0 * k3z + k4z)

    return np.array([nx, ny, nz], dtype=np.float64)

@njit
def generate_keystream(initial_state, num_bits, dt=0.01, sigma=10.0, rho=28.0, beta=2.6667):
    state = np.copy(initial_state)
    keystream = np.zeros(num_bits, dtype=np.uint8)
    
    for _ in range(1000):
        state = rk4_step(state, dt, sigma, rho, beta)
        
    for i in range(num_bits):
        state = rk4_step(state, dt, sigma, rho, beta)
        keystream[i] = int(abs(state[0] * 1e6)) % 2
        
    return keystream

def derive_initial_conditions(master_key: bytes):
    hashed = hashlib.pbkdf2_hmac(
        hash_name="sha256",
        password=master_key,
        salt=master_key,
        iterations=10000,
        dklen=24
    )

    bx = hashed[0:8]
    by = hashed[8:16]
    bz = hashed[16:24]
    
    max64 = 2**64 - 1
    
    x_int = int.from_bytes(bx, byteorder="big")
    y_int = int.from_bytes(by, byteorder="big")
    z_int = int.from_bytes(bz, byteorder="big")
    
    x0 = (x_int / max64) * 40 - 20
    y0 = (y_int / max64) * 40 - 20
    z0 = (z_int / max64) * 40 - 20
    
    return np.array([x0, y0, z0], dtype=np.float64)

def secure_delete(target_path):
    try:
        size = os.path.getsize(target_path)
        with open(target_path, "r+b") as f:
            f.write(os.urandom(size)) 
            f.flush()                   
            os.fsync(f.fileno())       
        os.remove(target_path)        
    except Exception as e:
        print(f"{R}[X] Secure wipe failed on {target_path}: {e}{W}")

def encrypt_target(target_path, derived_key):
    with open(target_path, 'rb') as f:
        data = f.read()

    if not data: return 

    bin_data = np.unpackbits(np.frombuffer(data, dtype=np.uint8))
    keystream = generate_keystream(derived_key, len(bin_data))

    encrypted_bits = np.bitwise_xor(bin_data, keystream)
    encrypted_data = np.packbits(encrypted_bits).tobytes()

    out_path = f"{target_path}.enc"
    with open(out_path, 'wb') as f:
        f.write(encrypted_data)
        
    secure_delete(target_path)
    print(f"{G}[+] Encrypted and wiped: {out_path}{W}")

def decrypt_target(target_path, derived_key):
    with open(target_path, 'rb') as f:
        data = f.read()

    if not data: return

    bin_data = np.unpackbits(np.frombuffer(data, dtype=np.uint8))
    keystream = generate_keystream(derived_key, len(bin_data))
    
    decrypted_bits = np.bitwise_xor(bin_data, keystream)
    decrypted_data = np.packbits(decrypted_bits).tobytes()

    out_path = target_path.with_suffix('')
    with open(out_path, 'wb') as f:
        f.write(decrypted_data)
        
    os.remove(target_path)
    print(f"{G}[+] Decrypted and restored: {out_path}{W}")

def clear_screen():
    os.system('clear' if os.name == 'posix' else 'cls')

def show_banner():
    clear_screen()
    btc_address = "0334f35bdf6b7f7b3ef95704920d487dccc142cfe1e3688cc79336ad0388d8faf5"
    
    logo = f"""{C}{B}
  _                                  _____ _       _               
 | |    ___  _ __ ___ _ __  ____    / ____(_)     | |              
 | |   / _ \| '__/ _ \ '_ \|_  /   | |     _ _ __ | |__   ___ _ __ 
 | |  | (_) | | |  __/ | | |/ /    | |    | | '_ \| '_ \ / _ \ '__|
 | |___\___/|_|  \___|_| |_/___|   | |____| | |_) | | | |  __/ |   
 |______|                           \_____|_| .__/|_| |_|\___|_|   
                                            | |                    
                                            |_|                    
    {W}{Y}:: by: l01-jcc ::{W}
    {W}{G}BTC Support:{W} {btc_address}
    """
    print(logo)

def main_menu():
    while True:
        show_banner()
        print(f" {G}[ 1 ]{W} Encrypt target (File/Directory)")
        print(f" {G}[ 2 ]{W} Decrypt target (File/Directory)")
        print(f" {R}[ 3 ]{W} Exit\n")
        
        choice = input(f"{B} lorenz > {W}")

        if choice == "1":
            print(f"\n{C}[*] Initiating encryption protocol...{W}")
            master_key = os.urandom(16)
            derived_key = derive_initial_conditions(master_key)
            
            print(f"{Y}[!] WARNING: Backup this key. Data loss is irreversible if lost:{W}")
            print(f"{B}Key: {master_key.hex()}{W}\n")
            
            target_input = input(f"{C}[?] Target path: {W}")
            target_obj = Path(target_input)
            
            if target_obj.is_file():
                encrypt_target(str(target_obj), derived_key)
            elif target_obj.is_dir():
                for filepath in target_obj.rglob('*'):
                    if filepath.is_file() and filepath.suffix != '.enc':
                        encrypt_target(str(filepath), derived_key)
            else: 
                print(f"{R}[X] Path not found.{W}")
            
            input(f"\n{Y}[Press ENTER to return]{W}")

        elif choice == "2":
            print(f"\n{C}[*] Initiating decryption protocol...{W}")
            key_input = input(f"{C}[?] Master key (hex): {W}")
            
            try:
                master_key_bytes = bytes.fromhex(key_input)
                derived_key = derive_initial_conditions(master_key_bytes)
                
                target_input = input(f"{C}[?] Target path: {W}")
                target_obj = Path(target_input)
                
                if target_obj.is_file() and target_obj.suffix == '.enc':
                    decrypt_target(target_obj, derived_key)
                elif target_obj.is_dir():
                    for filepath in target_obj.rglob('*.enc'):
                        if filepath.is_file():
                            decrypt_target(filepath, derived_key)
                else:
                    print(f"{R}[X] Invalid path or missing .enc files.{W}")
                
            except ValueError:
                print(f"{R}[X] Error: Invalid hexadecimal key.{W}")
                
            input(f"\n{Y}[Press ENTER to return]{W}")

        elif choice == "3":
            print(f"\n{R}[*] Terminating session.{W}\n")
            time.sleep(1)
            clear_screen()
            sys.exit()

        else:
            print(f"\n{R}[X] Invalid selection.{W}")
            time.sleep(1)

if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print(f"\n\n{R}[*] Manual interrupt detected. Exiting...{W}\n")
        sys.exit()