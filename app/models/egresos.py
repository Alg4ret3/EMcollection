from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, String, func
from sqlalchemy.orm import relationship
from app.database.database import Base
from datetime import datetime
from pytz import timezone

def get_local_time():
    # Cambia 'America/Bogota' por tu zona horaria local
    local_tz = timezone("America/Bogota")
    now = datetime.now(local_tz)
    return now.replace(microsecond=0)

class Egresos(Base):
    __tablename__ = "EGRESOS"

    ID_Egreso = Column(Integer, primary_key=True, autoincrement=True)
    Tipo_Egreso = Column(String(50), nullable=False)
    Fecha_Egreso = Column(DateTime(timezone=True), default=get_local_time)
    Descripcion = Column(String(255), nullable=True)
    Monto_Egreso = Column(Float, nullable=False)

    ID_Metodo_Pago = Column(Integer, ForeignKey("METODO_PAGO.ID_Metodo_Pago"))

    # Relaciones
    metodopago = relationship("MetodoPago", back_populates="egresos")
    analisisfinanciero = relationship("AnalisisFinanciero", back_populates="egresos")
