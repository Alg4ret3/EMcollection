from PyQt5.QtWidgets import QWidget, QMessageBox
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from ..ui import Ui_Cambio
from ..database.database import SessionLocal
from ..controllers.producto_crud import buscar_productos, actualizar_producto
from ..controllers.caja_crud import Caja
from ..controllers.ingresos_crud import crear_ingreso
from ..models.pago_credito import PagoCredito
from ..utils.autocomplementado import configurar_autocompletado
from datetime import datetime

class Cambio_View(QWidget, Ui_Cambio):
    def __init__(self, parent=None):
        super(Cambio_View, self).__init__(parent)
        self.setupUi(self)
        self.db = SessionLocal()

        # Placeholders
        self.InputDevuelto.setPlaceholderText("Ingrese el nombre del producto devuelto")
        self.InputCambio.setPlaceholderText("Ingrese el nombre del producto de cambio")

        # Combo de precios
        self.ComboPrecios.addItems(["Precio Normal", "Precio Mayor", "Precio Reventa"])

        # Campos de precio solo lectura
        self.InputPrecioDevuelto.setReadOnly(True)
        self.InputPrecioCambio.setReadOnly(True)
        self.InputDiferencia.setReadOnly(True)

        # Inicializar autocompletados
        self.inicializar_autocompletados()

        # Eventos
        self.InputDevuelto.textChanged.connect(lambda: self.refrescar_autocompletado(self.InputDevuelto))
        self.InputCambio.textChanged.connect(lambda: self.refrescar_autocompletado(self.InputCambio))
        self.InputDevuelto.editingFinished.connect(self.cargar_producto_devuelto)
        self.InputCambio.editingFinished.connect(self.cargar_producto_cambio)
        self.ComboPrecios.currentIndexChanged.connect(self.actualizar_precios)
        self.SpinDevuelto.valueChanged.connect(self.sincronizar_spin)
        self.SpinCambio.valueChanged.connect(self.sincronizar_spin)
        self.BtnCambio.clicked.connect(self.confirmar_cambio)

        self.InputDevuelto.setFocus()

    # =========================
    # Autocompletado
    # =========================
    def inicializar_autocompletados(self):
        def obtener_todos_productos(db):
            return buscar_productos(db, "")
        configurar_autocompletado(self.InputDevuelto, obtener_todos_productos, "Nombre", self.db)
        configurar_autocompletado(self.InputCambio, obtener_todos_productos, "Nombre", self.db)

    def refrescar_autocompletado(self, input_widget):
        texto = input_widget.text().strip()
        if texto:
            productos = buscar_productos(self.db, texto)
            items = [p.Nombre for p in productos]
            input_widget.completer().model().setStringList(items)

    # =========================
    # Cargar productos exactos
    # =========================
    def cargar_producto_devuelto(self):
        self._cargar_producto(self.InputDevuelto, "producto_devuelto")

    def cargar_producto_cambio(self):
        self._cargar_producto(self.InputCambio, "producto_cambio")

    def _cargar_producto(self, input_widget, attr_name):
        nombre = input_widget.text().strip()
        if not nombre:
            setattr(self, attr_name, None)
            return
        productos = buscar_productos(self.db, nombre)
        producto_exacto = next((p for p in productos if p.Nombre.lower() == nombre.lower()), None)
        if not producto_exacto:
            QMessageBox.warning(self, "Error", f"No se encontró el producto: {nombre}")
            setattr(self, attr_name, None)
            input_widget.clear()
            return
        setattr(self, attr_name, producto_exacto)
        self.actualizar_precios()
        self.calcular_diferencia()

    # =========================
    # Precios y diferencia
    # =========================
    def actualizar_precios(self):
        tipo = self.ComboPrecios.currentText()
        if getattr(self, "producto_devuelto", None):
            self.InputPrecioDevuelto.setText(str(self.obtener_precio_por_tipo(self.producto_devuelto, tipo)))
        if getattr(self, "producto_cambio", None):
            self.InputPrecioCambio.setText(str(self.obtener_precio_por_tipo(self.producto_cambio, tipo)))
        self.calcular_diferencia()

    def obtener_precio_por_tipo(self, producto, tipo):
        if tipo == "Precio Normal":
            return producto.Precio_venta_normal
        elif tipo == "Precio Mayor":
            return producto.Precio_venta_mayor
        else:
            return producto.Precio_venta_reventa

    # =========================
    # Spin sincronizados
    # =========================
    def sincronizar_spin(self, valor):
        sender = self.sender()
        if sender == self.SpinDevuelto:
            self.SpinCambio.blockSignals(True)
            self.SpinCambio.setValue(valor)
            self.SpinCambio.blockSignals(False)
        else:
            self.SpinDevuelto.blockSignals(True)
            self.SpinDevuelto.setValue(valor)
            self.SpinDevuelto.blockSignals(False)
        self.calcular_diferencia()

    # =========================
    # Calcular diferencia
    # =========================
    def calcular_diferencia(self):
        try:
            devuelto = float(self.InputPrecioDevuelto.text()) * self.SpinDevuelto.value()
            cambio = float(self.InputPrecioCambio.text()) * self.SpinCambio.value()
            diferencia = cambio - devuelto
            if diferencia < 0:
                self.InputDiferencia.setText("0")
                self.InputDiferencia.setStyleSheet("color: red;")
                self.BtnCambio.setEnabled(False)
            else:
                self.InputDiferencia.setText(str(diferencia))
                self.InputDiferencia.setStyleSheet("color: green;")
                self.BtnCambio.setEnabled(True)
        except:
            self.InputDiferencia.setText("0")
            self.InputDiferencia.setStyleSheet("color: black;")
            self.BtnCambio.setEnabled(False)

    # =========================
    # Caja abierta
    # =========================
    def obtener_caja_abierta(self):
        return self.db.query(Caja).filter(Caja.Estado == True).first()

    # =========================
    # Registrar abono por cambio
    # =========================
    def confirmar_cambio(self):
        caja = self.obtener_caja_abierta()
        if not caja:
            QMessageBox.warning(self, "Error", "No hay ninguna caja abierta. No se puede realizar devoluciones.")
            return

        if not getattr(self, "producto_devuelto", None) or not getattr(self, "producto_cambio", None):
            QMessageBox.warning(self, "Error", "Seleccione ambos productos válidos")
            return

        if self.producto_devuelto.ID_Producto == self.producto_cambio.ID_Producto:
            QMessageBox.warning(self, "Error", "El producto devuelto y el de cambio no pueden ser el mismo")
            return

        if self.SpinCambio.value() > self.producto_cambio.Stock_actual:
            QMessageBox.warning(self, "Error", "Stock insuficiente para el producto de cambio")
            return

        resp = QMessageBox.question(self, "Confirmar", "¿Desea realizar el cambio?",
                                    QMessageBox.Yes | QMessageBox.No)
        if resp != QMessageBox.Yes:
            return

        try:
            devuelto_valor = self.SpinDevuelto.value()
            cambio_valor = self.SpinCambio.value()

            # Actualizar stocks
            actualizar_producto(
                self.db,
                self.producto_devuelto.ID_Producto,
                stock_actual=self.producto_devuelto.Stock_actual + devuelto_valor
            )

            actualizar_producto(
                self.db,
                self.producto_cambio.ID_Producto,
                stock_actual=self.producto_cambio.Stock_actual - cambio_valor
            )


            QMessageBox.information(self, "Éxito", "Cambio realizado correctamente")
            self.limpiar()

        except Exception as e:
            self.db.rollback()
            QMessageBox.critical(self, "Error", str(e))

    # =========================
    # Limpiar formulario
    # =========================
    def limpiar(self):
        self.InputDevuelto.clear()
        self.InputCambio.clear()
        self.InputPrecioDevuelto.clear()
        self.InputPrecioCambio.clear()
        self.InputDiferencia.clear()
        self.SpinDevuelto.setValue(1)
        self.SpinCambio.setValue(1)
        self.BtnCambio.setEnabled(True)
        self.InputDevuelto.setFocus()
