from datetime import date, datetime

try:
    import pandas as pd
except ImportError as error:
    raise ImportError("No se pudo importar pandas. Instala pandas para usar este modulo.") from error

try:
    from database import conectar_db
except ImportError as error:
    raise ImportError(
        "No se pudo importar conectar_db desde database.py. "
        "Verifica que inventario.py este en la misma carpeta del proyecto."
    ) from error


FORMATO_FECHA = "%Y-%m-%d %H:%M:%S"
TIPO_ENTRADA = "entrada"
TIPO_SALIDA = "salida"

COLUMNAS_MOVIMIENTOS = [
    "id_movimiento",
    "codigo_producto",
    "nombre",
    "tipo_movimiento",
    "cantidad",
    "fecha",
    "descripcion",
]

COLUMNAS_STOCK_GENERAL = [
    "codigo",
    "nombre",
    "categoria",
    "entradas",
    "salidas",
    "stock_actual",
    "stock_minimo",
    "estado_stock",
]


def _fecha_actual():
    return datetime.now().strftime(FORMATO_FECHA)


def _normalizar_codigo(codigo_producto):
    if codigo_producto is None:
        return ""
    return str(codigo_producto).strip()


def _validar_cantidad(cantidad):
    try:
        if isinstance(cantidad, bool):
            return False, None, "Error: La cantidad debe ser un numero mayor a cero."

        cantidad_validada = float(cantidad)

        if cantidad_validada <= 0:
            return False, None, "Error: La cantidad debe ser mayor a cero."

        if cantidad_validada.is_integer():
            cantidad_validada = int(cantidad_validada)

        return True, cantidad_validada, ""
    except (TypeError, ValueError):
        return False, None, "Error: La cantidad debe ser un numero valido."


def _formatear_cantidad(cantidad):
    if isinstance(cantidad, float) and cantidad.is_integer():
        return str(int(cantidad))
    return str(cantidad)


def _preparar_descripcion(descripcion):
    if descripcion is None:
        return ""
    return str(descripcion).strip()


def _producto_existe_conexion(conexion, codigo_producto):
    codigo_producto = _normalizar_codigo(codigo_producto)
    if not codigo_producto:
        return False

    cursor = conexion.cursor()
    cursor.execute(
        "SELECT 1 FROM productos WHERE codigo = ? LIMIT 1",
        (codigo_producto,),
    )
    return cursor.fetchone() is not None


def _calcular_stock_conexion(conexion, codigo_producto):
    cursor = conexion.cursor()
    cursor.execute(
        """
        SELECT
            COALESCE(SUM(CASE WHEN LOWER(tipo_movimiento) = ? THEN cantidad ELSE 0 END), 0) AS entradas,
            COALESCE(SUM(CASE WHEN LOWER(tipo_movimiento) = ? THEN cantidad ELSE 0 END), 0) AS salidas
        FROM movimientos
        WHERE codigo_producto = ?
        """,
        (TIPO_ENTRADA, TIPO_SALIDA, codigo_producto),
    )
    entradas, salidas = cursor.fetchone()
    return entradas - salidas


def _normalizar_fecha_rango(valor_fecha, es_inicio=True):
    if isinstance(valor_fecha, datetime):
        return valor_fecha.strftime(FORMATO_FECHA)

    if isinstance(valor_fecha, date):
        hora = "00:00:00" if es_inicio else "23:59:59"
        return f"{valor_fecha.strftime('%Y-%m-%d')} {hora}"

    if valor_fecha is None:
        raise ValueError("Debe ingresar una fecha valida.")

    texto_fecha = str(valor_fecha).strip()

    if len(texto_fecha) == 10:
        datetime.strptime(texto_fecha, "%Y-%m-%d")
        hora = "00:00:00" if es_inicio else "23:59:59"
        return f"{texto_fecha} {hora}"

    datetime.strptime(texto_fecha, FORMATO_FECHA)
    return texto_fecha


def verificar_producto_existe(codigo_producto):
    conexion = None

    try:
        codigo_producto = _normalizar_codigo(codigo_producto)

        if not codigo_producto:
            print("Error: Debe ingresar el codigo del producto.")
            return False

        conexion = conectar_db()
        return _producto_existe_conexion(conexion, codigo_producto)
    except Exception as error:
        print(f"Error inesperado al verificar el producto: {error}")
        return False
    finally:
        if conexion:
            conexion.close()


def registrar_entrada(codigo_producto, cantidad, descripcion):
    conexion = None

    try:
        codigo_producto = _normalizar_codigo(codigo_producto)
        descripcion = _preparar_descripcion(descripcion)
        cantidad_es_valida, cantidad_validada, mensaje = _validar_cantidad(cantidad)

        if not codigo_producto:
            return "Error: Debe ingresar el codigo del producto."

        if not cantidad_es_valida:
            return mensaje

        conexion = conectar_db()

        if not _producto_existe_conexion(conexion, codigo_producto):
            return f"Error: El producto con codigo {codigo_producto} no existe."

        cursor = conexion.cursor()
        cursor.execute(
            """
            INSERT INTO movimientos (codigo_producto, tipo_movimiento, cantidad, fecha, descripcion)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                codigo_producto,
                TIPO_ENTRADA,
                cantidad_validada,
                _fecha_actual(),
                descripcion,
            ),
        )
        conexion.commit()

        return (
            f"Exito: Entrada registrada para el producto {codigo_producto}. "
            f"Cantidad: {_formatear_cantidad(cantidad_validada)}."
        )
    except Exception as error:
        if conexion:
            conexion.rollback()
        return f"Error inesperado al registrar entrada: {error}"
    finally:
        if conexion:
            conexion.close()


def registrar_salida(codigo_producto, cantidad, descripcion):
    conexion = None

    try:
        codigo_producto = _normalizar_codigo(codigo_producto)
        descripcion = _preparar_descripcion(descripcion)
        cantidad_es_valida, cantidad_validada, mensaje = _validar_cantidad(cantidad)

        if not codigo_producto:
            return "Error: Debe ingresar el codigo del producto."

        if not cantidad_es_valida:
            return mensaje

        conexion = conectar_db()

        if not _producto_existe_conexion(conexion, codigo_producto):
            return f"Error: El producto con codigo {codigo_producto} no existe."

        stock_actual = _calcular_stock_conexion(conexion, codigo_producto)

        if stock_actual < cantidad_validada:
            return (
                "Error: Stock insuficiente. "
                f"Stock disponible: {_formatear_cantidad(stock_actual)}. "
                f"Cantidad solicitada: {_formatear_cantidad(cantidad_validada)}."
            )

        cursor = conexion.cursor()
        cursor.execute(
            """
            INSERT INTO movimientos (codigo_producto, tipo_movimiento, cantidad, fecha, descripcion)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                codigo_producto,
                TIPO_SALIDA,
                cantidad_validada,
                _fecha_actual(),
                descripcion,
            ),
        )
        conexion.commit()

        return (
            f"Exito: Salida registrada para el producto {codigo_producto}. "
            f"Cantidad: {_formatear_cantidad(cantidad_validada)}."
        )
    except Exception as error:
        if conexion:
            conexion.rollback()
        return f"Error inesperado al registrar salida: {error}"
    finally:
        if conexion:
            conexion.close()


def calcular_stock_actual(codigo_producto):
    conexion = None

    try:
        codigo_producto = _normalizar_codigo(codigo_producto)

        if not codigo_producto:
            print("Error: Debe ingresar el codigo del producto.")
            return 0

        conexion = conectar_db()

        if not _producto_existe_conexion(conexion, codigo_producto):
            print(f"Error: El producto con codigo {codigo_producto} no existe.")
            return 0

        return _calcular_stock_conexion(conexion, codigo_producto)
    except Exception as error:
        print(f"Error inesperado al calcular stock actual: {error}")
        return 0
    finally:
        if conexion:
            conexion.close()


def validar_stock_disponible(codigo_producto, cantidad):
    conexion = None

    try:
        codigo_producto = _normalizar_codigo(codigo_producto)
        cantidad_es_valida, cantidad_validada, mensaje = _validar_cantidad(cantidad)

        if not codigo_producto:
            print("Error: Debe ingresar el codigo del producto.")
            return False

        if not cantidad_es_valida:
            print(mensaje)
            return False

        conexion = conectar_db()

        if not _producto_existe_conexion(conexion, codigo_producto):
            print(f"Error: El producto con codigo {codigo_producto} no existe.")
            return False

        stock_actual = _calcular_stock_conexion(conexion, codigo_producto)

        if stock_actual < cantidad_validada:
            print(
                "Error: Stock insuficiente. "
                f"Stock disponible: {_formatear_cantidad(stock_actual)}. "
                f"Cantidad solicitada: {_formatear_cantidad(cantidad_validada)}."
            )
            return False

        return True
    except Exception as error:
        print(f"Error inesperado al validar stock disponible: {error}")
        return False
    finally:
        if conexion:
            conexion.close()


def listar_movimientos():
    conexion = None

    try:
        conexion = conectar_db()
        consulta = """
        SELECT
            m.id_movimiento,
            m.codigo_producto,
            p.nombre,
            m.tipo_movimiento,
            m.cantidad,
            m.fecha,
            m.descripcion
        FROM movimientos m
        LEFT JOIN productos p ON p.codigo = m.codigo_producto
        ORDER BY m.fecha DESC, m.id_movimiento DESC
        """
        return pd.read_sql_query(consulta, conexion)
    except Exception as error:
        print(f"Error inesperado al listar movimientos: {error}")
        return pd.DataFrame(columns=COLUMNAS_MOVIMIENTOS)
    finally:
        if conexion:
            conexion.close()


def buscar_movimientos_por_fecha(fecha_inicio, fecha_fin):
    conexion = None

    try:
        fecha_inicio = _normalizar_fecha_rango(fecha_inicio, es_inicio=True)
        fecha_fin = _normalizar_fecha_rango(fecha_fin, es_inicio=False)

        if fecha_inicio > fecha_fin:
            print("Error: La fecha de inicio no puede ser mayor que la fecha final.")
            return pd.DataFrame(columns=COLUMNAS_MOVIMIENTOS)

        conexion = conectar_db()
        consulta = """
        SELECT
            m.id_movimiento,
            m.codigo_producto,
            p.nombre,
            m.tipo_movimiento,
            m.cantidad,
            m.fecha,
            m.descripcion
        FROM movimientos m
        LEFT JOIN productos p ON p.codigo = m.codigo_producto
        WHERE m.fecha BETWEEN ? AND ?
        ORDER BY m.fecha DESC, m.id_movimiento DESC
        """
        return pd.read_sql_query(consulta, conexion, params=(fecha_inicio, fecha_fin))
    except ValueError as error:
        print(f"Error: Fecha invalida. {error}")
        return pd.DataFrame(columns=COLUMNAS_MOVIMIENTOS)
    except Exception as error:
        print(f"Error inesperado al buscar movimientos por fecha: {error}")
        return pd.DataFrame(columns=COLUMNAS_MOVIMIENTOS)
    finally:
        if conexion:
            conexion.close()


def obtener_stock_general():
    conexion = None

    try:
        conexion = conectar_db()
        consulta = """
        WITH resumen AS (
            SELECT
                codigo_producto,
                COALESCE(SUM(CASE WHEN LOWER(tipo_movimiento) = 'entrada' THEN cantidad ELSE 0 END), 0) AS entradas,
                COALESCE(SUM(CASE WHEN LOWER(tipo_movimiento) = 'salida' THEN cantidad ELSE 0 END), 0) AS salidas
            FROM movimientos
            GROUP BY codigo_producto
        ),
        stock AS (
            SELECT
                p.codigo,
                p.nombre,
                p.categoria,
                COALESCE(r.entradas, 0) AS entradas,
                COALESCE(r.salidas, 0) AS salidas,
                COALESCE(r.entradas, 0) - COALESCE(r.salidas, 0) AS stock_actual,
                p.stock_minimo
            FROM productos p
            LEFT JOIN resumen r ON r.codigo_producto = p.codigo
        )
        SELECT
            codigo,
            nombre,
            categoria,
            entradas,
            salidas,
            stock_actual,
            stock_minimo,
            CASE
                WHEN stock_actual = 0 THEN 'Sin stock'
                WHEN stock_actual > 0 AND stock_actual <= COALESCE(stock_minimo, 0) THEN 'Bajo stock'
                WHEN stock_actual > COALESCE(stock_minimo, 0) THEN 'Normal'
                ELSE 'Sin stock'
            END AS estado_stock
        FROM stock
        ORDER BY nombre ASC, codigo ASC
        """
        return pd.read_sql_query(consulta, conexion)
    except Exception as error:
        print(f"Error inesperado al obtener stock general: {error}")
        return pd.DataFrame(columns=COLUMNAS_STOCK_GENERAL)
    finally:
        if conexion:
            conexion.close()


if __name__ == "__main__":
    codigo_prueba = "P001"

    print("=== Pruebas del modulo inventario ===")
    print("Use un codigo de producto existente en la tabla productos.")
    print()

    print("Verificar producto:")
    print(verificar_producto_existe(codigo_prueba))
    print()

    print("Registrar entrada:")
    print(registrar_entrada(codigo_prueba, 10, "Ingreso de prueba"))
    print()

    print("Stock actual:")
    print(calcular_stock_actual(codigo_prueba))
    print()

    print("Validar stock disponible:")
    print(validar_stock_disponible(codigo_prueba, 2))
    print()

    print("Registrar salida:")
    print(registrar_salida(codigo_prueba, 2, "Salida de prueba"))
    print()

    print("Historial de movimientos:")
    print(listar_movimientos())
    print()

    print("Movimientos por rango de fechas:")
    print(buscar_movimientos_por_fecha("2026-01-01", "2026-12-31"))
    print()

    print("Stock general:")
    print(obtener_stock_general())
