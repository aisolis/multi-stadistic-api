import requests
import random
import json

# Definir URL y encabezados
url = 'http://127.0.0.1:5000/insertar_venta'
headers = {'Content-Type': 'application/json'}

# Definir los meses
meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

# Generar 50 ventas
for _ in range(50):
    anioVenta = random.randint(2020, 2024)
    mes = random.choice(meses)
    unidadesVendidas = random.randint(1, 3000)  # Unidades entre 1 y 3000
    ganancias = unidadesVendidas * 50  # Precio por unidad es 50

    # Crear los datos de la venta
    data = {
        "anioVenta": anioVenta,
        "mes": mes,
        "unidadesVendidas": unidadesVendidas,
        "ganancias": ganancias
    }

    # Realizar la solicitud POST
    response = requests.post(url, headers=headers, data=json.dumps(data))

    # Comprobar si la solicitud fue exitosa
    if response.status_code == 200:
        print(f"Venta insertada: {data}")
    else:
        print(f"Error al insertar la venta: {response.status_code} - {response.text}")
