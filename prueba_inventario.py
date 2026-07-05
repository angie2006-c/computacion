from datetime import date

import pandas as pd
import streamlit as st

from inventario import (
    buscar_movimientos_por_fecha,
    calcular_stock_actual,
    listar_movimientos,
    obtener_stock_general,
    registrar_entrada,
    registrar_salida,
)


st.set_page_config(
    page_title="Prueba de Inventario",
    page_icon=":package:",
    layout="wide",
)


def mostrar_mensaje(mensaje):
    texto = str(mensaje)

    if texto.lower().startswith("exito"):
        st.success(texto)
    elif texto.lower().startswith("error"):
        st.error(texto)
    else:
        st.info(texto)


def codigo_vacio(codigo_producto):
    return not str(codigo_producto).strip()


def descripcion_vacia(descripcion):
    return not str(descripcion).strip()


def cantidad_invalida(cantidad):
    return cantidad is None or cantidad <= 0


def mostrar_dataframe(df, mensaje_vacio):
    if isinstance(df, pd.DataFrame) and not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.info(mensaje_vacio)


st.title("Prueba del modulo de inventario")
st.caption("Interfaz temporal para probar entradas, salidas, stock y movimientos.")

tab_entrada, tab_salida, tab_stock, tab_general, tab_historial, tab_fechas = st.tabs(
    [
        "Entrada",
        "Salida",
        "Stock actual",
        "Stock general",
        "Historial",
        "Por fechas",
    ]
)


with tab_entrada:
    st.subheader("Registrar entrada de mercaderia")

    with st.form("form_registrar_entrada"):
        codigo_producto = st.text_input("Codigo del producto", key="entrada_codigo")
        cantidad = st.number_input(
            "Cantidad",
            min_value=0.0,
            step=1.0,
            key="entrada_cantidad",
        )
        descripcion = st.text_area("Descripcion", key="entrada_descripcion")
        enviar = st.form_submit_button("Registrar entrada")

    if enviar:
        if codigo_vacio(codigo_producto):
            st.error("Error: Debe ingresar el codigo del producto.")
        elif cantidad_invalida(cantidad):
            st.error("Error: La cantidad debe ser mayor a cero.")
        elif descripcion_vacia(descripcion):
            st.error("Error: Debe ingresar una descripcion.")
        else:
            mensaje = registrar_entrada(codigo_producto, cantidad, descripcion)
            mostrar_mensaje(mensaje)


with tab_salida:
    st.subheader("Registrar salida de producto")

    with st.form("form_registrar_salida"):
        codigo_producto = st.text_input("Codigo del producto", key="salida_codigo")
        cantidad = st.number_input(
            "Cantidad",
            min_value=0.0,
            step=1.0,
            key="salida_cantidad",
        )
        descripcion = st.text_area("Descripcion", key="salida_descripcion")
        enviar = st.form_submit_button("Registrar salida")

    if enviar:
        if codigo_vacio(codigo_producto):
            st.error("Error: Debe ingresar el codigo del producto.")
        elif cantidad_invalida(cantidad):
            st.error("Error: La cantidad debe ser mayor a cero.")
        elif descripcion_vacia(descripcion):
            st.error("Error: Debe ingresar una descripcion.")
        else:
            mensaje = registrar_salida(codigo_producto, cantidad, descripcion)
            mostrar_mensaje(mensaje)


with tab_stock:
    st.subheader("Ver stock actual de un producto")

    with st.form("form_stock_actual"):
        codigo_producto = st.text_input("Codigo del producto", key="stock_codigo")
        consultar = st.form_submit_button("Consultar stock")

    if consultar:
        if codigo_vacio(codigo_producto):
            st.error("Error: Debe ingresar el codigo del producto.")
        else:
            stock_actual = calcular_stock_actual(codigo_producto)
            df_stock = pd.DataFrame(
                [
                    {
                        "codigo_producto": str(codigo_producto).strip(),
                        "stock_actual": stock_actual,
                    }
                ]
            )
            st.dataframe(df_stock, use_container_width=True)


with tab_general:
    st.subheader("Ver stock general")

    if st.button("Actualizar stock general"):
        df_stock_general = obtener_stock_general()
        mostrar_dataframe(df_stock_general, "No hay productos para mostrar.")
    else:
        st.info("Presione el boton para consultar el stock general.")


with tab_historial:
    st.subheader("Ver historial de movimientos")

    if st.button("Actualizar historial"):
        df_movimientos = listar_movimientos()
        mostrar_dataframe(df_movimientos, "No hay movimientos registrados.")
    else:
        st.info("Presione el boton para consultar el historial de movimientos.")


with tab_fechas:
    st.subheader("Buscar movimientos por fecha")

    with st.form("form_buscar_fechas"):
        col_inicio, col_fin = st.columns(2)

        with col_inicio:
            fecha_inicio = st.date_input(
                "Fecha de inicio",
                value=date.today(),
                key="fecha_inicio",
            )

        with col_fin:
            fecha_fin = st.date_input(
                "Fecha final",
                value=date.today(),
                key="fecha_fin",
            )

        buscar = st.form_submit_button("Buscar movimientos")

    if buscar:
        if fecha_inicio is None or fecha_fin is None:
            st.error("Error: Debe seleccionar fecha de inicio y fecha final.")
        elif fecha_inicio > fecha_fin:
            st.error("Error: La fecha de inicio no puede ser mayor que la fecha final.")
        else:
            df_movimientos_fecha = buscar_movimientos_por_fecha(fecha_inicio, fecha_fin)
            mostrar_dataframe(
                df_movimientos_fecha,
                "No hay movimientos registrados en el rango seleccionado.",
            )
