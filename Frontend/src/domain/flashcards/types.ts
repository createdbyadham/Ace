// Deck types
export interface Deck {
  deck_id: string;
  owner_id: string;
  title: string;
  description: string | null;
  tags: string[];
  language: string | null;
  created_at: string;
  updated_at: string | null;
}

export interface DeckCreate {
  title: string;
  description?: string | null;
  tags?: string[];
  language?: string | null;
}

export interface DeckUpdate {
  title?: string;
  description?: string | null;
  tags?: string[];
  language?: string | null;
}

// Card content (nested structure)
export interface CardContent {
  front: string;
  back: string | null;
  cloze?: Array<string> | null;
  hints?: Array<string> | null;
}

// Card types
export interface Card {
  card_id: string;
  deck_id: string | null;
  owner_id: string;
  content: CardContent;
  created_at: string;
}

export interface CardCreate {
  deck_id?: string;
  content: CardContent;
}

export interface CardUpdate {
  deck_id?: string | null;
  content?: CardContent;
}

// AI Generation types
export interface GeneratedFlashcard {
  front: string;
  back: string;
  source_file: string;
}

export interface FlashcardGenerationResponse {
  deck_id: string;
  deck_title: string;
  cards_created: number;
  cards: Array<GeneratedFlashcard>;
  source_files: Array<string>;
}

// UI State types
export interface FlashcardStudyState {
  currentIndex: number;
  isFlipped: boolean;
  cards: Array<Card>;
}

// ===========================================
// Study/Review Types (from backend SR system)
// ===========================================

export interface DeckStats {
  deck_id: string;
  total_cards: number;
  due_now: number;
  due_today: number;
  mastered: number;
  learning: number;
  new: number;
}

export interface StudyCard {
  card_id: string;
  deck_id: string | null;
  content: CardContent;
  next_review_at: string;
  repetition: number;
  interval_days: number;
  ef: number;
}

export interface StudySession {
  cards: StudyCard[];
  due_count: number;
  total_count: number;
  mode: 'review' | 'all';
}

export type ReviewResponse = 'forgot' | 'meh' | 'got_it';
export type StudyMode = 'review' | 'all';

export interface ReviewIn {
  card_id: string;
  response: ReviewResponse;
  mode: StudyMode;
  elapsed_ms?: number;
}

export interface ReviewOut {
  card_id: string;
  repetition: number;
  interval_days: number;
  ef: number;
  next_review_at: string;
  quality: number;
  xp_earned: number;
  streak: number;
  streak_updated: boolean;
}
