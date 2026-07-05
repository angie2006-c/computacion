"""
Modulo central del Dashboard de Smart Warehouse.

Este archivo organiza los indicadores, la clasificacion ABC y el acceso a los
graficos del Dashboard sin repetir consultas ni logica de negocio.
"""

from indicadores import (
    obtener_productos_stock_bajo,
    obtener_resumen_indicadores,
    obtener_valor_total_inventario,
)
from graficos import (
    generar_grafico_clasificacion_abc,
    generar_grafico_productos_mas_utilizados,
    generar_grafico_productos_stock_bajo,
    generar_grafico_rotacion_inventario,
    obtener_clasificacion_abc,
)


TITULO_DASHBOARD = "Dashboard Smart Warehouse"


OPCIONES_GRAFICOS = {
    "productos_mas_utilizados": generar_grafico_productos_mas_utilizados,
    "clasificacion_abc": generar_grafico_clasificacion_abc,
    "productos_stock_bajo": generar_grafico_productos_stock_bajo,
    "rotacion_inventario": generar_grafico_rotacion_inventario,
}


def obtener_datos_dashboard():
    """
    Devuelve los datos principales que necesita el Dashboard.
    """
    resumen = obtener_resumen_indicadores()

    return {
        "total_productos": resumen.get("total_productos", 0),
        "stock_total": resumen.get("stock_total", 0),
        "valor_inventario": obtener_valor_total_inventario(),
        "productos_stock_bajo": obtener_productos_stock_bajo(),
        "clasificacion_abc": obtener_clasificacion_abc(),
    }


def obtener_grafico(nombre_grafico, **kwargs):
    """
    Devuelve un grafico especifico del Dashboard.
    """
    funcion_grafico = OPCIONES_GRAFICOS.get(nombre_grafico)

    if not funcion_grafico:
        print("Error: Grafico no disponible.")
        return None

    return funcion_grafico(**kwargs)


def obtener_graficos_dashboard():
    """
    Devuelve todos los graficos disponibles del Dashboard.
    """
    return {
        nombre: funcion()
        for nombre, funcion in OPCIONES_GRAFICOS.items()
    }


def mostrar_resumen_dashboard():
    """
    Muestra en consola un resumen organizado del Dashboard.
    """
    datos = obtener_datos_dashboard()
    productos_stock_bajo = datos["productos_stock_bajo"]
    clasificacion_abc = datos["clasificacion_abc"]

    print(f"\n=== {TITULO_DASHBOARD} ===")
    print(f"Total de productos: {datos['total_productos']}")
    print(f"Stock total: {datos['stock_total']}")
    print(f"Valor del inventario: {datos['valor_inventario']:.2f}")

    print("\n--- Productos con stock bajo ---")
    if productos_stock_bajo.empty:
        print("No hay productos con stock bajo.")
    else:
        print(productos_stock_bajo.to_string(index=False))

    print("\n--- Clasificacion ABC ---")
    if clasificacion_abc.empty:
        print("No hay datos suficientes para clasificar productos.")
    else:
        print(clasificacion_abc.to_string(index=False))

    print("\n--- Graficos disponibles ---")
    for nombre_grafico in OPCIONES_GRAFICOS:
        print(f"- {nombre_grafico}")


def iniciar_dashboard():
    """
    Punto de entrada preparado para una futura interfaz con CustomTkinter.
    """
    print(
        "CustomTkinter aun no esta integrado en el proyecto. "
        "Se muestra el resumen del Dashboard por consola."
    )
    mostrar_resumen_dashboard()


if __name__ == "__main__":
    iniciar_dashboard()
