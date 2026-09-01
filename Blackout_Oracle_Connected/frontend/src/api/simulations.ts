import { apiGet,apiPost } from './client'; import type { SimulationCreate,SimulationResponse } from './types';
export const createSimulation=(payload:SimulationCreate)=>apiPost<SimulationResponse>('/simulations',payload);
export const runSimulationJob=(id:string)=>apiPost<SimulationResponse>(`/simulations/${encodeURIComponent(id)}/run`);
export const getSimulation=(id:string,signal?:AbortSignal)=>apiGet<SimulationResponse>(`/simulations/${encodeURIComponent(id)}`,signal);
export const getSimulationResult=(id:string,signal?:AbortSignal)=>apiGet<Record<string,unknown>>(`/simulations/${encodeURIComponent(id)}/result`,signal);
export const cancelSimulation=(id:string)=>apiPost<SimulationResponse>(`/simulations/${encodeURIComponent(id)}/cancel`);
export async function executeFullSimulationWorkflow(payload:SimulationCreate,onUpdate?:(s:SimulationResponse)=>void):Promise<{simulation:SimulationResponse;result:Record<string,unknown>|null}> { const created=await createSimulation(payload); onUpdate?.(created); let current=await runSimulationJob(created.id); onUpdate?.(current); while(current.status==='queued'||current.status==='running'){ await new Promise(r=>setTimeout(r,1200)); current=await getSimulation(created.id); onUpdate?.(current); } const result=current.status==='completed'?await getSimulationResult(created.id):null; return {simulation:current,result}; }
