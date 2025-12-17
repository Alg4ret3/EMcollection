from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from app.models.productos import Productos, Marcas, Categorias
from app.models.facturas import Facturas
from app.models.detalle_facturas import DetalleFacturas


# =========================
# UTILIDADES
# =========================

def redondear_a_cientos(numero):
    if numero is None:
        raise ValueError("El valor no puede ser None")
    if not isinstance(numero, (int, float)):
        raise TypeError("El valor debe ser numérico")

    if numero % 100 == 0:
        return numero
    return ((numero // 100) + 1) * 100


def calcular_ganancia(precio_venta, precio_costo):
    return precio_venta - precio_costo


def calcular_precio(precio_costo, porcentaje):
    return redondear_a_cientos(precio_costo + (precio_costo * porcentaje))


def cambiar_estado(stock_actual):
    return stock_actual > 0


# =========================
# CREAR PRODUCTO
# =========================

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

    # Si no envían reventa, se calcula automático (25%)
    if not precio_venta_reventa:
        precio_venta_reventa = calcular_precio(precio_costo, 0.25)

    nuevo_producto = Productos(
        ID_Producto=id_producto,
        Nombre=nombre,
        Precio_costo=precio_costo,

        Precio_venta_normal=precio_venta_normal,
        Precio_venta_mayor=precio_venta_mayor,
        Precio_venta_reventa=precio_venta_reventa,

        Ganancia_Producto_normal=calcular_ganancia(precio_venta_normal, precio_costo),
        Ganancia_Producto_mayor=calcular_ganancia(precio_venta_mayor, precio_costo),
        Ganancia_Producto_reventa=calcular_ganancia(precio_venta_reventa, precio_costo),

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


# =========================
# OBTENER PRODUCTOS
# =========================

def obtener_productos(db: Session):
    return (
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


def obtener_producto_por_id(db: Session, id_producto: int):
    productos = (
        db.query(
            Productos.ID_Producto,
            Productos.Nombre,
            Productos.Precio_costo,
            
            Productos.Precio_venta_mayor,
            Productos.Precio_venta_normal,
            Productos.Precio_venta_reventa,
            
            Productos.Ganancia_Producto_mayor,
            Productos.Ganancia_Producto_normal,
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
        return []

    return (
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


# =========================
# ACTUALIZAR PRODUCTO
# =========================

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
    producto = db.query(Productos).filter(Productos.ID_Producto == id_producto).first()
    if not producto:
        return None

    if nombre:
        producto.Nombre = nombre

    if precio_costo:
        producto.Precio_costo = precio_costo

    if precio_venta_normal:
        producto.Precio_venta_normal = precio_venta_normal
    elif precio_costo:
        producto.Precio_venta_normal = calcular_precio(precio_costo, 0.5)

    if precio_venta_mayor:
        producto.Precio_venta_mayor = precio_venta_mayor
    elif precio_costo:
        producto.Precio_venta_mayor = calcular_precio(precio_costo, 0.35)

    if precio_venta_reventa:
        producto.Precio_venta_reventa = precio_venta_reventa
    elif precio_costo:
        producto.Precio_venta_reventa = calcular_precio(precio_costo, 0.25)

    producto.Ganancia_Producto_normal = calcular_ganancia(
        producto.Precio_venta_normal, producto.Precio_costo
    )
    producto.Ganancia_Producto_mayor = calcular_ganancia(
        producto.Precio_venta_mayor, producto.Precio_costo
    )
    producto.Ganancia_Producto_reventa = calcular_ganancia(
        producto.Precio_venta_reventa, producto.Precio_costo
    )

    if stock_actual is not None:
        producto.Stock_actual = stock_actual
        producto.Estado = cambiar_estado(stock_actual)

    if stock_min is not None:
        producto.Stock_min = stock_min
    if stock_max is not None:
        producto.Stock_max = stock_max

    if id_marca:
        producto.ID_Marca = id_marca
    if id_categoria:
        producto.ID_Categoria = id_categoria

    db.commit()
    db.refresh(producto)
    return producto
