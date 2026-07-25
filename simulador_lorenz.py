import numpy as np
import matplotlib.pyplot as plt

def rk4_paso(estado, dt, sigma, rho, betha):
    x, y, z = estado

    k1x = sigma * (y-x)
    k1y = x*(rho - z) - y
    k1z = x*y - betha*z

    tx = x + k1x * 0.5 * dt
    ty = y + k1y * 0.5 * dt
    tz = z + k1z * 0.5 * dt


    k2x = sigma * (ty-tx)
    k2y = x*(rho - z) - y
    k2z = x*y - betha*z

    tx = x + k2x * 0.5 * dt
    ty = y + k2y * 0.5 * dt
    tz = z + k2z * 0.5 * dt


    k3x = sigma * (y-x)
    k3y = x*(rho - z) - y
    k3z = x*y - betha*z

    tx = x + k3x * dt
    ty = y + k3y * dt
    tz = z + k3z * dt

    k4x = sigma * (ty-tx)
    k4y = x*(rho - z) - y
    k4z = x*y - betha*z

    x_nuevo = x + (dt / 6.0) * (k1x + 2.0*k2x + 2.0*k3x + k4x)
    y_nuevo = y + (dt / 6.0) * (k1y + 2.0*k2y + 2.0*k3y + k4y)
    z_nuevo = z + (dt / 6.0) * (k1z + 2.0*k2z + 2.0*k3z + k4z)

    return np.array([x_nuevo, y_nuevo, z_nuevo], dtype=np.float64)

SIGMA = 10.0
RHO = 28.0
BETA = 8.0 / 3.0
DT = 0.01
PASOS = 4000
tiempo = np.linspace(0, PASOS * DT, PASOS)

# Llaves criptográficas (Condiciones iniciales)
# Clave A: Base original
clave_a = np.array([1.0, 1.0, 1.0], dtype=np.float64)

# Clave B: Variación infinitesimal (10^-6 en el eje X)
clave_b = np.array([1.000001, 1.0, 1.0], dtype=np.float64)

# Arreglo para almacenar la divergencia
distancias = np.zeros(PASOS)

print("Iniciando simulación ")

# Bucle principal de evolución temporal
for t in range(PASOS):
    # Medir la distancia euclidiana entre las dos trayectorias
    d = np.linalg.norm(clave_a - clave_b)
    distancias[t] = d
    
    # Avanzar un paso en el tiempo para ambas claves
    clave_a = rk4_paso(clave_a, DT, SIGMA, RHO, BETA)
    clave_b = rk4_paso(clave_b, DT, SIGMA, RHO, BETA)

print("¡Simulación completada! Generando gráfico...")

# ==========================================
# GRÁFICA DE RESULTADOS
# ==========================================
plt.figure(figsize=(10, 5))
plt.plot(tiempo, distancias, color='crimson', linewidth=1.5, label='Divergencia entre Clave A y Clave B')
plt.yscale('log')
plt.xlabel('Tiempo de simulación (t)')
plt.ylabel('Distancia Euclidiana (Escala Log)')
plt.title('Demostración del Efecto Mariposa para Seguridad Criptográfica')
plt.grid(True, which="both", ls="--", alpha=0.6)
plt.legend()
plt.tight_layout()

# Guardar la imagen localmente
plt.savefig('divergencia_caotica_python.png', dpi=300)
plt.show()