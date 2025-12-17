// Question Set types
export interface QuestionSet {
  set_id: string;
  owner_id: string;
  title: string;
  description: string | null;
  tags: string[];
  created_at: string;
  questions_count: number;
}

export interface QuestionSetCreate {
  title: string;
  description?: string | null;
  tags?: string[];
}

export interface QuestionSetUpdate {
  title?: string;
  description?: string | null;
  tags?: string[];
}

// Question types
export interface Question {
  question_id: string;
  set_id: string;
  owner_id: string;
  question_text: string;
  options: string[];
  correct_answer: number;
  explanation: string | null;
  source_file: string | null;
  created_at: string;
}

export interface QuestionCreate {
  question_text: string;
  options: string[];
  correct_answer: number;
  explanation?: string | null;
  source_file?: string | null;
}

export interface QuestionUpdate {
  question_text?: string;
  options?: string[];
  correct_answer?: number;
  explanation?: string | null;
}

export interface QuestionSetWithQuestions extends Omit<QuestionSet, 'questions_count'> {
  questions: Question[];
}

// Quiz Session types
export interface QuizQuestion {
  question_id: string;
  question_text: string;
  options: string[];
}

export interface QuizStart {
  quiz_session_id: string;
  set_id: string;
  title: string;
  questions: QuizQuestion[];
  time_limit_seconds: number | null;
}

export interface QuestionAnswer {
  question_id: string;
  selected_answer: number;
}

export interface QuizSubmission {
  answers: QuestionAnswer[];
  time_taken_seconds?: number | null;
}

export interface QuestionResult {
  question_id: string;
  question_text: string;
  options: string[];
  correct_answer: number;
  user_answer: number;
  is_correct: boolean;
  explanation: string | null;
}

export interface QuizResult {
  quiz_session_id: string;
  set_id: string;
  title: string;
  total_questions: number;
  correct_count: number;
  wrong_count: number;
  percentage: number;
  time_taken_seconds: number | null;
  results: QuestionResult[];
  wrong_question_ids: string[];
}

export interface RevisionStart {
  revision_session_id: string;
  set_id: string;
  title: string;
  original_quiz_session_id: string;
  questions: QuizQuestion[];
}

// AI Generation types
export interface GeneratedMCQ {
  question_text: string;
  options: string[];
  correct_answer: number;
  explanation: string;
  source_file: string;
}

export interface MCQGenerationResponse {
  set_id: string;
  set_title: string;
  questions_created: number;
  questions: GeneratedMCQ[];
  source_files: string[];
}

