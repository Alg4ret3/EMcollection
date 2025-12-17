from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy import or_
from app.models.productos import Productos
from app.models.productos import Marcas
from app.models.productos import Categorias
from app.models.facturas import Facturas
from app.models.detalle_facturas import DetalleFacturas


def redondear_a_cientos(numero):
    """
    Redondea el número hacia el siguiente múltiplo de 100.
    Siempre redondea hacia arriba.
    """
    if numero is None:
        raise ValueError("El valor de 'numero' no puede ser None")
    if not isinstance(numero, (int, float)):
        raise TypeError("El valor debe ser un número entero o flotante")
    if numero % 100 == 0:
        return numero
    return ((numero // 100) + 1) * 100


def calcular_ganancia(precio_venta, precio_costo):
    return precio_venta - precio_costo


def calcular_precio(precio_costo, porcentaje):
    return redondear_a_cientos(precio_costo + (precio_costo * porcentaje))


def cambiar_estado(stock_actual):
    return stock_actual > 0


# Crear un producto
def crear_producto(
    db: Session,
    id_producto: int,
    nombre: str,
    precio_costo: float,
    stock_actual: int,
    stock_min: int,
    stock_max: int,
    precio_venta_normal: float,
    precio_venta_mayor: float,
    precio_venta_reventa: float = None,
    id_marca: int = None,
    id_categoria: int = None,
):
    estado = cambiar_estado(stock_actual)

    if not precio_venta_reventa:
        precio_venta_reventa = calcular_precio(precio_costo, 0.31)

    ganancia_producto_normal = calcular_ganancia(precio_venta_normal, precio_costo)
    ganancia_producto_mayor = calcular_ganancia(precio_venta_mayor, precio_costo)
    ganancia_producto_reventa = calcular_ganancia(precio_venta_reventa, precio_costo)

    nuevo_producto = Productos(
        ID_Producto=id_producto,
        Nombre=nombre,
        Precio_costo=precio_costo,
        Precio_venta_normal=precio_venta_normal,
        Precio_venta_mayor=precio_venta_mayor,
        Precio_venta_reventa=precio_venta_reventa,
        Ganancia_Producto_normal=ganancia_producto_normal,
        Ganancia_Producto_mayor=ganancia_producto_mayor,
        Ganancia_Producto_reventa=ganancia_producto_reventa,
        Stock_actual=stock_actual,
        Stock_min=stock_min,
        Stock_max=stock_max,
        ID_Marca=id_marca,
        ID_Categoria=id_categoria,
        Estado=estado,
    )
    db.add(nuevo_producto)
    db.commit()
    db.refresh(nuevo_producto)
    return nuevo_producto


def obtener_productos_mas_vendidos(db: Session, limite=20):
    resultados = (
        db.query(
            Productos.ID_Producto,
            Productos.Nombre,
            func.sum(DetalleFacturas.Cantidad).label("Total_Unidades_Vendidas"),
            func.sum(DetalleFacturas.Subtotal).label("Total_Ganado"),
        )
        .join(DetalleFacturas, Productos.ID_Producto == DetalleFacturas.ID_Producto)
        .group_by(Productos.ID_Producto, Productos.Nombre)
        .order_by(func.sum(DetalleFacturas.Cantidad).desc())
        .limit(limite)
        .all()
    )
    return resultados


def obtener_productos(db: Session):
    productos = (
        db.query(
            Productos.ID_Producto,
            Productos.Nombre,
            Productos.Precio_costo,
            Productos.Precio_venta_normal,
            Productos.Precio_venta_mayor,
            Productos.Precio_venta_reventa,
            Productos.Ganancia_Producto_normal,
            Productos.Ganancia_Producto_mayor,
            Productos.Ganancia_Producto_reventa,
            Productos.Stock_actual,
            Productos.Stock_min,
            Productos.Stock_max,
            Productos.Estado,
            Marcas.Nombre.label("marcas"),
            Categorias.Nombre.label("categorias"),
        )
        .join(Marcas, Productos.ID_Marca == Marcas.ID_Marca)
        .join(Categorias, Productos.ID_Categoria == Categorias.ID_Categoria)
        .all()
    )
    return productos


def obtener_producto_por_id(db: Session, id_producto: int):
    productos = (
        db.query(
            Productos.ID_Producto,
            Productos.Nombre,
            Productos.Precio_costo,
            Productos.Precio_venta_normal,
            Productos.Precio_venta_mayor,
            Productos.Precio_venta_reventa,
            Productos.Ganancia_Producto_normal,
            Productos.Ganancia_Producto_mayor,
            Productos.Ganancia_Producto_reventa,
            Productos.Stock_actual,
            Productos.Stock_min,
            Productos.Stock_max,
            Marcas.Nombre.label("marcas"),
            Categorias.Nombre.label("categorias"),
        )
        .join(Marcas, Productos.ID_Marca == Marcas.ID_Marca)
        .join(Categorias, Productos.ID_Categoria == Categorias.ID_Categoria)
        .filter(Productos.ID_Producto == id_producto)
        .all()
    )
    return productos


def buscar_productos(db: Session, busqueda: str):
    if not busqueda:
        return None

    productos = (
        db.query(
            Productos.ID_Producto,
            Productos.Nombre,
            Productos.Precio_costo,
            Productos.Precio_venta_normal,
            Productos.Precio_venta_mayor,
            Productos.Precio_venta_reventa,
            Productos.Ganancia_Producto_normal,
            Productos.Ganancia_Producto_mayor,
            Productos.Ganancia_Producto_reventa,
            Productos.Stock_actual,
            Productos.Stock_min,
            Productos.Stock_max,
            Productos.Estado,
            Marcas.Nombre.label("marcas"),
            Categorias.Nombre.label("categorias"),
        )
        .join(Marcas, Productos.ID_Marca == Marcas.ID_Marca)
        .join(Categorias, Productos.ID_Categoria == Categorias.ID_Categoria)
        .filter(
            or_(
                Productos.Nombre.like(f"%{busqueda}%"),
                Productos.ID_Producto.like(f"%{busqueda}%"),
                Marcas.Nombre.like(f"%{busqueda}%"),
                Categorias.Nombre.like(f"%{busqueda}%"),
            )
        )
        .all()
    )
    return productos


def actualizar_producto(
    db: Session,
    id_producto: int,
    nombre: str = None,
    precio_costo: float = None,
    precio_venta_normal: float = None,
    precio_venta_mayor: float = None,
    precio_venta_reventa: float = None,
    stock_actual: int = None,
    stock_min: int = None,
    stock_max: int = None,
    id_marca: int = None,
    id_categoria: int = None,
):
    producto_existente = (
        db.query(Productos).filter(Productos.ID_Producto == id_producto).first()
    )
    if not producto_existente:
        return None

    if nombre:
        producto_existente.Nombre = nombre
    if precio_costo:
        producto_existente.Precio_costo = precio_costo

    if precio_costo and not precio_venta_normal:
        producto_existente.Precio_venta_normal = calcular_precio(precio_costo, 0.5)
    if precio_costo and not precio_venta_mayor:
        producto_existente.Precio_venta_mayor = calcular_precio(precio_costo, 0.35)
    if precio_costo and not precio_venta_reventa:
        producto_existente.Precio_venta_reventa = calcular_precio(precio_costo, 0.31)

    if precio_venta_normal:
        producto_existente.Precio_venta_normal = precio_venta_normal
    if precio_venta_mayor:
        producto_existente.Precio_venta_mayor = precio_venta_mayor
    if precio_venta_reventa:
        producto_existente.Precio_venta_reventa = precio_venta_reventa

    # Recalcular ganancias
    if precio_costo or precio_venta_normal:
        producto_existente.Ganancia_Producto_normal = calcular_ganancia(
            producto_existente.Precio_venta_normal, producto_existente.Precio_costo
        )
    if precio_costo or precio_venta_mayor:
        producto_existente.Ganancia_Producto_mayor = calcular_ganancia(
            producto_existente.Precio_venta_mayor, producto_existente.Precio_costo
        )
    if precio_costo or precio_venta_reventa:
        producto_existente.Ganancia_Producto_reventa = calcular_ganancia(
            producto_existente.Precio_venta_reventa, producto_existente.Precio_costo
        )

    if stock_actual is not None:
        producto_existente.Stock_actual = stock_actual
        producto_existente.Estado = cambiar_estado(stock_actual)
    if stock_min is not None:
        producto_existente.Stock_min = stock_min
    if stock_max is not None:
        producto_existente.Stock_max = stock_max

    if id_marca:
        producto_existente.ID_Marca = id_marca
    if id_categoria:
        producto_existente.ID_Categoria = id_categoria

    db.commit()
    db.refresh(producto_existente)
    return producto_existente


def eliminar_producto(db: Session, id_producto: int):
    producto_existente = (
        db.query(Productos).filter(Productos.ID_Producto == id_producto).first()
    )
    if not producto_existente:
        return False

    db.delete(producto_existente)
    db.commit()
    return True


def verificar_stock(db: Session, id_producto: int):
    producto = db.query(Productos).filter(Productos.ID_Producto == id_producto).first()
    if producto:
        if producto.Stock_actual < producto.Stock_min:
            return f"Advertencia: El stock del producto '{producto.Nombre}' está por debajo del mínimo permitido."
        return f"El stock del producto '{producto.Nombre}' está dentro del rango permitido."
    return "Producto no encontrado."
