"""
Modulo de indicadores para el Dashboard de Smart Warehouse.

Este modulo obtiene metricas generales del inventario mediante consultas SQL
sobre la base de datos existente, sin modificar su estructura.
"""

import sqlite3

import pandas as pd

from database import obtener_conexion


COLUMNAS_STOCK_BAJO = [
    "id_producto",
    "codigo_barras",
    "nombre",
    "categoria",
    "stock_actual",
    "stock_minimo",
    "estado",
]

COLUMNAS_PRODUCTOS_CATEGORIA = ["categoria", "total_productos"]


def _obtener_valor_escalar(consulta, parametros=None, valor_defecto=0):
    conexion = None

    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        cursor.execute(consulta, parametros or ())
        resultado = cursor.fetchone()

        if not resultado or resultado[0] is None:
            return valor_defecto

        return resultado[0]
    except sqlite3.Error as error:
        print(f"Error al obtener indicador: {error}")
        return valor_defecto
    finally:
        if conexion:
            conexion.close()


def _obtener_fila_diccionario(consulta, parametros=None):
    conexion = None

    try:
        conexion = obtener_conexion()
        conexion.row_factory = sqlite3.Row
        cursor = conexion.cursor()
        cursor.execute(consulta, parametros or ())
        fila = cursor.fetchone()

        return dict(fila) if fila else None
    except sqlite3.Error as error:
        print(f"Error al obtener indicador: {error}")
        return None
    finally:
        if conexion:
            conexion.close()


def obtener_total_productos():
    """
    Devuelve la cantidad total de productos registrados.
    """
    consulta = "SELECT COUNT(*) FROM productos;"
    return _obtener_valor_escalar(consulta)


def obtener_total_productos_activos():
    """
    Devuelve la cantidad de productos con estado activo.
    """
    consulta = """
        SELECT COUNT(*)
        FROM productos
        WHERE LOWER(estado) = 'activo';
    """
    return _obtener_valor_escalar(consulta)


def obtener_stock_total():
    """
    Devuelve la suma del stock actual de todos los productos.
    """
    consulta = "SELECT COALESCE(SUM(stock_actual), 0) FROM productos;"
    return _obtener_valor_escalar(consulta)


def obtener_productos_stock_bajo():
    """
    Devuelve los productos cuyo stock actual es menor o igual al stock minimo.
    """
    conexion = None

    try:
        conexion = obtener_conexion()
        consulta = """
            SELECT
                id_producto,
                codigo_barras,
                nombre,
                categoria,
                stock_actual,
                stock_minimo,
                estado
            FROM productos
            WHERE COALESCE(stock_actual, 0) <= COALESCE(stock_minimo, 0)
            ORDER BY stock_actual ASC, nombre ASC;
        """
        return pd.read_sql_query(consulta, conexion)
    except sqlite3.Error as error:
        print(f"Error al obtener productos con stock bajo: {error}")
        return pd.DataFrame(columns=COLUMNAS_STOCK_BAJO)
    finally:
        if conexion:
            conexion.close()


def obtener_cantidad_productos_stock_bajo():
    """
    Devuelve la cantidad de productos con stock bajo o sin stock.
    """
    consulta = """
        SELECT COUNT(*)
        FROM productos
        WHERE COALESCE(stock_actual, 0) <= COALESCE(stock_minimo, 0);
    """
    return _obtener_valor_escalar(consulta)


def obtener_valor_total_inventario():
    """
    Devuelve el valor total del inventario usando el precio de compra.
    """
    consulta = """
        SELECT COALESCE(SUM(stock_actual * precio_compra), 0)
        FROM productos;
    """
    return _obtener_valor_escalar(consulta, valor_defecto=0.0)


def obtener_valor_total_venta_estimado():
    """
    Devuelve el valor total estimado usando el precio de venta.
    """
    consulta = """
        SELECT COALESCE(SUM(stock_actual * precio_venta), 0)
        FROM productos;
    """
    return _obtener_valor_escalar(consulta, valor_defecto=0.0)


def obtener_productos_por_categoria():
    """
    Devuelve la cantidad de productos agrupados por categoria.
    """
    conexion = None

    try:
        conexion = obtener_conexion()
        consulta = """
            SELECT
                COALESCE(NULLIF(TRIM(categoria), ''), 'Sin categoria') AS categoria,
                COUNT(*) AS total_productos
            FROM productos
            GROUP BY COALESCE(NULLIF(TRIM(categoria), ''), 'Sin categoria')
            ORDER BY total_productos DESC, categoria ASC;
        """
        return pd.read_sql_query(consulta, conexion)
    except sqlite3.Error as error:
        print(f"Error al obtener productos por categoria: {error}")
        return pd.DataFrame(columns=COLUMNAS_PRODUCTOS_CATEGORIA)
    finally:
        if conexion:
            conexion.close()


def obtener_producto_mayor_stock():
    """
    Devuelve el producto con mayor stock actual.
    """
    consulta = """
        SELECT
            id_producto,
            codigo_barras,
            nombre,
            categoria,
            stock_actual,
            stock_minimo,
            estado
        FROM productos
        ORDER BY stock_actual DESC, nombre ASC
        LIMIT 1;
    """
    return _obtener_fila_diccionario(consulta)


def obtener_producto_menor_stock():
    """
    Devuelve el producto con menor stock actual.
    """
    consulta = """
        SELECT
            id_producto,
            codigo_barras,
            nombre,
            categoria,
            stock_actual,
            stock_minimo,
            estado
        FROM productos
        ORDER BY stock_actual ASC, nombre ASC
        LIMIT 1;
    """
    return _obtener_fila_diccionario(consulta)


def obtener_total_entradas():
    """
    Devuelve la cantidad total de unidades registradas como entradas.
    """
    consulta = """
        SELECT COALESCE(SUM(cantidad), 0)
        FROM movimientos
        WHERE LOWER(tipo_movimiento) = 'entrada';
    """
    return _obtener_valor_escalar(consulta)


def obtener_total_salidas():
    """
    Devuelve la cantidad total de unidades registradas como salidas.
    """
    consulta = """
        SELECT COALESCE(SUM(cantidad), 0)
        FROM movimientos
        WHERE LOWER(tipo_movimiento) = 'salida';
    """
    return _obtener_valor_escalar(consulta)


def obtener_resumen_indicadores():
    """
    Devuelve un diccionario con los principales indicadores del inventario.
    """
    return {
        "total_productos": obtener_total_productos(),
        "total_productos_activos": obtener_total_productos_activos(),
        "stock_total": obtener_stock_total(),
        "productos_stock_bajo": obtener_cantidad_productos_stock_bajo(),
        "valor_total_inventario": obtener_valor_total_inventario(),
        "valor_total_venta_estimado": obtener_valor_total_venta_estimado(),
        "total_entradas": obtener_total_entradas(),
        "total_salidas": obtener_total_salidas(),
    }


if __name__ == "__main__":
    print("Modulo de indicadores listo para integrarse con el Dashboard.")
