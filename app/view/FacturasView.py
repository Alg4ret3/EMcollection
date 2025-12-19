from PyQt5.QtWidgets import (
    QWidget,
    QMessageBox,
)
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import pyqtSignal

from ..ui import Ui_Facturas
from ..database.database import SessionLocal
from ..controllers.facturas_crud import *
from ..controllers.producto_crud import *
from ..controllers.tipo_ingreso_crud import *
from ..controllers.ingresos_crud import *
from ..utils.enviar_notifi import enviar_notificacion
from ..utils.restructura_ticket import generate_ticket


class Facturas_View(QWidget, Ui_Facturas):
    enviar_facturas_A = pyqtSignal(dict)
    enviar_facturas_B = pyqtSignal(dict)
    enviar_facturas_C = pyqtSignal(dict)

    def __init__(self, parent=None):
        super(Facturas_View, self).__init__(parent)
        self.setupUi(self)

        self.InputBuscador.setPlaceholderText(
            "Buscar por ID, Cliente, Fecha, Metodo de pago o Tipo deFactura"
        )
        self.InputBuscador.textChanged.connect(self.buscar_facturas)

        self.TablaFacturas.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.TablaFacturas.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
        self.TablaFacturas.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.TablaFacturas.setColumnWidth(0, 50)
        self.TablaFacturas.setColumnWidth(5, 120)
        self.TablaFacturas.setColumnWidth(6, 120)


        #self.BtnEliminarFactura.clicked.connect(self.eliminar_factura)
        self.BtnGenerarTicket.clicked.connect(self.generar_ticket)
        self.BtnFacturaPagada.clicked.connect(self.factura_pagada)
        #self.BtnEditarFactura.clicked.connect(self.editar_factura)
        self.BtnVerCancelarVenta.clicked.connect(self.cancelar_venta)

    def showEvent(self, event):
        super().showEvent(event)
        self.limpiar_tabla_facturas()
        self.mostrar_facturas()
        self.InputBuscador.clear()
                        
    
    def cancelar_venta(self):
        ids = self.obtener_ids_seleccionados()

        if not ids:
            enviar_notificacion(
                "Advertencia", "No se seleccionaron facturas para cancelar."
            )
            return
        
        for id_factura in ids:
            facturas = obtener_factura_por_id(self.db, id_factura)
            if facturas.Estado == True:
                QMessageBox.warning(self, "Factura", f"La factura {id_factura} ya está pagada.")
                return 
            
            if facturas.tipofactura == "Credito":
                QMessageBox.warning(self, "Factura", f"La factura {id_factura} no es una factura de venta.")
                return

            factura_completa = obtener_factura_completa(self.db, id_factura)
            
            productos = factura_completa["Detalles"]
            
            for producto in productos:
                id_producto = producto["ID_Producto"]
                cantidad = producto["Cantidad"]
                
                producto = obtener_producto_por_id(self.db, id_producto)
                
                stock = producto[0].Stock_actual
                cantidad = cantidad + stock
                actualizar_producto(db=self.db, id_producto=id_producto, stock_actual=cantidad)
                
            eliminar_factura(self.db, id_factura)
            
        self.limpiar_tabla_facturas()
        self.mostrar_facturas()
        enviar_notificacion("Éxito", "Factura(s) cancelada(s) correctamente.")
        
    def mostrar_facturas(self):
        # Obtener datos de la tabla
        self.db = SessionLocal()
        rows = obtener_facturas(self.db)

        self.actualizar_tabla_facturas(rows)
        print("Mostrar facturas en la tabla")

        # Cerrar la conexión a la base de datos
        self.db.close()

    def limpiar_tabla_facturas(self):
        self.TablaFacturas.setRowCount(0)

    def actualizar_tabla_facturas(self, rows):
        if not rows:
            print("No hay filas para mostrar.")
            self.TablaFacturas.setRowCount(0)
            return

        try:
            self.TablaFacturas.setRowCount(0)

             # Ordenar filas por ID en orden descendente (de mayor a menor)
            rows.sort(key=lambda x: x.ID_Factura, reverse=False)
            # Iterar sobre las filas
            for row_idx, row in enumerate(rows):
                # Datos de la fila
                id_factura = str(row.ID_Factura)
                fecha = str(row.Fecha_Factura)
                fecha_conf = str(row.fecha_modificacion) if row.fecha_modificacion else "Actual"
                cliente = str(row.cliente)
                monto_efectivo = str(row.Monto_efectivo)
                monto_transaccion = str(row.Monto_TRANSACCION)
                estado = "Pagado" if row.Estado else "Pendiente"
                id_tipo_factura = str(row.tipofactura)
                id_metodo_pago = str(row.metodopago)
                usuario = str(row.usuario)
                total = row.Monto_efectivo + row.Monto_TRANSACCION
                domicilio = row.Domicilio

                self.TablaFacturas.insertRow(0)
                # Configurar items de la tabla
                items = [
                    (id_factura, 0),
                    (usuario, 1),
                    (id_metodo_pago, 2),
                    (cliente, 3),
                    (id_tipo_factura, 4),
                    (fecha, 5),
                    (fecha_conf, 6),  # Texto fijo
                    (monto_efectivo, 7),
                    (monto_transaccion, 8),
                    (str(total), 9),
                    (estado, 10),
                ]

                # Determinar color de texto
                if domicilio == True:
                    color = QtGui.QColor("green")
                else:
                    color = QtGui.QColor("black")

                # Añadir items a la tabla
                for value, col_idx in items:
                    item = QtWidgets.QTableWidgetItem(value)
                    item.setTextAlignment(QtCore.Qt.AlignCenter)
                    item.setForeground(QtGui.QBrush(color))
                    self.TablaFacturas.setItem(0, col_idx, item)
                    
        except Exception as e:
            print(f"Error al mostrar las facturas: {e}")

    def obtener_ids_seleccionados(self):
        """
        Obtiene los IDs de los productos seleccionados en la tabla.
        """
        filas_seleccionadas = self.TablaFacturas.selectionModel().selectedRows()
        ids = []

        for fila in filas_seleccionadas:
            id_producto = self.TablaFacturas.item(
                fila.row(), 0
            ).text()  # Columna 0: ID del producto
            ids.append(int(id_producto))

        return ids

    def eliminar_factura(self):
        """
        Elimina una factura.
        """
        # Obtener el ID de la factura seleccionada
        ids = self.obtener_ids_seleccionados()

        if not ids:
            enviar_notificacion(
                "Advertencia", "No se seleccionaron facturas para eliminar."
            )
            return
        
        for id_factura in ids:
            facturas = obtener_factura_por_id(self.db, id_factura)
            
            if facturas.tipofactura == "Credito":
                QMessageBox.warning(self, "Factura", f"La factura {id_factura} no es una factura de venta.")
                return
            

        respuesta = QtWidgets.QMessageBox.question(
            self,
            "Confirmar Eliminación",
            f"¿Está seguro de que desea eliminar {len(ids)} factura(s)?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
        )

        if respuesta == QtWidgets.QMessageBox.Yes:
            try:
                self.db = SessionLocal()

                for id_factura in ids:
                    eliminar_factura(self.db, id_factura)

                self.db.commit()
                enviar_notificacion("Éxito", "Factura(s) eliminada(s) correctamente.")

                # Actualizar la tabla
                self.limpiar_tabla_facturas()
                self.mostrar_facturas()

            except Exception as e:
                enviar_notificacion("Error", f"Error al eliminar facturas: {e}")
            finally:
                self.db.close()

    def buscar_facturas(self):
        """
        Busca facturas en la base de datos y actualiza la tabla.
        """
        busqueda = self.InputBuscador.text().strip()
        if not busqueda:
            self.mostrar_facturas()
            return

        self.db = SessionLocal()

        facturas = buscar_facturas(self.db, busqueda)
        self.actualizar_tabla_facturas(facturas)

        self.db.close()

    def generar_ticket(self):
        ids = self.obtener_ids_seleccionados()

        if not ids:
            QMessageBox.warning(self, "Advertencia", "No se seleccionaron facturas.")
            return

        db = SessionLocal()
        try:
            factura_completa = obtener_factura_completa(db, ids[0])

            if not factura_completa:
                QMessageBox.warning(self, "Error", "Factura no encontrada.")
                return

            factura = factura_completa["Factura"]
            cliente = factura_completa["Cliente"]
            detalles = factura_completa["Detalles"]

            subtotal = sum(d["Subtotal"] for d in detalles)
            descuento = factura["Descuento"]
            total = subtotal - descuento

            # 🧾 TEXTO TIPO TICKET
            texto = f"""
    ════════════════════════════
            TICKET DE VENTA
    ════════════════════════════
    Factura #: {factura['ID_Factura']}
    Fecha   : {factura['Fecha_Factura']}

    Cliente : {cliente['Nombre']} {cliente['Apellido']}
    Tel     : {cliente['Teléfono']}
    Dirección:
    {cliente['Direccion']}
    ────────────────────────────
    ITEM                TOTAL
    ────────────────────────────
    """

            for d in detalles:
                producto = d['Producto'][:16]  # corta para alinear
                texto += f"{producto:<16} x{d['Cantidad']:<2} ${d['Subtotal']:>8,.2f}\n"

            texto += f"""
    ────────────────────────────
    Subtotal        ${subtotal:>10,.2f}
    Descuento       ${descuento:>10,.2f}
    ────────────────────────────
    TOTAL           ${total:>10,.2f}
    ────────────────────────────
    Pago: {factura['MetodoPago']}
    ════════════════════════════
        ¡GRACIAS POR SU COMPRA!
    ════════════════════════════
    """

            QMessageBox.information(self, "🧾 Ticket de Venta", texto)

        finally:
            db.close()


    def factura_pagada(self):
        """
        Marca la factura como pagada.
        """
        ids = self.obtener_ids_seleccionados()

        if not ids:
            enviar_notificacion(
                "Advertencia", "No se seleccionaron productos para marcar como pagada."
            )
            return       
        
        try:
            db = SessionLocal()

            for id_factura in ids:
                factura = obtener_factura_por_id(db=db, id_factura=id_factura)
                
                if factura.tipofactura == "Credito":
                    QMessageBox.warning(self, "Factura", f"La factura {id_factura} no es una factura de venta.")
                    return
                
                if factura.Estado == True:
                    QMessageBox.warning(
                        self, "Factura", f"La factura {id_factura} ya está pagada."
                    )
                else:
                    actualizar_factura(db=db, id_factura=id_factura, estado=True)
                    tipo_ingreso = crear_tipo_ingreso(db=db, tipo_ingreso="Venta", id_factura=id_factura)
                    crear_ingreso(db=db, id_tipo_ingreso=tipo_ingreso.ID_Tipo_Ingreso)
            db.commit()
            enviar_notificacion(
                "Éxito", "Factura(s) marcada(s) como pagada(s) correctamente."
            )
            self.limpiar_tabla_facturas()
            self.mostrar_facturas()
        except Exception as e:
            enviar_notificacion(
                "Error", f"Error al marcar factura(s) como pagada(s): {e}"
            )
        finally:
            db.close()

    def editar_factura(self):
        """Abrir ventana de ventas con los datos de la factura seleccionada."""
        try:
            ids = self.obtener_ids_seleccionados()

            if not ids:
                enviar_notificacion(
                    "Advertencia", "No se seleccionaron facturas para editar."
                )
                return
            
            for id_factura in ids:
                facturas = obtener_factura_por_id(self.db, id_factura)
                
                if facturas.tipofactura == "Credito":
                    QMessageBox.warning(self, "Factura", f"La factura {id_factura} no es una factura de venta.")
                    return
            
            # Llamar a la función para obtener todos los datos de la factura
            factura_completa = obtener_factura_completa(self.db, ids[0])

            if not factura_completa:
                QMessageBox.showerror(
                    "Error", f"No se encontró la factura con ID {ids[0]}."
                )
                return

            if factura_completa["Factura"]["TipoFactura"] == "Detal":
                self.enviar_facturas_A.emit(factura_completa)

            elif factura_completa["Factura"]["TipoFactura"] == "Reventa":
                self.enviar_facturas_B.emit(factura_completa)

            elif factura_completa["Factura"]["TipoFactura"] == "Mayorista":
                self.enviar_facturas_C.emit(factura_completa)

        except Exception as e:
            print(f"Error al abrir ventana de ventas: {e}")
