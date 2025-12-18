// Summary types
export interface Summary {
  summary_id: string;
  owner_id: string;
  title: string;
  content: string;
  key_points: string[];
  source_files: string[];
  word_count: number;
  created_at: string;
  updated_at: string | null;
}

export interface SummaryListResponse {
  summaries: Summary[];
  total: number;
}

export interface SummaryUpdate {
  title?: string;
  content?: string;
}

// AI Generation types
export type SummaryLength = 'brief' | 'medium' | 'detailed';

export interface SummaryGenerationResponse {
  summary_id: string;
  title: string;
  content: string;
  key_points: string[];
  source_files: string[];
  word_count: number;
}

// UI state types
export interface SummaryViewState {
  selectedSummary: Summary | null;
  isGenerating: boolean;
  searchQuery: string;
}

