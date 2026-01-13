export interface AnalysisResponse {
  extraction?: any;
  summary?: string;
  translation?: string;
  analysis?: string;
  recommendation?: string;
  // Optional per-agent outputs (keyed by agent name)
  agents?: Record<string, any>;
}