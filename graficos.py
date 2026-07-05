"""
Modulo de graficos para el Dashboard de Smart Warehouse.

Este modulo genera visualizaciones con Matplotlib reutilizando las funciones
publicas de los modulos de indicadores y clasificacion ABC.
"""

from importlib import util
from pathlib import Path

import matplotlib.pyplot as plt

from indicadores import obtener_productos_stock_bajo, obtener_resumen_indicadores


def _cargar_modulo_abc():
    ruta_modulo = Path(__file__).resolve().parent / "abc.py"
    especificacion = util.spec_from_file_location("dashboard_abc", ruta_modulo)
    modulo = util.module_from_spec(especificacion)
    especificacion.loader.exec_module(modulo)
    return modulo


_modulo_abc = _cargar_modulo_abc()
obtener_clasificacion_abc = _modulo_abc.obtener_clasificacion_abc
obtener_consumo_por_producto = _modulo_abc.obtener_consumo_por_producto
obtener_resumen_abc = _modulo_abc.obtener_resumen_abc


COLOR_PRINCIPAL = "#2E86AB"
COLOR_SECUNDARIO = "#F6C85F"
COLOR_ALERTA = "#C0392B"
COLOR_EXITO = "#27AE60"
COLOR_NEUTRO = "#95A5A6"
COLORES_ABC = ["#2E86AB", "#F6C85F", "#C0392B"]


def _configurar_grafico(titulo, etiqueta_x=None, etiqueta_y=None):
    plt.title(titulo)

    if etiqueta_x:
        plt.xlabel(etiqueta_x)

    if etiqueta_y:
        plt.ylabel(etiqueta_y)

    plt.tight_layout()


def _figura_sin_datos(titulo, mensaje="No hay datos disponibles."):
    figura, eje = plt.subplots(figsize=(8, 5))
    eje.text(
        0.5,
        0.5,
        mensaje,
        ha="center",
        va="center",
        fontsize=12,
    )
    eje.set_title(titulo)
    eje.axis("off")
    figura.tight_layout()
    return figura


def generar_grafico_productos_mas_utilizados(limite=10):
    """
    Genera un grafico de barras con los productos de mayor consumo.
    """
    dataframe = obtener_consumo_por_producto()

    if dataframe.empty:
        return _figura_sin_datos("Productos mas utilizados")

    dataframe = dataframe.head(limite)

    figura, eje = plt.subplots(figsize=(10, 6))
    eje.barh(dataframe["nombre"], dataframe["consumo_total"], color=COLOR_PRINCIPAL)
    eje.invert_yaxis()
    eje.set_title("Productos mas utilizados")
    eje.set_xlabel("Consumo total")
    eje.set_ylabel("Producto")

    for indice, valor in enumerate(dataframe["consumo_total"]):
        eje.text(valor, indice, f" {valor}", va="center")

    figura.tight_layout()
    return figura


def generar_grafico_clasificacion_abc():
    """
    Genera un grafico circular con la distribucion porcentual ABC.
    """
    resumen = obtener_resumen_abc()

    if resumen.empty:
        return _figura_sin_datos("Clasificacion ABC")

    figura, eje = plt.subplots(figsize=(7, 7))
    eje.pie(
        resumen["porcentaje_total"],
        labels=resumen["clasificacion"],
        autopct="%1.1f%%",
        startangle=90,
        colors=COLORES_ABC[: len(resumen)],
    )
    eje.set_title("Clasificacion ABC por consumo")
    eje.axis("equal")
    figura.tight_layout()
    return figura


def generar_grafico_productos_stock_bajo(limite=10):
    """
    Genera un grafico de barras con productos en stock bajo.
    """
    dataframe = obtener_productos_stock_bajo()

    if dataframe.empty:
        return _figura_sin_datos("Productos con stock bajo")

    dataframe = dataframe.sort_values(
        by=["stock_actual", "nombre"],
        ascending=[True, True],
    ).head(limite)

    figura, eje = plt.subplots(figsize=(10, 6))
    eje.barh(
        dataframe["nombre"],
        dataframe["stock_actual"],
        color=COLOR_ALERTA,
        label="Stock actual",
    )
    eje.scatter(
        dataframe["stock_minimo"],
        dataframe["nombre"],
        color=COLOR_SECUNDARIO,
        label="Stock minimo",
        zorder=3,
    )
    eje.invert_yaxis()
    eje.set_title("Productos con stock bajo")
    eje.set_xlabel("Unidades")
    eje.set_ylabel("Producto")
    eje.legend()
    figura.tight_layout()
    return figura


def generar_grafico_rotacion_inventario():
    """
    Genera un grafico de barras con la rotacion general del inventario.
    """
    indicadores = obtener_resumen_indicadores()
    stock_total = indicadores.get("stock_total", 0) or 0
    total_salidas = indicadores.get("total_salidas", 0) or 0

    if stock_total <= 0 and total_salidas <= 0:
        return _figura_sin_datos("Rotacion del inventario")

    rotacion = 0

    if stock_total > 0:
        rotacion = round(total_salidas / stock_total, 2)

    figura, eje = plt.subplots(figsize=(8, 5))
    etiquetas = ["Salidas", "Stock actual", "Rotacion"]
    valores = [total_salidas, stock_total, rotacion]
    colores = [COLOR_PRINCIPAL, COLOR_EXITO, COLOR_SECUNDARIO]

    eje.bar(etiquetas, valores, color=colores)
    eje.set_title("Rotacion del inventario")
    eje.set_ylabel("Valor")

    for indice, valor in enumerate(valores):
        eje.text(indice, valor, f"{valor}", ha="center", va="bottom")

    figura.tight_layout()
    return figura


def generar_grafico_rotacion_por_clase_abc():
    """
    Genera un grafico de barras con el consumo acumulado por clase ABC.
    """
    dataframe = obtener_clasificacion_abc()

    if dataframe.empty:
        return _figura_sin_datos("Rotacion por clase ABC")

    resumen = (
        dataframe.groupby("clasificacion", as_index=False)["consumo_total"]
        .sum()
        .sort_values("clasificacion")
    )

    figura, eje = plt.subplots(figsize=(8, 5))
    eje.bar(
        resumen["clasificacion"],
        resumen["consumo_total"],
        color=COLORES_ABC[: len(resumen)],
    )
    eje.set_title("Rotacion por clase ABC")
    eje.set_xlabel("Clasificacion")
    eje.set_ylabel("Consumo total")

    for indice, valor in enumerate(resumen["consumo_total"]):
        eje.text(indice, valor, f"{valor}", ha="center", va="bottom")

    figura.tight_layout()
    return figura


if __name__ == "__main__":
    print("Modulo de graficos listo para integrarse con el Dashboard.")
