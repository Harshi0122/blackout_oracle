import { apiGet,apiPost } from './client'; import type { RecommendationResponse,RecommendationReviewRequest } from './types';
export const fetchRecommendations=(signal?:AbortSignal)=>apiGet<RecommendationResponse[]>('/recommendations',signal);
export const approveRecommendation=(id:string,payload:RecommendationReviewRequest)=>apiPost<RecommendationResponse>(`/recommendations/${encodeURIComponent(id)}/approve`,payload);
export const rejectRecommendation=(id:string,payload:RecommendationReviewRequest)=>apiPost<RecommendationResponse>(`/recommendations/${encodeURIComponent(id)}/reject`,payload);
export const markRecommendationExecuted=(id:string,payload:RecommendationReviewRequest)=>apiPost<RecommendationResponse>(`/recommendations/${encodeURIComponent(id)}/executed`,payload);
