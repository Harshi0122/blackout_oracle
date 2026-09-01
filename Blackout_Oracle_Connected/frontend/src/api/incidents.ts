import { apiGet,apiPost } from './client'; import type { IncidentResponse,IncidentResolveRequest } from './types';
export const fetchIncidents=(signal?:AbortSignal)=>apiGet<IncidentResponse[]>('/incidents',signal);
export const resolveIncident=(id:string,payload:IncidentResolveRequest)=>apiPost<IncidentResponse>(`/incidents/${encodeURIComponent(id)}/resolve`,payload);
export const markIncidentFalsePositive=(id:string)=>apiPost<IncidentResponse>(`/incidents/${encodeURIComponent(id)}/false-positive`);
