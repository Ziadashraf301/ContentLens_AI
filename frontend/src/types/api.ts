export interface AnalysisResponse {
  extraction?: any;
  summary?: string;
  translation?: string;
  analysis?: string;
  recommendation?: string;
  ideation?: string;
  copywriting?: string;
  compliance?: any;
  next_steps?: string[];
  current_step_index?: number;
  // Optional per-agent outputs (keyed by agent name)
  agents?: Record<string, any>;
  trace_id?: string;
}