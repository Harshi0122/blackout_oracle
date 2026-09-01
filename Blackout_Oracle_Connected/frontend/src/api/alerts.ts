import { apiGet,apiPost } from './client'; import type { AlertResponse,AlertAcknowledgeRequest,AlertResolveRequest } from './types';
export const fetchAlerts=(signal?:AbortSignal)=>apiGet<AlertResponse[]>('/alerts',signal);
export const acknowledgeAlert=(id:string,payload:AlertAcknowledgeRequest)=>apiPost<AlertResponse>(`/alerts/${encodeURIComponent(id)}/acknowledge`,payload);
export const resolveAlert=(id:string,payload:AlertResolveRequest)=>apiPost<AlertResponse>(`/alerts/${encodeURIComponent(id)}/resolve`,payload);
export const dismissAlert=(id:string)=>apiPost<AlertResponse>(`/alerts/${encodeURIComponent(id)}/dismiss`);
