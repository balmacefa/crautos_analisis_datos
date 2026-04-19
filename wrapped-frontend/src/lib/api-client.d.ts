/* eslint-disable */
/* tslint:disable */
// @ts-nocheck
/*
 * ---------------------------------------------------------------
 * ## THIS FILE WAS GENERATED VIA SWAGGER-TYPESCRIPT-API        ##
 * ##                                                           ##
 * ## AUTHOR: acacode                                           ##
 * ## SOURCE: https://github.com/acacode/swagger-typescript-api ##
 * ---------------------------------------------------------------
 */

/** BrandComparisonStat */
export interface BrandComparisonStat {
  /** Marca */
  marca: string;
  /** Avg Price Usd */
  avg_price_usd: number;
  /** Avg Price Crc */
  avg_price_crc: number;
  /** Avg Mileage */
  avg_mileage: number;
  /** Avg Year */
  avg_year: number;
  /** Count */
  count: number;
}
/** BrandStat */
export interface BrandStat {
  /** Marca */
  marca: string;
  /** Count */
  count: number;
  /** Avg Price Usd */
  avg_price_usd: number;
  /** Avg Price Crc */
  avg_price_crc: number;
}
/** CarDetail */
export interface CarDetail {
  /** Car Id */
  car_id: string;
  /** Url */
  url: string;
  /** Año */
  año?: number | null;
  /** Marca */
  marca?: string | null;
  /** Modelo */
  modelo?: string | null;
  /** Precio Crc */
  precio_crc?: number | null;
  /** Precio Usd */
  precio_usd?: number | null;
  /** Imagen Principal */
  imagen_principal?: string | null;
  /**
   * Galeria Imagenes
   * @default []
   */
  galeria_imagenes?: string[];
  vendedor?: SellerInfo | null;
  informacion_general?: GeneralInfo | null;
  /**
   * Equipamiento
   * @default []
   */
  equipamiento?: string[];
  /** Scraped At */
  scraped_at: string;
}
/** CarsResponse */
export interface CarsResponse {
  /** Total */
  total: number;
  /** Page */
  page: number;
  /** Limit */
  limit: number;
  /** Cars */
  cars: CarDetail[];
  /** Facets */
  facets?: FacetResult[] | null;
}
/** CuriositiesResponse */
export interface CuriositiesResponse {
  most_expensive?: CuriosityCar | null;
  cheapest?: CuriosityCar | null;
  oldest?: CuriosityCar | null;
  highest_mileage?: CuriosityCar | null;
}
/** CuriosityCar */
export interface CuriosityCar {
  /** Car Id */
  car_id: string;
  /** Marca */
  marca: string;
  /** Modelo */
  modelo: string;
  /** Año */
  año: number;
  /** Precio Usd */
  precio_usd: number;
  /** Precio Crc */
  precio_crc: number;
  /** Kilometraje Number */
  kilometraje_number?: number | null;
  /** Imagen Principal */
  imagen_principal?: string | null;
  /** Title */
  title: string;
  /** Description */
  description: string;
}
/** DepreciationStat */
export interface DepreciationStat {
  /** Marca */
  marca: string;
  /** Modelo */
  modelo: string;
  /** Año */
  año: number;
  /** Count */
  count: number;
  /** Avg Price Usd */
  avg_price_usd: number;
  /** Avg Price Crc */
  avg_price_crc: number;
}
/** ExplorerData */
export interface ExplorerData {
  /** Car Id */
  car_id: string;
  /** Marca */
  marca?: string | null;
  /** Modelo */
  modelo?: string | null;
  /** Año */
  año?: number | null;
  /** Precio Crc */
  precio_crc?: number | null;
  /** Precio Usd */
  precio_usd?: number | null;
  /** Kilometraje Number */
  kilometraje_number?: number | null;
  /** Provincia */
  provincia?: string | null;
  /** Combustible */
  combustible?: string | null;
  /** Transmisión */
  transmisión?: string | null;
}
/** FacetResult */
export interface FacetResult {
  /** Field Name */
  field_name: string;
  /** Counts */
  counts: FacetValue[];
}
/** FacetValue */
export interface FacetValue {
  /** Value */
  value: string;
  /** Count */
  count: number;
}
/** FuelStat */
export interface FuelStat {
  /** Combustible */
  combustible: string;
  /** Count */
  count: number;
  /** Avg Price Usd */
  avg_price_usd: number;
  /** Avg Price Crc */
  avg_price_crc: number;
}
/** GeneralInfo */
export interface GeneralInfo {
  /** Cilindrada */
  cilindrada?: string | null;
  /** Estilo */
  estilo?: string | null;
  /** Pasajeros */
  pasajeros?: string | null;
  /** Combustible */
  combustible?: string | null;
  /** Transmisión */
  transmisión?: string | null;
  /** Estado */
  estado?: string | null;
  /** Kilometraje */
  kilometraje?: string | null;
  /** Placa */
  placa?: string | null;
  /** Color Exterior */
  color_exterior?: string | null;
  /** Color Interior */
  color_interior?: string | null;
  /** Puertas */
  puertas?: string | null;
  /** Ya Pagó Impuestos */
  ya_pagó_impuestos?: string | null;
  /** Precio Negociable */
  precio_negociable?: string | null;
  /** Se Recibe Vehículo */
  se_recibe_vehículo?: string | null;
  /** Provincia */
  provincia?: string | null;
  /** Fecha De Ingreso */
  fecha_de_ingreso?: string | null;
  /** Comentario Vendedor */
  comentario_vendedor?: string | null;
  /** Kilometraje Number */
  kilometraje_number?: number | null;
  /** Cilindrada Number */
  cilindrada_number?: number | null;
}
/** HTTPValidationError */
export interface HTTPValidationError {
  /** Detail */
  detail?: ValidationError[];
}
/** MarketExtremeBrand */
export interface MarketExtremeBrand {
  /** Marca */
  marca: string;
  /** Count */
  count: number;
}
/** MarketExtremeModel */
export interface MarketExtremeModel {
  /** Marca */
  marca: string;
  /** Modelo */
  modelo: string;
  /** Avg Price Crc */
  avg_price_crc: number;
  /** Count */
  count: number;
}
/** MarketExtremesResponse */
export interface MarketExtremesResponse {
  most_popular_brand?: MarketExtremeBrand | null;
  least_popular_brand?: MarketExtremeBrand | null;
  highest_value_model?: MarketExtremeModel | null;
  lowest_value_model?: MarketExtremeModel | null;
}
/** ModelStat */
export interface ModelStat {
  /** Marca */
  marca: string;
  /** Modelo */
  modelo: string;
  /** Count */
  count: number;
  /** Avg Price Usd */
  avg_price_usd: number;
  /** Avg Price Crc */
  avg_price_crc: number;
}
/** ModelTransmissionStat */
export interface ModelTransmissionStat {
  /** Marca */
  marca: string;
  /** Modelo */
  modelo: string;
  /** Transmisión */
  transmisión: string;
  /** Count */
  count: number;
}
/** OpportunityCar */
export interface OpportunityCar {
  /** Car Id */
  car_id: string;
  /** Url */
  url: string;
  /** Marca */
  marca: string;
  /** Modelo */
  modelo: string;
  /** Año */
  año: number;
  /** Precio Usd */
  precio_usd: number;
  /** Precio Crc */
  precio_crc: number;
  /** Kilometraje Number */
  kilometraje_number?: number | null;
  /** Avg Price Usd */
  avg_price_usd: number;
  /** Avg Price Crc */
  avg_price_crc: number;
  /** Deviation Percent */
  deviation_percent: number;
  /** Imagen Principal */
  imagen_principal?: string | null;
}
/** ProvinceStat */
export interface ProvinceStat {
  /** Provincia */
  provincia: string;
  /** Count */
  count: number;
  /** Avg Price Usd */
  avg_price_usd: number;
  /** Avg Price Crc */
  avg_price_crc: number;
}
/** RatioStat */
export interface RatioStat {
  /** Marca */
  marca: string;
  /** Modelo */
  modelo: string;
  /** Avg Price Usd */
  avg_price_usd: number;
  /** Avg Price Crc */
  avg_price_crc: number;
  /** Avg Mileage */
  avg_mileage: number;
  /** Ratio Usd */
  ratio_usd: number;
  /** Ratio Crc */
  ratio_crc: number;
  /** Count */
  count: number;
}
/** SellerInfo */
export interface SellerInfo {
  /** Nombre */
  nombre?: string | null;
  /** Teléfono */
  teléfono?: string | null;
  /** Whatsapp */
  whatsapp?: string | null;
}
/** SummaryStats */
export interface SummaryStats {
  /** Total Cars */
  total_cars: number;
  /** Avg Price Usd */
  avg_price_usd: number;
  /** Avg Price Crc */
  avg_price_crc: number;
  /** Top Brands */
  top_brands: Record<string, any>[];
  /** Last Updated */
  last_updated?: string | null;
}
/** TransmissionStat */
export interface TransmissionStat {
  /** Transmisión */
  transmisión: string;
  /** Count */
  count: number;
  /** Avg Price Usd */
  avg_price_usd: number;
  /** Avg Price Crc */
  avg_price_crc: number;
}
/** ValidationError */
export interface ValidationError {
  /** Location */
  loc: (string | number)[];
  /** Message */
  msg: string;
  /** Error Type */
  type: string;
  /** Input */
  input?: any;
  /** Context */
  ctx?: object;
}
/** VerdictResponse */
export interface VerdictResponse {
  /** Marca */
  marca: string;
  /** Modelo */
  modelo: string;
  /** Combustible */
  combustible: string;
  /** Count */
  count: number;
  /** Avg Price Usd */
  avg_price_usd: number;
  /** Avg Price Crc */
  avg_price_crc: number;
  /** Avg Mileage */
  avg_mileage?: number | null;
  /** Verdict Title */
  verdict_title: string;
  /** Verdict Text */
  verdict_text: string;
  /** Is Good Option */
  is_good_option: boolean;
  /** Market Share Percent */
  market_share_percent: number;
}
/** YearStat */
export interface YearStat {
  /** Año */
  año: number;
  /** Count */
  count: number;
  /** Avg Price Usd */
  avg_price_usd: number;
  /** Avg Price Crc */
  avg_price_crc: number;
}
export type QueryParamsType = Record<string | number, any>;
export type ResponseFormat = keyof Omit<Body, "body" | "bodyUsed">;
export interface FullRequestParams extends Omit<RequestInit, "body"> {
  /** set parameter to `true` for call `securityWorker` for this request */
  secure?: boolean;
  /** request path */
  path: string;
  /** content type of request body */
  type?: ContentType;
  /** query params */
  query?: QueryParamsType;
  /** format of response (i.e. response.json() -> format: "json") */
  format?: ResponseFormat;
  /** request body */
  body?: unknown;
  /** base url */
  baseUrl?: string;
  /** request cancellation token */
  cancelToken?: CancelToken;
}
export type RequestParams = Omit<
  FullRequestParams,
  "body" | "method" | "query" | "path"
>;
export interface ApiConfig<SecurityDataType = unknown> {
  baseUrl?: string;
  baseApiParams?: Omit<RequestParams, "baseUrl" | "cancelToken" | "signal">;
  securityWorker?: (
    securityData: SecurityDataType | null,
  ) => Promise<RequestParams | void> | RequestParams | void;
  customFetch?: typeof fetch;
}
export interface HttpResponse<D extends unknown, E extends unknown = unknown>
  extends Response {
  data: D;
  error: E;
}
type CancelToken = Symbol | string | number;
export declare enum ContentType {
  Json = "application/json",
  JsonApi = "application/vnd.api+json",
  FormData = "multipart/form-data",
  UrlEncoded = "application/x-www-form-urlencoded",
  Text = "text/plain",
}
export declare class HttpClient<SecurityDataType = unknown> {
  baseUrl: string;
  private securityData;
  private securityWorker?;
  private abortControllers;
  private customFetch;
  private baseApiParams;
  constructor(apiConfig?: ApiConfig<SecurityDataType>);
  setSecurityData: (data: SecurityDataType | null) => void;
  protected encodeQueryParam(key: string, value: any): string;
  protected addQueryParam(query: QueryParamsType, key: string): string;
  protected addArrayQueryParam(query: QueryParamsType, key: string): any;
  protected toQueryString(rawQuery?: QueryParamsType): string;
  protected addQueryParams(rawQuery?: QueryParamsType): string;
  private contentFormatters;
  protected mergeRequestParams(
    params1: RequestParams,
    params2?: RequestParams,
  ): RequestParams;
  protected createAbortSignal: (
    cancelToken: CancelToken,
  ) => AbortSignal | undefined;
  abortRequest: (cancelToken: CancelToken) => void;
  request: <T = any, E = any>({
    body,
    secure,
    path,
    type,
    query,
    format,
    baseUrl,
    cancelToken,
    ...params
  }: FullRequestParams) => Promise<HttpResponse<T, E>>;
}
/**
 * @title Crautos Async Data API
 * @version 0.1.0
 */
export declare class Api<
  SecurityDataType extends unknown,
> extends HttpClient<SecurityDataType> {
  api: {
    /**
     * No description
     *
     * @name GetCarsApiCarsGet
     * @summary Get Cars
     * @request GET:/api/cars
     */
    getCarsApiCarsGet: (
      query?: {
        /**
         * Page
         * @min 1
         * @default 1
         */
        page?: number;
        /**
         * Limit
         * @min 1
         * @max 100
         * @default 50
         */
        limit?: number;
        /** Marca */
        marca?: string | null;
        /** Modelo */
        modelo?: string | null;
        /** Year Min */
        year_min?: number | null;
        /** Year Max */
        year_max?: number | null;
      },
      params?: RequestParams,
    ) => Promise<HttpResponse<CarsResponse, HTTPValidationError>>;
    /**
     * No description
     *
     * @name SearchCarsApiSearchGet
     * @summary Search Cars
     * @request GET:/api/search
     */
    searchCarsApiSearchGet: (
      query: {
        /**
         * Q
         * @minLength 2
         */
        q: string;
        /**
         * Page
         * @min 1
         * @default 1
         */
        page?: number;
        /**
         * Limit
         * @min 1
         * @max 100
         * @default 50
         */
        limit?: number;
      },
      params?: RequestParams,
    ) => Promise<HttpResponse<CarsResponse, HTTPValidationError>>;
    /**
     * No description
     *
     * @name GetCarApiCarsCarIdGet
     * @summary Get Car
     * @request GET:/api/cars/{car_id}
     */
    getCarApiCarsCarIdGet: (
      carId: string,
      params?: RequestParams,
    ) => Promise<HttpResponse<CarDetail, HTTPValidationError>>;
    /**
     * No description
     *
     * @name GetSummaryApiInsightsSummaryGet
     * @summary Get Summary
     * @request GET:/api/insights/summary
     */
    getSummaryApiInsightsSummaryGet: (
      params?: RequestParams,
    ) => Promise<HttpResponse<SummaryStats, any>>;
    /**
     * No description
     *
     * @name GetBrandsInsightApiInsightsBrandsGet
     * @summary Get Brands Insight
     * @request GET:/api/insights/brands
     */
    getBrandsInsightApiInsightsBrandsGet: (
      params?: RequestParams,
    ) => Promise<HttpResponse<BrandStat[], any>>;
    /**
     * No description
     *
     * @name GetTopRatiosApiInsightsRatiosTopGet
     * @summary Get Top Ratios
     * @request GET:/api/insights/ratios/top
     */
    getTopRatiosApiInsightsRatiosTopGet: (
      params?: RequestParams,
    ) => Promise<HttpResponse<RatioStat[], any>>;
    /**
     * No description
     *
     * @name GetBrandComparisonApiInsightsBrandsCompareGet
     * @summary Get Brand Comparison
     * @request GET:/api/insights/brands/compare
     */
    getBrandComparisonApiInsightsBrandsCompareGet: (
      query: {
        /**
         * Brands
         * Comma separated list of brands
         */
        brands: string;
      },
      params?: RequestParams,
    ) => Promise<HttpResponse<BrandComparisonStat[], HTTPValidationError>>;
    /**
     * No description
     *
     * @name GetYearsInsightApiInsightsYearsGet
     * @summary Get Years Insight
     * @request GET:/api/insights/years
     */
    getYearsInsightApiInsightsYearsGet: (
      params?: RequestParams,
    ) => Promise<HttpResponse<YearStat[], any>>;
    /**
     * No description
     *
     * @name GetProvincesInsightApiInsightsProvincesGet
     * @summary Get Provinces Insight
     * @request GET:/api/insights/provinces
     */
    getProvincesInsightApiInsightsProvincesGet: (
      params?: RequestParams,
    ) => Promise<HttpResponse<ProvinceStat[], any>>;
    /**
     * No description
     *
     * @name GetDepreciationInsightApiInsightsDepreciationGet
     * @summary Get Depreciation Insight
     * @request GET:/api/insights/depreciation
     */
    getDepreciationInsightApiInsightsDepreciationGet: (
      params?: RequestParams,
    ) => Promise<HttpResponse<DepreciationStat[], any>>;
    /**
     * No description
     *
     * @name GetFuelDistributionApiInsightsDistributionFuelGet
     * @summary Get Fuel Distribution
     * @request GET:/api/insights/distribution/fuel
     */
    getFuelDistributionApiInsightsDistributionFuelGet: (
      params?: RequestParams,
    ) => Promise<HttpResponse<FuelStat[], any>>;
    /**
     * No description
     *
     * @name GetTransmissionDistributionApiInsightsDistributionTransmissionGet
     * @summary Get Transmission Distribution
     * @request GET:/api/insights/distribution/transmission
     */
    getTransmissionDistributionApiInsightsDistributionTransmissionGet: (
      params?: RequestParams,
    ) => Promise<HttpResponse<TransmissionStat[], any>>;
    /**
     * No description
     *
     * @name GetOpportunitiesApiInsightsOpportunitiesGet
     * @summary Get Opportunities
     * @request GET:/api/insights/opportunities
     */
    getOpportunitiesApiInsightsOpportunitiesGet: (
      params?: RequestParams,
    ) => Promise<HttpResponse<OpportunityCar[], any>>;
    /**
     * No description
     *
     * @name GetModelsInsightApiInsightsModelsGet
     * @summary Get Models Insight
     * @request GET:/api/insights/models
     */
    getModelsInsightApiInsightsModelsGet: (
      params?: RequestParams,
    ) => Promise<HttpResponse<ModelStat[], any>>;
    /**
     * No description
     *
     * @name GetPriceRangesCrcApiInsightsPriceRangesCrcGet
     * @summary Get Price Ranges Crc
     * @request GET:/api/insights/price-ranges-crc
     */
    getPriceRangesCrcApiInsightsPriceRangesCrcGet: (
      params?: RequestParams,
    ) => Promise<HttpResponse<any, any>>;
    /**
     * No description
     *
     * @name GetMileageInsightApiInsightsMileageGet
     * @summary Get Mileage Insight
     * @request GET:/api/insights/mileage
     */
    getMileageInsightApiInsightsMileageGet: (
      params?: RequestParams,
    ) => Promise<HttpResponse<any, any>>;
    /**
     * No description
     *
     * @name GetCuriositiesApiInsightsCuriositiesGet
     * @summary Get Curiosities
     * @request GET:/api/insights/curiosities
     */
    getCuriositiesApiInsightsCuriositiesGet: (
      params?: RequestParams,
    ) => Promise<HttpResponse<CuriositiesResponse, any>>;
    /**
     * No description
     *
     * @name GetExplorerDataApiInsightsExplorerGet
     * @summary Get Explorer Data
     * @request GET:/api/insights/explorer
     */
    getExplorerDataApiInsightsExplorerGet: (
      params?: RequestParams,
    ) => Promise<HttpResponse<ExplorerData[], any>>;
    /**
     * No description
     *
     * @name GetMarketExtremesApiInsightsMarketExtremesGet
     * @summary Get Market Extremes
     * @request GET:/api/insights/market-extremes
     */
    getMarketExtremesApiInsightsMarketExtremesGet: (
      params?: RequestParams,
    ) => Promise<HttpResponse<MarketExtremesResponse, any>>;
    /**
     * No description
     *
     * @name GetModelsTransmissionsApiInsightsModelsTransmissionsGet
     * @summary Get Models Transmissions
     * @request GET:/api/insights/models/transmissions
     */
    getModelsTransmissionsApiInsightsModelsTransmissionsGet: (
      params?: RequestParams,
    ) => Promise<HttpResponse<ModelTransmissionStat[], any>>;
    /**
     * No description
     *
     * @name GetVerdictApiInsightsVerdictGet
     * @summary Get Verdict
     * @request GET:/api/insights/verdict
     */
    getVerdictApiInsightsVerdictGet: (
      query: {
        /** Marca */
        marca: string;
        /** Modelo */
        modelo: string;
        /** Combustible */
        combustible: string;
      },
      params?: RequestParams,
    ) => Promise<HttpResponse<VerdictResponse, HTTPValidationError>>;
    /**
     * No description
     *
     * @name GetCarsV2ApiV2CarsGet
     * @summary Get Cars V2
     * @request GET:/api/v2/cars
     */
    getCarsV2ApiV2CarsGet: (
      query?: {
        /**
         * Q
         * @default "*"
         */
        q?: string;
        /**
         * Page
         * @min 1
         * @default 1
         */
        page?: number;
        /**
         * Limit
         * @min 1
         * @max 100
         * @default 50
         */
        limit?: number;
        /** Brands */
        brands?: string | null;
        /** Models */
        models?: string | null;
        /** Year Min */
        year_min?: number | null;
        /** Year Max */
        year_max?: number | null;
        /** Price Min */
        price_min?: number | null;
        /** Price Max */
        price_max?: number | null;
        /** Km Min */
        km_min?: number | null;
        /** Km Max */
        km_max?: number | null;
        /** Provinces */
        provinces?: string | null;
        /** Fuels */
        fuels?: string | null;
        /** Transmissions */
        transmissions?: string | null;
        /**
         * Sort By
         * @default "año:desc"
         */
        sort_by?: string | null;
        /**
         * Facet By
         * @default "marca,año,combustible,transmisión,provincia"
         */
        facet_by?: string | null;
      },
      params?: RequestParams,
    ) => Promise<HttpResponse<CarsResponse, HTTPValidationError>>;
  };
}
export {};
