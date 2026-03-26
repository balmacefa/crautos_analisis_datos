from typing import List, Optional
from pydantic import BaseModel

class SellerInfo(BaseModel):
    nombre: Optional[str] = None
    teléfono: Optional[str] = None
    whatsapp: Optional[str] = None

class GeneralInfo(BaseModel):
    cilindrada: Optional[str] = None
    estilo: Optional[str] = None
    pasajeros: Optional[str] = None
    combustible: Optional[str] = None
    transmisión: Optional[str] = None
    estado: Optional[str] = None
    kilometraje: Optional[str] = None
    placa: Optional[str] = None
    color_exterior: Optional[str] = None
    color_interior: Optional[str] = None
    puertas: Optional[str] = None
    ya_pagó_impuestos: Optional[str] = None
    precio_negociable: Optional[str] = None
    se_recibe_vehículo: Optional[str] = None
    provincia: Optional[str] = None
    fecha_de_ingreso: Optional[str] = None
    comentario_vendedor: Optional[str] = None
    kilometraje_number: Optional[int] = None
    cilindrada_number: Optional[int] = None

class CarDetail(BaseModel):
    car_id: str
    url: str
    año: Optional[int] = None
    marca: Optional[str] = None
    modelo: Optional[str] = None
    precio_crc: Optional[float] = None
    precio_usd: Optional[float] = None
    imagen_principal: Optional[str] = None
    galeria_imagenes: List[str] = []
    vendedor: Optional[SellerInfo] = None
    informacion_general: Optional[GeneralInfo] = None
    equipamiento: List[str] = []
    scraped_at: str

class CarsResponse(BaseModel):
    total: int
    page: int
    limit: int
    cars: List[CarDetail]

class SummaryStats(BaseModel):
    total_cars: int
    avg_price_usd: float
    avg_price_crc: float
    top_brands: List[dict]

class BrandStat(BaseModel):
    marca: str
    count: int
    avg_price_usd: float
    avg_price_crc: float

class YearStat(BaseModel):
    año: int
    count: int
    avg_price_usd: float
    avg_price_crc: float

class ProvinceStat(BaseModel):
    provincia: str
    count: int
    avg_price_usd: float
    avg_price_crc: float

class ModelStat(BaseModel):
    marca: str
    modelo: str
    count: int
    avg_price_usd: float
    avg_price_crc: float
