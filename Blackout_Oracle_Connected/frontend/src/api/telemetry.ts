import { apiGet } from './client'; import type { TelemetrySummary,TelemetryHealthResponse,TelemetryLatestResponse,TelemetryPointResponse } from './types';
export const fetchTelemetrySummary=(signal?:AbortSignal)=>apiGet<TelemetrySummary>('/telemetry/summary',signal);
export const fetchTelemetryHealth=(signal?:AbortSignal)=>apiGet<TelemetryHealthResponse>('/telemetry/health',signal);
export const fetchLatestTelemetry=(assetId:string,signal?:AbortSignal)=>apiGet<TelemetryLatestResponse>(`/telemetry/latest/${encodeURIComponent(assetId)}`,signal);
export const fetchTelemetry=(signal?:AbortSignal)=>apiGet<TelemetryPointResponse[]>('/telemetry',signal);
