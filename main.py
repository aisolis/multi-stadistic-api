from flask import Flask, request, jsonify, send_from_directory
from scipy.stats import pearsonr, norm, t
import numpy as np
from flask_cors import CORS
import matplotlib.pyplot as plt
import os
import threading

from Dbmanager import MongoDBManager

app = Flask(__name__)
CORS(app)  # Habilitar CORS para todas las rutas

IMAGE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'images')
os.makedirs(IMAGE_DIR, exist_ok=True)

@app.route('/hypothesis_test', methods=['POST'])
def hypothesis_test():
    data = request.get_json()
    mu0 = data['miu']
    x_bar = data['media']
    n = data['n']
    alpha = data.get('a', 0.05)
    
    if 'varianza' in data:
        sigma = np.sqrt(data['varianza'])
        critical_value_func = norm.ppf
        distribution_used = "Normal"
    elif 'desvStd' in data:
        sigma = data['desvStd']
        critical_value_func = lambda p, df: t.ppf(p, df)
        distribution_used = "t-Student"
    else:
        return jsonify({'error': 'Falta especificar la varianza o la desviación estándar'}), 400
    
    z_score = (x_bar - mu0) / (sigma / np.sqrt(n))
    tipo_de_cola = "de dos colas" if data.get('tipo', '=') == '=' else ("unilateral a la izquierda" if data['tipo'] == '<' else "unilateral a la derecha")
    
    if data.get('tipo', '=') == '=':
        p_value = 2 * (1 - norm.cdf(abs(z_score)))
        critical_value = critical_value_func(1 - alpha/2) if distribution_used == "Normal" else critical_value_func(1 - alpha/2, n-1)
        condition = f"se rechaza si |{z_score}| >= {critical_value}"
    else:
        if data['tipo'] == '<':
            p_value = norm.cdf(z_score)
            critical_value = critical_value_func(alpha) if distribution_used == "Normal" else critical_value_func(alpha, n-1)
            condition = f"se rechaza si {z_score} <= {critical_value}"
        else:
            p_value = 1 - norm.cdf(z_score)
            critical_value = critical_value_func(1 - alpha) if distribution_used == "Normal" else critical_value_func(1 - alpha, n-1)
            condition = f"se rechaza si {z_score} >= {critical_value}"
    
    decision = 'Rechazar H0' if p_value < alpha else 'Aceptar H0'
    
    # Generate the plot for the hypothesis test
    x = np.linspace(-3, 3, 1000)
    y = np.exp(-0.5 * x**2) / np.sqrt(2 * np.pi)
    
    plt.figure(figsize=(10, 6))
    plt.plot(x, y, label='Distribución', color='green')
    
    if tipo_de_cola == "de dos colas":
        plt.fill_between(x, y, where=(x <= -critical_value) | (x >= critical_value), color='red', alpha=0.3, label='Zonas Críticas')
        plt.axvline(-critical_value, color='red', linestyle='--', label='Valor Crítico (-)')
        plt.axvline(critical_value, color='red', linestyle='--', label='Valor Crítico (+)')
    elif tipo_de_cola == "unilateral a la izquierda":
        plt.fill_between(x, y, where=(x <= critical_value), color='red', alpha=0.3, label='Zona Crítica')
        plt.axvline(critical_value, color='red', linestyle='--', label='Valor Crítico')
    else:
        plt.fill_between(x, y, where=(x >= critical_value), color='red', alpha=0.3, label='Zona Crítica')
        plt.axvline(critical_value, color='red', linestyle='--', label='Valor Crítico')
    
    plt.axvline(z_score, color='blue', linestyle='--', label='Estadístico de prueba')
    plt.title('Prueba de Hipótesis')
    plt.xlabel('Z')
    plt.ylabel('Densidad')
    plt.legend()
    plt.grid(True)
    
    # Save the plot as an image
    image_filename = 'hypothesis_test_plot.png'
    image_path = os.path.join(IMAGE_DIR, image_filename)
    plt.savefig(image_path)
    plt.close()

    response = {
        "data": {
            "1": f"Variable de interés: media de la muestra = {x_bar}",
            "2": f"Hipótesis nula H0: μ = {mu0}",
            "3": f"Hipótesis alternativa H1: μ {data['tipo']} {mu0}",
            "4": f"Significancia: {alpha}",
            "5": f"Estadístico de prueba Z_0: {z_score}",
            "6": condition,
            "7": f"Decisión: {decision}",
            "8": f"Distribución usada: {distribution_used}"
        },
        "extras": {
           "p_value": f"{p_value}",
           "valor_critico": f"{critical_value}",
           "Estadístico_de_prueba_Z_0": f"{z_score}",
           "tipo_de_cola": tipo_de_cola
        },
        "image_path": f"/images/{image_filename}"
    }
    
    return jsonify(response)

@app.route('/images/<filename>', methods=['GET'])
def get_image(filename):
    return send_from_directory(IMAGE_DIR, filename)

@app.route('/mmc', methods=['POST'])
def minimos_cuadrados():
    data = request.get_json()
    x = np.array(data['x'])
    y = np.array(data['y'])
    
    if len(x) != len(y):
        return jsonify({'error': 'Los arrays x e y deben tener la misma longitud'}), 400
    
    n = len(x)
    xy = x * y
    x2 = x**2
    sum_x = np.sum(x)
    sum_y = np.sum(y)
    sum_xy = np.sum(xy)
    sum_x2 = np.sum(x2)
    
    b = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x**2)
    a = (sum_y - b * sum_x) / n
    
    r, _ = pearsonr(x, y)
    
    if abs(r) >= 0.9:
        fuerza_correlacion = "Muy fuerte"
    elif abs(r) >= 0.7:
        fuerza_correlacion = "Fuerte"
    elif abs(r) >= 0.5:
        fuerza_correlacion = "Moderada"
    elif abs(r) >= 0.3:
        fuerza_correlacion = "Débil"
    else:
        fuerza_correlacion = "Muy débil o ninguna"
    
    factor_crecimiento = (y[-1] / y[0]) ** (1 / (n-1)) - 1
    
    intervalo = data.get('intervalo', 'meses')
    periodos = data.get('periodos', 24)
    
    incremento_tiempo = 1 if intervalo == 'meses' else 12
    
    predicciones = []
    x_actual = x[-1]
    for i in range(periodos):
        x_actual = x_actual * (1 + factor_crecimiento)
        y_pred = a + b * x_actual
        predicciones.append({
            "periodo": i + 1,
            "unidades": x_actual,
            "ganancias": y_pred,
            "intervalo": intervalo
        })
    
    response = {
        "x": x.tolist(),
        "y": y.tolist(),
        "xy": xy.tolist(),
        "x2": x2.tolist(),
        "b": b,
        "a": a,
        "coeficiente_correlacion": r,
        "fuerza_correlacion": fuerza_correlacion,
        "factor_crecimiento": factor_crecimiento,
        "predicciones": predicciones
    }
    
    return jsonify(response)

uri = "mongodb://localhost:27017"
mongo_manager = MongoDBManager(uri)

@app.route('/insertar_venta', methods=['POST'])
def insertar_venta():
    data = request.get_json()
    ano = data['anioVenta']
    mes = data['mes']
    unidadesVendidas = data['unidadesVendidas']
    ganancias = data['ganancias']

    mongo_manager.insertar_venta(ano, mes, unidadesVendidas, ganancias)

    return jsonify({"message": f"Documento insertado o actualizado para el mes {mes} del año {ano}."}), 200

@app.route('/recuperar_ventas_globales', methods=['GET'])
def recuperar_ventas_globales():
    documentos = mongo_manager.recuperar_ventas_globales()
    return jsonify({"documentos": documentos})

def run_flask():
    app.run(debug=True, use_reloader=False)

if __name__ == '__main__':
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()
