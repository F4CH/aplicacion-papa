from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class AuditMixin:
    creado_en: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    modificado_en: Mapped[datetime | None] = mapped_column(DateTime, onupdate=func.now())


class Usuario(Base, AuditMixin):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    codigo: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    rol: Mapped[str] = mapped_column(String(30), nullable=False, default="consulta")
    nivel_seguridad: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    menu: Mapped[str] = mapped_column(String(60), nullable=False, default="")
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class Operador(Base, AuditMixin):
    __tablename__ = "operadores"

    codigo: Mapped[str] = mapped_column(String(5), primary_key=True)
    descripcion: Mapped[str] = mapped_column(String(100), nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    ingreso: Mapped[date | None] = mapped_column(Date)
    tinta: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    cuadraturas: Mapped[list["Cuadratura"]] = relationship(back_populates="operador")
    depositos: Mapped[list["Deposito"]] = relationship(back_populates="operador")


class Cuadratura(Base, AuditMixin):
    __tablename__ = "cuadraturas"
    __table_args__ = (UniqueConstraint("numero", name="uq_cuadraturas_numero"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    numero: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    turno: Mapped[int] = mapped_column(Integer, nullable=False)
    operador_codigo: Mapped[str] = mapped_column(ForeignKey("operadores.codigo"), nullable=False, index=True)

    combust_v: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    otros_v: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    deposito_v: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ventas_v: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    transbnk_v: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    transfer_v: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    piloto_v: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    operador: Mapped[Operador] = relationship(back_populates="cuadraturas")


class Deposito(Base, AuditMixin):
    __tablename__ = "depositos"
    __table_args__ = (UniqueConstraint("numero", name="uq_depositos_numero"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    numero: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    turno: Mapped[int] = mapped_column(Integer, nullable=False)
    operador_codigo: Mapped[str] = mapped_column(ForeignKey("operadores.codigo"), nullable=False, index=True)

    por_20k: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    por_10k: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    por_05k: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    por_02k: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    por_01k: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    por_05c: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    por_01c: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    por_50u: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    por_10u: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    aceite_c: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    promo_c: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    val_20k: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    val_10k: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    val_05k: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    val_02k: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    val_01k: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    val_05c: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    val_01c: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    val_50u: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    val_10u: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    aceite_v: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    promo_v: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    val_comb: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    val_otro: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_v: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    operador: Mapped[Operador] = relationship(back_populates="depositos")


class Configuracion(Base, AuditMixin):
    __tablename__ = "configuracion"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    empresa: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    rut: Mapped[str] = mapped_column(String(20), nullable=False, default="")
    local: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    email: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    membrete: Mapped[str] = mapped_column(String(500), nullable=False, default="")
