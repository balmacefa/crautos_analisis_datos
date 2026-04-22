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
    fuente: Optional[str] = None

class FacetValue(BaseModel):
    value: str
    count: int

class FacetResult(BaseModel):
    field_name: str
    counts: List[FacetValue]

class CarsResponse(BaseModel):
    total: int
    page: int
    limit: int
    cars: List[CarDetail]
    facets: Optional[List[FacetResult]] = None

class SummaryStats(BaseModel):
    total_cars: int
    avg_price_usd: float
    avg_price_crc: float
    top_brands: List[dict]
    last_updated: Optional[str] = None

class BrandStat(BaseModel):
    marca: str
    count: int
    avg_price_usd: float
    avg_price_crc: float

class MarketExtremeBrand(BaseModel):
    marca: str
    count: int

class MarketExtremeModel(BaseModel):
    marca: str
    modelo: str
    avg_price_crc: float
    count: int

class MarketExtremesResponse(BaseModel):
    most_popular_brand: Optional[MarketExtremeBrand] = None
    least_popular_brand: Optional[MarketExtremeBrand] = None
    highest_value_model: Optional[MarketExtremeModel] = None
    lowest_value_model: Optional[MarketExtremeModel] = None

class ModelTransmissionStat(BaseModel):
    marca: str
    modelo: str
    transmisión: str
    count: int

class DepreciationStat(BaseModel):
    marca: str
    modelo: str
    año: int
    count: int
    avg_price_usd: float
    avg_price_crc: float

class OpportunityCar(BaseModel):
    car_id: str
    url: str
    marca: str
    modelo: str
    año: int
    precio_usd: float
    precio_crc: float
    kilometraje_number: Optional[int] = None
    avg_price_usd: float
    avg_price_crc: float
    deviation_percent: float
    imagen_principal: Optional[str] = None

class FuelStat(BaseModel):
    combustible: str
    count: int
    avg_price_usd: float
    avg_price_crc: float

class TransmissionStat(BaseModel):
    transmisión: str
    count: int
    avg_price_usd: float
    avg_price_crc: float

class RatioStat(BaseModel):
    marca: str
    modelo: str
    avg_price_usd: float
    avg_price_crc: float
    avg_mileage: float
    ratio_usd: float
    ratio_crc: float
    count: int

class BrandComparisonStat(BaseModel):
    marca: str
    avg_price_usd: float
    avg_price_crc: float
    avg_mileage: float
    avg_year: float
    count: int

class CuriosityCar(BaseModel):
    car_id: str
    marca: str
    modelo: str
    año: int
    precio_usd: float
    precio_crc: float
    kilometraje_number: Optional[int] = None
    imagen_principal: Optional[str] = None
    title: str
    description: str

class CuriositiesResponse(BaseModel):
    most_expensive: Optional[CuriosityCar] = None
    cheapest: Optional[CuriosityCar] = None
    oldest: Optional[CuriosityCar] = None
    highest_mileage: Optional[CuriosityCar] = None

class ExplorerData(BaseModel):
    car_id: str
    marca: Optional[str] = None
    modelo: Optional[str] = None
    año: Optional[int] = None
    precio_crc: Optional[float] = None
    precio_usd: Optional[float] = None
    kilometraje_number: Optional[int] = None
    provincia: Optional[str] = None
    combustible: Optional[str] = None
    transmisión: Optional[str] = None

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

class VerdictResponse(BaseModel):
    marca: str
    modelo: str
    combustible: str
    count: int
    avg_price_usd: float
    avg_price_crc: float
    avg_mileage: Optional[float] = None
    verdict_title: str
    verdict_text: str
    is_good_option: bool
    market_share_percent: float
