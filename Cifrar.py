import numpy as np
import os
import hashlib

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
        bit = valor_profundo % 2
        
        keystream[i] = bit
        
    return keystream

def texto_a_bits(texto):

    bits = []
    for letra in texto:
        binario = bin(ord(letra))[2:].zfill(8)

        for bit in binario:
            bits.append(int(bit))

    return np.array(bits, dtype=np.uint8)

def bits_a_texto(bits):
    texto = ""

    for i in range(0, len(bits), 8):
        byte = bits[i:i+8]

        binario = ""

        for bit in byte:
            binario += str(bit)

        numero = int(binario, 2)

        letra = chr(numero)
        texto += letra
    return texto

def cifrado(mensaje, llave):

    texto_cifrado = np.bitwise_xor(mensaje, llave)

    return texto_cifrado

def adaptar_ci(password: str, salt_existence: bytes = None):

    if salt_existence is None:
        salt = os.urandom(16)

    else:
        salt = salt_existence

    hash_total = hashlib.pbkdf2_hmac(
            hash_name ="sha256",
            password=password.encode("utf-8"),
            salt = salt,
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
    
    return x0, y0, z0, salt




contraseña = input("Ingrese una contraseña:")
x, y, z, salt = adaptar_ci(contraseña)

llave_adaptada = np.array([x, y, z], dtype=np.float64)

texto = input("Ingrese un texto: ")

texto_binario = texto_a_bits(texto)

cantidad_bits = len(texto_binario)

llave = generar_keystream(llave_adaptada, cantidad_bits)

bits_cifrados = cifrado(texto_binario, llave)
print(f"Salt: {salt.hex()}")
print(f"El texto cifrado es: {bits_cifrados}\n")

