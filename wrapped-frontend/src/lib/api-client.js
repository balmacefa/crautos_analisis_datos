
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

export var ContentType;
(function (ContentType) {
  ContentType["Json"] = "application/json";
  ContentType["JsonApi"] = "application/vnd.api+json";
  ContentType["FormData"] = "multipart/form-data";
  ContentType["UrlEncoded"] = "application/x-www-form-urlencoded";
  ContentType["Text"] = "text/plain";
})(ContentType || (ContentType = {}));
export class HttpClient {
  baseUrl = "";
  securityData = null;
  securityWorker;
  abortControllers = new Map();
  customFetch = (...fetchParams) => fetch(...fetchParams);
  baseApiParams = {
    credentials: "same-origin",
    headers: {},
    redirect: "follow",
    referrerPolicy: "no-referrer",
  };
  constructor(apiConfig = {}) {
    Object.assign(this, apiConfig);
  }
  setSecurityData = (data) => {
    this.securityData = data;
  };
  encodeQueryParam(key, value) {
    const encodedKey = encodeURIComponent(key);
    return `${encodedKey}=${encodeURIComponent(typeof value === "number" ? value : `${value}`)}`;
  }
  addQueryParam(query, key) {
    return this.encodeQueryParam(key, query[key]);
  }
  addArrayQueryParam(query, key) {
    const value = query[key];
    return value.map((v) => this.encodeQueryParam(key, v)).join("&");
  }
  toQueryString(rawQuery) {
    const query = rawQuery || {};
    const keys = Object.keys(query).filter(
      (key) => "undefined" !== typeof query[key],
    );
    return keys
      .map((key) =>
        Array.isArray(query[key])
          ? this.addArrayQueryParam(query, key)
          : this.addQueryParam(query, key),
      )
      .join("&");
  }
  addQueryParams(rawQuery) {
    const queryString = this.toQueryString(rawQuery);
    return queryString ? `?${queryString}` : "";
  }
  contentFormatters = {
    [ContentType.Json]: (input) =>
      input !== null && (typeof input === "object" || typeof input === "string")
        ? JSON.stringify(input)
        : input,
    [ContentType.JsonApi]: (input) =>
      input !== null && (typeof input === "object" || typeof input === "string")
        ? JSON.stringify(input)
        : input,
    [ContentType.Text]: (input) =>
      input !== null && typeof input !== "string"
        ? JSON.stringify(input)
        : input,
    [ContentType.FormData]: (input) => {
      if (input instanceof FormData) {
        return input;
      }
      return Object.keys(input || {}).reduce((formData, key) => {
        const property = input[key];
        formData.append(
          key,
          property instanceof Blob
            ? property
            : typeof property === "object" && property !== null
              ? JSON.stringify(property)
              : `${property}`,
        );
        return formData;
      }, new FormData());
    },
    [ContentType.UrlEncoded]: (input) => this.toQueryString(input),
  };
  mergeRequestParams(params1, params2) {
    return {
      ...this.baseApiParams,
      ...params1,
      ...(params2 || {}),
      headers: {
        ...(this.baseApiParams.headers || {}),
        ...(params1.headers || {}),
        ...((params2 && params2.headers) || {}),
      },
    };
  }
  createAbortSignal = (cancelToken) => {
    if (this.abortControllers.has(cancelToken)) {
      const abortController = this.abortControllers.get(cancelToken);
      if (abortController) {
        return abortController.signal;
      }
      return void 0;
    }
    const abortController = new AbortController();
    this.abortControllers.set(cancelToken, abortController);
    return abortController.signal;
  };
  abortRequest = (cancelToken) => {
    const abortController = this.abortControllers.get(cancelToken);
    if (abortController) {
      abortController.abort();
      this.abortControllers.delete(cancelToken);
    }
  };
  request = async ({
    body,
    secure,
    path,
    type,
    query,
    format,
    baseUrl,
    cancelToken,
    ...params
  }) => {
    const secureParams =
      ((typeof secure === "boolean" ? secure : this.baseApiParams.secure) &&
        this.securityWorker &&
        (await this.securityWorker(this.securityData))) ||
      {};
    const requestParams = this.mergeRequestParams(params, secureParams);
    const queryString = query && this.toQueryString(query);
    const payloadFormatter = this.contentFormatters[type || ContentType.Json];
    const responseFormat = format || requestParams.format;
    return this.customFetch(
      `${baseUrl || this.baseUrl || ""}${path}${queryString ? `?${queryString}` : ""}`,
      {
        ...requestParams,
        headers: {
          ...(requestParams.headers || {}),
          ...(type && type !== ContentType.FormData
            ? { "Content-Type": type }
            : {}),
        },
        signal:
          (cancelToken
            ? this.createAbortSignal(cancelToken)
            : requestParams.signal) || null,
        body:
          typeof body === "undefined" || body === null
            ? null
            : payloadFormatter(body),
      },
    ).then(async (response) => {
      const r = response;
      r.data = null;
      r.error = null;
      const responseToParse = responseFormat ? response.clone() : response;
      const data = !responseFormat
        ? r
        : await responseToParse[responseFormat]()
            .then((data) => {
              if (r.ok) {
                r.data = data;
              } else {
                r.error = data;
              }
              return r;
            })
            .catch((e) => {
              r.error = e;
              return r;
            });
      if (cancelToken) {
        this.abortControllers.delete(cancelToken);
      }
      if (!response.ok) throw data;
      return data;
    });
  };
}
/**
 * @title Crautos Async Data API
 * @version 0.1.0
 */
export class Api extends HttpClient {
  api = {
    /**
     * No description
     *
     * @name GetCarsApiCarsGet
     * @summary Get Cars
     * @request GET:/api/cars
     */
    getCarsApiCarsGet: (query, params = {}) =>
      this.request({
        path: `/api/cars`,
        method: "GET",
        query: query,
        format: "json",
        ...params,
      }),
    /**
     * No description
     *
     * @name SearchCarsApiSearchGet
     * @summary Search Cars
     * @request GET:/api/search
     */
    searchCarsApiSearchGet: (query, params = {}) =>
      this.request({
        path: `/api/search`,
        method: "GET",
        query: query,
        format: "json",
        ...params,
      }),
    /**
     * No description
     *
     * @name GetCarApiCarsCarIdGet
     * @summary Get Car
     * @request GET:/api/cars/{car_id}
     */
    getCarApiCarsCarIdGet: (carId, params = {}) =>
      this.request({
        path: `/api/cars/${carId}`,
        method: "GET",
        format: "json",
        ...params,
      }),
    /**
     * No description
     *
     * @name GetSummaryApiInsightsSummaryGet
     * @summary Get Summary
     * @request GET:/api/insights/summary
     */
    getSummaryApiInsightsSummaryGet: (params = {}) =>
      this.request({
        path: `/api/insights/summary`,
        method: "GET",
        format: "json",
        ...params,
      }),
    /**
     * No description
     *
     * @name GetBrandsInsightApiInsightsBrandsGet
     * @summary Get Brands Insight
     * @request GET:/api/insights/brands
     */
    getBrandsInsightApiInsightsBrandsGet: (params = {}) =>
      this.request({
        path: `/api/insights/brands`,
        method: "GET",
        format: "json",
        ...params,
      }),
    /**
     * No description
     *
     * @name GetTopRatiosApiInsightsRatiosTopGet
     * @summary Get Top Ratios
     * @request GET:/api/insights/ratios/top
     */
    getTopRatiosApiInsightsRatiosTopGet: (params = {}) =>
      this.request({
        path: `/api/insights/ratios/top`,
        method: "GET",
        format: "json",
        ...params,
      }),
    /**
     * No description
     *
     * @name GetBrandComparisonApiInsightsBrandsCompareGet
     * @summary Get Brand Comparison
     * @request GET:/api/insights/brands/compare
     */
    getBrandComparisonApiInsightsBrandsCompareGet: (query, params = {}) =>
      this.request({
        path: `/api/insights/brands/compare`,
        method: "GET",
        query: query,
        format: "json",
        ...params,
      }),
    /**
     * No description
     *
     * @name GetYearsInsightApiInsightsYearsGet
     * @summary Get Years Insight
     * @request GET:/api/insights/years
     */
    getYearsInsightApiInsightsYearsGet: (params = {}) =>
      this.request({
        path: `/api/insights/years`,
        method: "GET",
        format: "json",
        ...params,
      }),
    /**
     * No description
     *
     * @name GetProvincesInsightApiInsightsProvincesGet
     * @summary Get Provinces Insight
     * @request GET:/api/insights/provinces
     */
    getProvincesInsightApiInsightsProvincesGet: (params = {}) =>
      this.request({
        path: `/api/insights/provinces`,
        method: "GET",
        format: "json",
        ...params,
      }),
    /**
     * No description
     *
     * @name GetDepreciationInsightApiInsightsDepreciationGet
     * @summary Get Depreciation Insight
     * @request GET:/api/insights/depreciation
     */
    getDepreciationInsightApiInsightsDepreciationGet: (params = {}) =>
      this.request({
        path: `/api/insights/depreciation`,
        method: "GET",
        format: "json",
        ...params,
      }),
    /**
     * No description
     *
     * @name GetFuelDistributionApiInsightsDistributionFuelGet
     * @summary Get Fuel Distribution
     * @request GET:/api/insights/distribution/fuel
     */
    getFuelDistributionApiInsightsDistributionFuelGet: (params = {}) =>
      this.request({
        path: `/api/insights/distribution/fuel`,
        method: "GET",
        format: "json",
        ...params,
      }),
    /**
     * No description
     *
     * @name GetTransmissionDistributionApiInsightsDistributionTransmissionGet
     * @summary Get Transmission Distribution
     * @request GET:/api/insights/distribution/transmission
     */
    getTransmissionDistributionApiInsightsDistributionTransmissionGet: (
      params = {},
    ) =>
      this.request({
        path: `/api/insights/distribution/transmission`,
        method: "GET",
        format: "json",
        ...params,
      }),
    /**
     * No description
     *
     * @name GetOpportunitiesApiInsightsOpportunitiesGet
     * @summary Get Opportunities
     * @request GET:/api/insights/opportunities
     */
    getOpportunitiesApiInsightsOpportunitiesGet: (params = {}) =>
      this.request({
        path: `/api/insights/opportunities`,
        method: "GET",
        format: "json",
        ...params,
      }),
    /**
     * No description
     *
     * @name GetModelsInsightApiInsightsModelsGet
     * @summary Get Models Insight
     * @request GET:/api/insights/models
     */
    getModelsInsightApiInsightsModelsGet: (params = {}) =>
      this.request({
        path: `/api/insights/models`,
        method: "GET",
        format: "json",
        ...params,
      }),
    /**
     * No description
     *
     * @name GetPriceRangesCrcApiInsightsPriceRangesCrcGet
     * @summary Get Price Ranges Crc
     * @request GET:/api/insights/price-ranges-crc
     */
    getPriceRangesCrcApiInsightsPriceRangesCrcGet: (params = {}) =>
      this.request({
        path: `/api/insights/price-ranges-crc`,
        method: "GET",
        format: "json",
        ...params,
      }),
    /**
     * No description
     *
     * @name GetMileageInsightApiInsightsMileageGet
     * @summary Get Mileage Insight
     * @request GET:/api/insights/mileage
     */
    getMileageInsightApiInsightsMileageGet: (params = {}) =>
      this.request({
        path: `/api/insights/mileage`,
        method: "GET",
        format: "json",
        ...params,
      }),
    /**
     * No description
     *
     * @name GetCuriositiesApiInsightsCuriositiesGet
     * @summary Get Curiosities
     * @request GET:/api/insights/curiosities
     */
    getCuriositiesApiInsightsCuriositiesGet: (params = {}) =>
      this.request({
        path: `/api/insights/curiosities`,
        method: "GET",
        format: "json",
        ...params,
      }),
    /**
     * No description
     *
     * @name GetExplorerDataApiInsightsExplorerGet
     * @summary Get Explorer Data
     * @request GET:/api/insights/explorer
     */
    getExplorerDataApiInsightsExplorerGet: (params = {}) =>
      this.request({
        path: `/api/insights/explorer`,
        method: "GET",
        format: "json",
        ...params,
      }),
    /**
     * No description
     *
     * @name GetMarketExtremesApiInsightsMarketExtremesGet
     * @summary Get Market Extremes
     * @request GET:/api/insights/market-extremes
     */
    getMarketExtremesApiInsightsMarketExtremesGet: (params = {}) =>
      this.request({
        path: `/api/insights/market-extremes`,
        method: "GET",
        format: "json",
        ...params,
      }),
    /**
     * No description
     *
     * @name GetModelsTransmissionsApiInsightsModelsTransmissionsGet
     * @summary Get Models Transmissions
     * @request GET:/api/insights/models/transmissions
     */
    getModelsTransmissionsApiInsightsModelsTransmissionsGet: (params = {}) =>
      this.request({
        path: `/api/insights/models/transmissions`,
        method: "GET",
        format: "json",
        ...params,
      }),
    /**
     * No description
     *
     * @name GetVerdictApiInsightsVerdictGet
     * @summary Get Verdict
     * @request GET:/api/insights/verdict
     */
    getVerdictApiInsightsVerdictGet: (query, params = {}) =>
      this.request({
        path: `/api/insights/verdict`,
        method: "GET",
        query: query,
        format: "json",
        ...params,
      }),
    /**
     * No description
     *
     * @name GetCarsV2ApiV2CarsGet
     * @summary Get Cars V2
     * @request GET:/api/v2/cars
     */
    getCarsV2ApiV2CarsGet: (query, params = {}) =>
      this.request({
        path: `/api/v2/cars`,
        method: "GET",
        query: query,
        format: "json",
        ...params,
      }),
  };
}
