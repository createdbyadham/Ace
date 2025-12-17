import apiClient from '@/infrastructure/api/client';
import type {
  QuestionSet,
  QuestionSetCreate,
  QuestionSetUpdate,
  QuestionSetWithQuestions,
  Question,
  QuestionCreate,
  QuestionUpdate,
  QuizStart,
  QuizSubmission,
  QuizResult,
  RevisionStart,
  MCQGenerationResponse,
} from '@/components/quiz/types';

export const quizApi = {
  // Question Set operations
  listQuestionSets: async (): Promise<QuestionSet[]> => {
    const { data } = await apiClient.get<QuestionSet[]>('/question-sets');
    return data;
  },

  getQuestionSet: async (setId: string): Promise<QuestionSetWithQuestions> => {
    const { data } = await apiClient.get<QuestionSetWithQuestions>(`/question-sets/${setId}`);
    return data;
  },

  createQuestionSet: async (payload: QuestionSetCreate): Promise<QuestionSet> => {
    const { data } = await apiClient.post<QuestionSet>('/question-sets', payload);
    return data;
  },

  updateQuestionSet: async (setId: string, payload: QuestionSetUpdate): Promise<QuestionSet> => {
    const { data } = await apiClient.patch<QuestionSet>(`/question-sets/${setId}`, payload);
    return data;
  },

  deleteQuestionSet: async (setId: string): Promise<void> => {
    await apiClient.delete(`/question-sets/${setId}`);
  },

  // Question operations
  getQuestion: async (questionId: string): Promise<Question> => {
    const { data } = await apiClient.get<Question>(`/questions/${questionId}`);
    return data;
  },

  createQuestion: async (setId: string, payload: QuestionCreate): Promise<Question> => {
    const { data } = await apiClient.post<Question>(`/question-sets/${setId}/questions`, payload);
    return data;
  },

  updateQuestion: async (questionId: string, payload: QuestionUpdate): Promise<Question> => {
    const { data } = await apiClient.patch<Question>(`/questions/${questionId}`, payload);
    return data;
  },

  deleteQuestion: async (questionId: string): Promise<void> => {
    await apiClient.delete(`/questions/${questionId}`);
  },

  // Quiz operations
  startQuiz: async (
    setId: string,
    options?: { time_limit_seconds?: number | null; shuffle?: boolean }
  ): Promise<QuizStart> => {
    const { data } = await apiClient.post<QuizStart>(`/question-sets/${setId}/quiz/start`, {
      time_limit_seconds: options?.time_limit_seconds ?? null,
      shuffle: options?.shuffle ?? true,
    });
    return data;
  },

  submitQuiz: async (
    setId: string,
    quizSessionId: string,
    submission: QuizSubmission
  ): Promise<QuizResult> => {
    const { data } = await apiClient.post<QuizResult>(`/question-sets/${setId}/quiz/submit`, {
      quiz_session_id: quizSessionId,
      submission,
    });
    return data;
  },

  startRevision: async (
    setId: string,
    originalQuizSessionId: string,
    wrongQuestionIds: string[],
    shuffle?: boolean
  ): Promise<RevisionStart> => {
    const { data } = await apiClient.post<RevisionStart>(`/question-sets/${setId}/quiz/revision`, {
      original_quiz_session_id: originalQuizSessionId,
      wrong_question_ids: wrongQuestionIds,
      shuffle: shuffle ?? true,
    });
    return data;
  },

  // AI Generation
  generateQuestions: async (
    files: File[],
    numQuestions: number,
    setTitle: string,
    setDescription?: string
  ): Promise<MCQGenerationResponse> => {
    const formData = new FormData();
    files.forEach((file) => formData.append('files', file));
    formData.append('num_questions', numQuestions.toString());
    formData.append('set_title', setTitle);
    if (setDescription) {
      formData.append('set_description', setDescription);
    }

    const { data } = await apiClient.post<MCQGenerationResponse>(
      '/agents/mcq',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return data;
  },
};

export default quizApi;

