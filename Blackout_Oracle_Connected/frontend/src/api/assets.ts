import { apiGet } from './client'; import type { AssetResponse } from './types';
export const fetchAssets=(signal?:AbortSignal)=>apiGet<AssetResponse[]>('/assets',signal);
export const fetchAsset=(id:string,signal?:AbortSignal)=>apiGet<AssetResponse>(`/assets/${encodeURIComponent(id)}`,signal);
export const fetchAssetStatus=(id:string,signal?:AbortSignal)=>apiGet(`/assets/${encodeURIComponent(id)}/status`,signal);
export const fetchAssetTelemetry=(id:string,signal?:AbortSignal)=>apiGet(`/assets/${encodeURIComponent(id)}/telemetry`,signal);
