from PyQt5 import QtWidgets

from app.view.CajaView import Caja_View


def test_sumar_total_incluye_monto_de_apertura():
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    view = Caja_View.__new__(Caja_View)
    view.TablaIngresos = QtWidgets.QTableWidget(2, 4)
    view.OutEfectivo = QtWidgets.QLabel()
    view.OutTransferencia = QtWidgets.QLabel()
    view.OutTotal = QtWidgets.QLabel()
    view.OutApertura_2 = QtWidgets.QLabel()

    view.OutApertura_2.setText("150.00")

    view.TablaIngresos.setItem(0, 1, QtWidgets.QTableWidgetItem("Ingreso"))
    view.TablaIngresos.setItem(0, 2, QtWidgets.QTableWidgetItem("100"))
    view.TablaIngresos.setItem(0, 3, QtWidgets.QTableWidgetItem("50"))

    view.TablaIngresos.setItem(1, 1, QtWidgets.QTableWidgetItem("Egreso: X"))
    view.TablaIngresos.setItem(1, 2, QtWidgets.QTableWidgetItem("20"))
    view.TablaIngresos.setItem(1, 3, QtWidgets.QTableWidgetItem("10"))

    view.formatear_valor = lambda valor: f"{float(valor):,.2f}"

    view.sumar_total()

    assert view.OutTotal.text() == "270.00"
