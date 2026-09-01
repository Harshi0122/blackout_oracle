import { apiGet,apiPost } from './client'; import type { RiskAssessmentRequest,RiskAssessmentResponse,RiskSummaryResponse,RiskFactor } from './types';
export const fetchLatestRisk=(signal?:AbortSignal)=>apiGet<RiskAssessmentResponse>('/risk/latest',signal);
export const fetchRiskSummary=(signal?:AbortSignal)=>apiGet<RiskSummaryResponse>('/risk/summary',signal);
export const fetchRiskFactors=(signal?:AbortSignal)=>apiGet<RiskFactor[]>('/risk/factors',signal);
export const assessRisk=(payload:RiskAssessmentRequest,signal?:AbortSignal)=>apiPost<RiskAssessmentResponse>('/risk/assess',payload,signal);
