import numpy as np
import os
import hashlib
from pathlib import Path

def rk4_paso(estado, dt, sigma, rho, betha):
    x, y, z = estado

    k1x = sigma * (y-x)
    k1y = x*(rho - z) - y
    k1z = x*y - betha*z

    tx = x + k1x * 0.5 * dt
    ty = y + k1y * 0.5 * dt
    tz = z + k1z * 0.5 * dt

    k2x = sigma * (ty-tx)
    k2y = tx*(rho - tz) - ty
    k2z = tx*ty - betha*tz

    tx = x + k2x * 0.5 * dt
    ty = y + k2y * 0.5 * dt
    tz = z + k2z * 0.5 * dt

    k3x = sigma * (ty-tx)
    k3y = tx*(rho - tz) - ty
    k3z = tx*ty - betha*tz

    tx = x + k3x * dt
    ty = y + k3y * dt
    tz = z + k3z * dt

    k4x = sigma * (ty-tx)
    k4y = tx*(rho - tz) - ty
    k4z = tx*ty - betha*tz

    x_nuevo = x + (dt / 6.0) * (k1x + 2.0*k2x + 2.0*k3x + k4x)
    y_nuevo = y + (dt / 6.0) * (k1y + 2.0*k2y + 2.0*k3y + k4y)
    z_nuevo = z + (dt / 6.0) * (k1z + 2.0*k2z + 2.0*k3z + k4z)

    return np.array([x_nuevo, y_nuevo, z_nuevo], dtype=np.float64)


def generar_keystream(llave_estado, num_bits, dt=0.01, sigma=10.0, rho=28.0, beta=2.6667):
    estado = np.copy(llave_estado)
    keystream = np.zeros(num_bits, dtype=np.uint8)
    
    for _ in range(1000):
        estado = rk4_paso(estado, dt, sigma, rho, beta)
        
    for i in range(num_bits):
        estado = rk4_paso(estado, dt, sigma, rho, beta)
        x = estado[0]
        valor_profundo = int(abs(x * 1e6))
        keystream[i] = valor_profundo % 2
        
    return keystream

def adaptar_ci(clave: bytes):
    hash_total = hashlib.pbkdf2_hmac(
            hash_name ="sha256",
            password=clave,
            salt = clave,
            iterations=10000,
            dklen=24
            )

    bytes_x = hash_total[0:8]
    bytes_y = hash_total[8:16]
    bytes_z = hash_total[16:24]
    
    MAX64 = 2**64 - 1

    x_int = int.from_bytes(bytes_x, byteorder="big")
    y_int = int.from_bytes(bytes_y, byteorder="big")
    z_int = int.from_bytes(bytes_z, byteorder="big")
    
    x0 = (x_int / MAX64) * 40 - 20
    y0 = (y_int / MAX64) * 40 - 20
    z0 = (z_int / MAX64) * 40 - 20
    
    return np.array([x0, y0, z0], dtype=np.float64)

def borrado_seguro(ruta_archivo):
    try:
        tamaño = os.path.getsize(ruta_archivo)
        with open(ruta_archivo, "r+b") as f:
            f.write(os.urandom(tamaño)) 
            f.flush()                   
            os.fsync(f.fileno())       
        os.remove(ruta_archivo)        
    except Exception as e:
        print(f"No se pudo realizar el borrado seguro en {ruta_archivo}. Error: {e}")


def cifrar(ruta, llave_adaptada):
    with open(ruta, 'rb') as f:
        datos = f.read()

    if not datos: return 

    texto_binario = np.unpackbits(np.frombuffer(datos, dtype=np.uint8))
    cantidad_bits = len(texto_binario)

    llave = generar_keystream(llave_adaptada, cantidad_bits)

    bits_cifrados = np.bitwise_xor(texto_binario, llave)
    datos_cifrados = np.packbits(bits_cifrados).tobytes()

    ruta_salida = f"{ruta}.enc"
    with open(ruta_salida, 'wb') as f:
        f.write(datos_cifrados)
        
    borrado_seguro(ruta)
    print(f"Encriptado: {ruta_salida}")

if __name__ == "__main__":
    clave_generada = os.urandom(16)
    llave_adaptada = adaptar_ci(clave_generada)

    print(f"\nClave: {clave_generada.hex()}")

    ruta_input = input("Ingrese la ruta a cifrar: ")
    ruta_obj = Path(ruta_input)

    if ruta_obj.is_file():
        cifrar(str(ruta_obj), llave_adaptada)
    elif ruta_obj.is_dir():
        for archivo_path in ruta_obj.rglob('*'):
            if archivo_path.is_file() and not archivo_path.suffix == '.enc':
                cifrar(str(archivo_path), llave_adaptada)
    else: 
        print("La ruta no existe.")