import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { quizApi } from '@/components/quiz/api';
import type {
  QuestionSetCreate,
  QuestionSetUpdate,
  QuestionCreate,
  QuestionUpdate,
  QuizSubmission,
} from '@/components/quiz/types';

export const quizKeys = {
  all: ['quiz'] as const,
  questionSets: () => [...quizKeys.all, 'sets'] as const,
  questionSet: (id: string) => [...quizKeys.questionSets(), id] as const,
  question: (id: string) => [...quizKeys.all, 'question', id] as const,
};

// =============================================================================
// Question Set Hooks
// =============================================================================

export function useQuestionSets() {
  return useQuery({
    queryKey: quizKeys.questionSets(),
    queryFn: quizApi.listQuestionSets,
  });
}

export function useQuestionSet(setId: string | undefined) {
  return useQuery({
    queryKey: quizKeys.questionSet(setId || ''),
    queryFn: () => quizApi.getQuestionSet(setId!),
    enabled: !!setId,
  });
}

export function useCreateQuestionSet() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: QuestionSetCreate) => quizApi.createQuestionSet(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: quizKeys.questionSets() });
    },
  });
}

export function useUpdateQuestionSet() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ setId, payload }: { setId: string; payload: QuestionSetUpdate }) =>
      quizApi.updateQuestionSet(setId, payload),
    onSuccess: (_, { setId }) => {
      queryClient.invalidateQueries({ queryKey: quizKeys.questionSets() });
      queryClient.invalidateQueries({ queryKey: quizKeys.questionSet(setId) });
    },
  });
}

export function useDeleteQuestionSet() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (setId: string) => quizApi.deleteQuestionSet(setId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: quizKeys.questionSets() });
    },
  });
}

// =============================================================================
// Question Hooks
// =============================================================================

export function useCreateQuestion() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ setId, payload }: { setId: string; payload: QuestionCreate }) =>
      quizApi.createQuestion(setId, payload),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: quizKeys.questionSet(data.set_id) });
      queryClient.invalidateQueries({ queryKey: quizKeys.questionSets() });
    },
  });
}

export function useUpdateQuestion() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ questionId, payload }: { questionId: string; payload: QuestionUpdate }) =>
      quizApi.updateQuestion(questionId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: quizKeys.all });
    },
  });
}

export function useDeleteQuestion() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (questionId: string) => quizApi.deleteQuestion(questionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: quizKeys.all });
    },
  });
}

// =============================================================================
// Quiz Session Hooks
// =============================================================================

export function useStartQuiz() {
  return useMutation({
    mutationFn: ({
      setId,
      options,
    }: {
      setId: string;
      options?: { time_limit_seconds?: number | null; shuffle?: boolean };
    }) => quizApi.startQuiz(setId, options),
  });
}

export function useSubmitQuiz() {
  return useMutation({
    mutationFn: ({
      setId,
      quizSessionId,
      submission,
    }: {
      setId: string;
      quizSessionId: string;
      submission: QuizSubmission;
    }) => quizApi.submitQuiz(setId, quizSessionId, submission),
  });
}

export function useStartRevision() {
  return useMutation({
    mutationFn: ({
      setId,
      originalQuizSessionId,
      wrongQuestionIds,
      shuffle,
    }: {
      setId: string;
      originalQuizSessionId: string;
      wrongQuestionIds: string[];
      shuffle?: boolean;
    }) => quizApi.startRevision(setId, originalQuizSessionId, wrongQuestionIds, shuffle),
  });
}

// =============================================================================
// Enhanced Hooks with Toast Notifications
// =============================================================================

interface MutationCallbacks {
  onSuccess?: () => void;
  onError?: () => void;
}

export function useQuestionSetMutations() {
  const createMutation = useCreateQuestionSet();
  const updateMutation = useUpdateQuestionSet();
  const deleteMutation = useDeleteQuestionSet();

  const createQuestionSet = async (data: QuestionSetCreate, callbacks?: MutationCallbacks) => {
    try {
      await createMutation.mutateAsync(data);
      toast.success('Question set created successfully');
      callbacks?.onSuccess?.();
    } catch (error: any) {
      toast.error('Failed to create question set', {
        description: error?.response?.data?.detail || 'Please try again.',
      });
      callbacks?.onError?.();
    }
  };

  const updateQuestionSet = async (
    setId: string,
    data: QuestionSetUpdate,
    callbacks?: MutationCallbacks
  ) => {
    try {
      await updateMutation.mutateAsync({ setId, payload: data });
      toast.success('Question set updated successfully');
      callbacks?.onSuccess?.();
    } catch (error: any) {
      toast.error('Failed to update question set', {
        description: error?.response?.data?.detail || 'Please try again.',
      });
      callbacks?.onError?.();
    }
  };

  const deleteQuestionSet = async (setId: string, callbacks?: MutationCallbacks) => {
    try {
      await deleteMutation.mutateAsync(setId);
      toast.success('Question set deleted successfully');
      callbacks?.onSuccess?.();
    } catch (error: any) {
      toast.error('Failed to delete question set', {
        description: error?.response?.data?.detail || 'Please try again.',
      });
      callbacks?.onError?.();
    }
  };

  return {
    createQuestionSet,
    updateQuestionSet,
    deleteQuestionSet,
    isCreating: createMutation.isPending,
    isUpdating: updateMutation.isPending,
    isDeleting: deleteMutation.isPending,
  };
}

export function useQuestionMutations() {
  const createMutation = useCreateQuestion();
  const updateMutation = useUpdateQuestion();
  const deleteMutation = useDeleteQuestion();

  const createQuestion = async (
    setId: string,
    data: QuestionCreate,
    callbacks?: MutationCallbacks
  ) => {
    try {
      await createMutation.mutateAsync({ setId, payload: data });
      toast.success('Question created successfully');
      callbacks?.onSuccess?.();
    } catch (error: any) {
      toast.error('Failed to create question', {
        description: error?.response?.data?.detail || 'Please try again.',
      });
      callbacks?.onError?.();
    }
  };

  const updateQuestion = async (
    questionId: string,
    data: QuestionUpdate,
    callbacks?: MutationCallbacks
  ) => {
    try {
      await updateMutation.mutateAsync({ questionId, payload: data });
      toast.success('Question updated successfully');
      callbacks?.onSuccess?.();
    } catch (error: any) {
      toast.error('Failed to update question', {
        description: error?.response?.data?.detail || 'Please try again.',
      });
      callbacks?.onError?.();
    }
  };

  const deleteQuestion = async (questionId: string, callbacks?: MutationCallbacks) => {
    try {
      await deleteMutation.mutateAsync(questionId);
      toast.success('Question deleted successfully');
      callbacks?.onSuccess?.();
    } catch (error: any) {
      toast.error('Failed to delete question', {
        description: error?.response?.data?.detail || 'Please try again.',
      });
      callbacks?.onError?.();
    }
  };

  return {
    createQuestion,
    updateQuestion,
    deleteQuestion,
    isCreating: createMutation.isPending,
    isUpdating: updateMutation.isPending,
    isDeleting: deleteMutation.isPending,
  };
}

export function useQuizMutations() {
  const startMutation = useStartQuiz();
  const submitMutation = useSubmitQuiz();
  const revisionMutation = useStartRevision();

  const startQuiz = async (
    setId: string,
    options?: { time_limit_seconds?: number | null; shuffle?: boolean },
    callbacks?: MutationCallbacks
  ) => {
    try {
      const result = await startMutation.mutateAsync({ setId, options });
      callbacks?.onSuccess?.();
      return result;
    } catch (error: any) {
      toast.error('Failed to start quiz', {
        description: error?.response?.data?.detail || 'Please try again.',
      });
      callbacks?.onError?.();
      throw error;
    }
  };

  const submitQuiz = async (
    setId: string,
    quizSessionId: string,
    submission: QuizSubmission,
    callbacks?: MutationCallbacks
  ) => {
    try {
      const result = await submitMutation.mutateAsync({ setId, quizSessionId, submission });
      callbacks?.onSuccess?.();
      return result;
    } catch (error: any) {
      const detail = error?.response?.data?.detail;
      // Handle both string and array error details
      const description = typeof detail === 'string' 
        ? detail 
        : Array.isArray(detail) 
          ? detail[0]?.msg || 'Validation error' 
          : 'Please try again.';
      toast.error('Failed to submit quiz', { description });
      callbacks?.onError?.();
      throw error;
    }
  };

  const startRevision = async (
    setId: string,
    originalQuizSessionId: string,
    wrongQuestionIds: string[],
    shuffle?: boolean,
    callbacks?: MutationCallbacks
  ) => {
    try {
      const result = await revisionMutation.mutateAsync({
        setId,
        originalQuizSessionId,
        wrongQuestionIds,
        shuffle,
      });
      toast.success('Revision started', {
        description: `Reviewing ${wrongQuestionIds.length} question${wrongQuestionIds.length !== 1 ? 's' : ''}`,
      });
      callbacks?.onSuccess?.();
      return result;
    } catch (error: any) {
      toast.error('Failed to start revision', {
        description: error?.response?.data?.detail || 'Please try again.',
      });
      callbacks?.onError?.();
      throw error;
    }
  };

  return {
    startQuiz,
    submitQuiz,
    startRevision,
    isStarting: startMutation.isPending,
    isSubmitting: submitMutation.isPending,
    isStartingRevision: revisionMutation.isPending,
  };
}

// =============================================================================
// AI Generation Hooks
// =============================================================================

export function useGenerateQuestions() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      files,
      numQuestions,
      setTitle,
      setDescription,
    }: {
      files: File[];
      numQuestions: number;
      setTitle: string;
      setDescription?: string;
    }) => quizApi.generateQuestions(files, numQuestions, setTitle, setDescription),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: quizKeys.questionSets() });
    },
  });
}

export function useAIGeneration() {
  const generateMutation = useGenerateQuestions();

  const generateQuestions = async (
    params: {
      files: File[];
      numQuestions: number;
      setTitle: string;
      setDescription?: string;
    },
    callbacks?: MutationCallbacks
  ) => {
    try {
      const result = await generateMutation.mutateAsync(params);
      toast.success(`Generated ${result.questions_created} questions!`, {
        description: `Question set "${result.set_title}" created successfully.`,
      });
      callbacks?.onSuccess?.();
      return result;
    } catch (error: any) {
      toast.error('Failed to generate questions', {
        description: error?.response?.data?.detail || 'Please try again.',
      });
      callbacks?.onError?.();
      throw error;
    }
  };

  return {
    generateQuestions,
    isGenerating: generateMutation.isPending,
  };
}

