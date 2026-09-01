import { apiGet } from './client'; import type { WeatherObservationResponse, WeatherForecastResponse } from './types';
export const fetchWeather=(latitude:number,longitude:number,signal?:AbortSignal)=>apiGet<WeatherObservationResponse>('/weather/latest',signal,{latitude,longitude});
export const fetchWeatherRisk=(signal?:AbortSignal)=>apiGet<Record<string,unknown>>('/weather/risk',signal);
export const fetchWeatherForecasts=(signal?:AbortSignal)=>apiGet<WeatherForecastResponse[]>('/weather/forecasts',signal);
