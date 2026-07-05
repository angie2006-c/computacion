"""
Modulo de clasificacion ABC para el Dashboard de Smart Warehouse.

Este modulo calcula la clasificacion ABC utilizando unicamente los movimientos
reales de salida registrados en la base de datos.
"""

import sqlite3

import pandas as pd

from database import obtener_conexion


COLUMNAS_CLASIFICACION_ABC = [
    "id_producto",
    "codigo_barras",
    "nombre",
    "categoria",
    "consumo_total",
    "porcentaje",
    "porcentaje_acumulado",
    "clasificacion",
]

PORCENTAJE_CLASE_A = 80
PORCENTAJE_CLASE_B = 95


def _dataframe_vacio():
    return pd.DataFrame(columns=COLUMNAS_CLASIFICACION_ABC)


def _asignar_clasificacion(porcentaje_acumulado_anterior):
    if porcentaje_acumulado_anterior < PORCENTAJE_CLASE_A:
        return "A"

    if porcentaje_acumulado_anterior < PORCENTAJE_CLASE_B:
        return "B"

    return "C"


def obtener_movimientos_salida():
    """
    Devuelve los movimientos de salida registrados en la base de datos.
    """
    conexion = None

    try:
        conexion = obtener_conexion()
        consulta = """
            SELECT
                m.id_movimiento,
                m.id_producto,
                p.codigo_barras,
                p.nombre,
                p.categoria,
                m.cantidad,
                m.fecha_movimiento,
                m.motivo,
                m.observacion,
                m.id_usuario
            FROM movimientos m
            INNER JOIN productos p ON m.id_producto = p.id_producto
            WHERE LOWER(m.tipo_movimiento) = 'salida'
            ORDER BY m.fecha_movimiento DESC, m.id_movimiento DESC;
        """
        return pd.read_sql_query(consulta, conexion)
    except sqlite3.Error as error:
        print(f"Error al obtener movimientos de salida: {error}")
        return pd.DataFrame()
    finally:
        if conexion:
            conexion.close()


def obtener_consumo_por_producto():
    """
    Calcula el consumo total por producto usando movimientos de salida.
    """
    conexion = None

    try:
        conexion = obtener_conexion()
        consulta = """
            SELECT
                p.id_producto,
                p.codigo_barras,
                p.nombre,
                p.categoria,
                COALESCE(SUM(m.cantidad), 0) AS consumo_total
            FROM movimientos m
            INNER JOIN productos p ON m.id_producto = p.id_producto
            WHERE LOWER(m.tipo_movimiento) = 'salida'
            GROUP BY
                p.id_producto,
                p.codigo_barras,
                p.nombre,
                p.categoria
            ORDER BY consumo_total DESC, p.nombre ASC;
        """
        return pd.read_sql_query(consulta, conexion)
    except sqlite3.Error as error:
        print(f"Error al obtener consumo por producto: {error}")
        return pd.DataFrame(
            columns=[
                "id_producto",
                "codigo_barras",
                "nombre",
                "categoria",
                "consumo_total",
            ]
        )
    finally:
        if conexion:
            conexion.close()


def obtener_clasificacion_abc():
    """
    Calcula la clasificacion ABC de productos segun su consumo por salidas.
    """
    dataframe = obtener_consumo_por_producto()

    if dataframe.empty:
        return _dataframe_vacio()

    consumo_total_general = dataframe["consumo_total"].sum()

    if consumo_total_general <= 0:
        return _dataframe_vacio()

    dataframe = dataframe.sort_values(
        by=["consumo_total", "nombre"],
        ascending=[False, True],
    ).reset_index(drop=True)

    dataframe["porcentaje"] = (
        dataframe["consumo_total"] / consumo_total_general * 100
    ).round(2)
    dataframe["porcentaje_acumulado"] = dataframe["porcentaje"].cumsum().round(2)

    porcentaje_acumulado_anterior = 0
    clasificaciones = []

    for porcentaje in dataframe["porcentaje"]:
        clasificaciones.append(_asignar_clasificacion(porcentaje_acumulado_anterior))
        porcentaje_acumulado_anterior += porcentaje

    dataframe["clasificacion"] = clasificaciones

    return dataframe[COLUMNAS_CLASIFICACION_ABC]


def obtener_productos_clase(clasificacion):
    """
    Devuelve los productos de una clase ABC especifica.
    """
    clasificacion = str(clasificacion).strip().upper()

    if clasificacion not in ("A", "B", "C"):
        print("Error: La clasificacion debe ser A, B o C.")
        return _dataframe_vacio()

    dataframe = obtener_clasificacion_abc()

    if dataframe.empty:
        return dataframe

    return dataframe[dataframe["clasificacion"] == clasificacion].reset_index(drop=True)


def obtener_resumen_abc():
    """
    Devuelve un resumen por clase ABC con productos, consumo y porcentaje.
    """
    dataframe = obtener_clasificacion_abc()

    if dataframe.empty:
        return pd.DataFrame(
            columns=[
                "clasificacion",
                "total_productos",
                "consumo_total",
                "porcentaje_total",
            ]
        )

    resumen = (
        dataframe.groupby("clasificacion", as_index=False)
        .agg(
            total_productos=("id_producto", "count"),
            consumo_total=("consumo_total", "sum"),
            porcentaje_total=("porcentaje", "sum"),
        )
        .sort_values("clasificacion")
        .reset_index(drop=True)
    )
    resumen["porcentaje_total"] = resumen["porcentaje_total"].round(2)

    return resumen


if __name__ == "__main__":
    print("Modulo de clasificacion ABC listo para integrarse con el Dashboard.")
