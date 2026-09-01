import { apiGet } from './client';
import { fetchAssets } from './assets';
import { fetchAlerts } from './alerts';
import { fetchLatestRisk, fetchRiskSummary } from './risk';
import { fetchWeather, fetchWeatherRisk } from './weather';
import { fetchTelemetrySummary } from './telemetry';
import { fetchRecommendations } from './recommendations';
import { fetchIncidents } from './incidents';

export async function getOracleSnapshot(
  location: { latitude: number; longitude: number },
  signal?: AbortSignal,
) {
  const requests = [
    apiGet<Record<string, unknown>>('/health', signal),
    fetchAssets(signal),
    fetchAlerts(signal),
    fetchLatestRisk(signal),
    fetchRiskSummary(signal),
    fetchWeather(location.latitude, location.longitude, signal),
    fetchWeatherRisk(signal),
    fetchTelemetrySummary(signal),
    fetchRecommendations(signal),
    fetchIncidents(signal),
  ];

  const settled = await Promise.allSettled(requests);
  const value = <T>(index: number, fallback: T): T =>
    settled[index].status === 'fulfilled'
      ? (settled[index] as PromiseFulfilledResult<T>).value
      : fallback;

  return {
    health: value(0, { status: 'offline' }),
    assets: value(1, []),
    alerts: value(2, []),
    riskLatest: value(3, null),
    riskSummary: value(4, null),
    weather: value(5, null),
    weatherRisk: value(6, null),
    telemetry: value(7, {}),
    recommendations: value(8, []),
    incidents: value(9, []),
    failed: settled.filter((item) => item.status === 'rejected').length,
    errors: settled.map((item, index) => item.status === 'rejected'
      ? { index, reason: item.reason instanceof Error ? item.reason.message : String(item.reason) }
      : null).filter(Boolean),
  };
}
