import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { flashcardsApi } from '@/components/flashcards/api';
import type {
  DeckCreate,
  DeckUpdate,
  CardCreate,
  CardUpdate,
  StudyMode,
  ReviewIn,
  ReviewResponse,
  SnoozeIn,
} from '@/components/flashcards/types';

export const flashcardKeys = {
  all: ['flashcards'] as const,
  decks: () => [...flashcardKeys.all, 'decks'] as const,
  deck: (id: string) => [...flashcardKeys.decks(), id] as const,
  cards: (deckId?: string) => [...flashcardKeys.all, 'cards', { deckId }] as const,
  card: (id: string) => [...flashcardKeys.all, 'card', id] as const,
};

// Deck hooks
export function useDecks() {
  return useQuery({
    queryKey: flashcardKeys.decks(),
    queryFn: flashcardsApi.listDecks,
  });
}

export function useDeck(deckId: string) {
  return useQuery({
    queryKey: flashcardKeys.deck(deckId),
    queryFn: () => flashcardsApi.getDeck(deckId),
    enabled: !!deckId,
  });
}

export function useCreateDeck() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: DeckCreate) => flashcardsApi.createDeck(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: flashcardKeys.decks() });
    },
  });
}

export function useUpdateDeck() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ deckId, payload }: { deckId: string; payload: DeckUpdate }) =>
      flashcardsApi.updateDeck(deckId, payload),
    onSuccess: (_, { deckId }) => {
      queryClient.invalidateQueries({ queryKey: flashcardKeys.decks() });
      queryClient.invalidateQueries({ queryKey: flashcardKeys.deck(deckId) });
    },
  });
}

export function useDeleteDeck() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (deckId: string) => flashcardsApi.deleteDeck(deckId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: flashcardKeys.decks() });
    },
  });
}

// Card hooks
export function useCards(deckId?: string) {
  return useQuery({
    queryKey: flashcardKeys.cards(deckId),
    queryFn: () => flashcardsApi.listCards(deckId),
  });
}

export function useCard(cardId: string) {
  return useQuery({
    queryKey: flashcardKeys.card(cardId),
    queryFn: () => flashcardsApi.getCard(cardId),
    enabled: !!cardId,
  });
}

export function useCreateCard() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: CardCreate) => flashcardsApi.createCard(payload),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: flashcardKeys.cards(data.deck_id || undefined) });
      queryClient.invalidateQueries({ queryKey: flashcardKeys.cards() });
    },
  });
}

export function useUpdateCard() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ cardId, payload }: { cardId: string; payload: CardUpdate }) =>
      flashcardsApi.updateCard(cardId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: flashcardKeys.all });
    },
  });
}

export function useDeleteCard() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (cardId: string) => flashcardsApi.deleteCard(cardId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: flashcardKeys.all });
    },
  });
}

// AI Generation hook
export function useGenerateFlashcards() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      files,
      numCards,
      deckTitle,
      deckDescription,
      model = 'openai',
    }: {
      files: File[];
      numCards: number;
      deckTitle: string;
      deckDescription?: string;
      model?: 'openai' | 'ace';
    }) => flashcardsApi.generateFlashcards(files, numCards, deckTitle, deckDescription, model),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: flashcardKeys.decks() });
      queryClient.invalidateQueries({ queryKey: flashcardKeys.cards() });
    },
  });
}

// Hook to get available models
export function useAvailableModels() {
  return useQuery({
    queryKey: ['agents', 'models'],
    queryFn: flashcardsApi.getAvailableModels,
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
  });
}

// ============================================
// Enhanced hooks with toast notifications
// ============================================

interface MutationCallbacks {
  onSuccess?: () => void;
  onError?: () => void;
}

export function useDeckMutations() {
  const createDeckMutation = useCreateDeck();
  const updateDeckMutation = useUpdateDeck();
  const deleteDeckMutation = useDeleteDeck();

  const createDeck = async (data: DeckCreate, callbacks?: MutationCallbacks) => {
    try {
      await createDeckMutation.mutateAsync(data);
      toast.success('Deck created successfully');
      callbacks?.onSuccess?.();
    } catch (error: any) {
      toast.error('Failed to create deck', {
        description: error?.response?.data?.detail || 'Please try again.',
      });
      callbacks?.onError?.();
    }
  };

  const updateDeck = async (deckId: string, data: DeckUpdate, callbacks?: MutationCallbacks) => {
    try {
      await updateDeckMutation.mutateAsync({ deckId, payload: data });
      toast.success('Deck updated successfully');
      callbacks?.onSuccess?.();
    } catch (error: any) {
      toast.error('Failed to update deck', {
        description: error?.response?.data?.detail || 'Please try again.',
      });
      callbacks?.onError?.();
    }
  };

  const deleteDeck = async (deckId: string, callbacks?: MutationCallbacks) => {
    try {
      await deleteDeckMutation.mutateAsync(deckId);
      toast.success('Deck deleted successfully');
      callbacks?.onSuccess?.();
    } catch (error: any) {
      toast.error('Failed to delete deck', {
        description: error?.response?.data?.detail || 'Please try again.',
      });
      callbacks?.onError?.();
    }
  };

  return {
    createDeck,
    updateDeck,
    deleteDeck,
    isCreating: createDeckMutation.isPending,
    isUpdating: updateDeckMutation.isPending,
    isDeleting: deleteDeckMutation.isPending,
  };
}

export function useCardMutations() {
  const createCardMutation = useCreateCard();
  const updateCardMutation = useUpdateCard();
  const deleteCardMutation = useDeleteCard();

  const createCard = async (data: CardCreate, callbacks?: MutationCallbacks) => {
    try {
      await createCardMutation.mutateAsync(data);
      toast.success('Card created successfully');
      callbacks?.onSuccess?.();
    } catch (error: any) {
      toast.error('Failed to create card', {
        description: error?.response?.data?.detail || 'Please try again.',
      });
      callbacks?.onError?.();
    }
  };

  const updateCard = async (cardId: string, data: CardCreate, callbacks?: MutationCallbacks) => {
    try {
      await updateCardMutation.mutateAsync({ cardId, payload: data });
      toast.success('Card updated successfully');
      callbacks?.onSuccess?.();
    } catch (error: any) {
      toast.error('Failed to update card', {
        description: error?.response?.data?.detail || 'Please try again.',
      });
      callbacks?.onError?.();
    }
  };

  const deleteCard = async (cardId: string, callbacks?: MutationCallbacks) => {
    try {
      await deleteCardMutation.mutateAsync(cardId);
      toast.success('Card deleted successfully');
      callbacks?.onSuccess?.();
    } catch (error: any) {
      toast.error('Failed to delete card', {
        description: error?.response?.data?.detail || 'Please try again.',
      });
      callbacks?.onError?.();
    }
  };

  return {
    createCard,
    updateCard,
    deleteCard,
    isCreating: createCardMutation.isPending,
    isUpdating: updateCardMutation.isPending,
    isDeleting: deleteCardMutation.isPending,
  };
}

export function useAIGeneration() {
  const generateMutation = useGenerateFlashcards();

  const generateFlashcards = async (
    params: {
      files: File[];
      numCards: number;
      deckTitle: string;
      deckDescription?: string;
      model?: 'openai' | 'ace';
    },
    callbacks?: MutationCallbacks
  ) => {
    try {
      const result = await generateMutation.mutateAsync(params);
      const modelName = params.model === 'ace' ? 'Ace' : 'ChatGPT';
      toast.success(`Generated ${result.cards_created} flashcards!`, {
        description: `Deck "${result.deck_title}" created using ${modelName}.`,
      });
      callbacks?.onSuccess?.();
      return result;
    } catch (error: any) {
      toast.error('Failed to generate flashcards', {
        description: error?.response?.data?.detail || 'Please try again.',
      });
      callbacks?.onError?.();
      throw error;
    }
  };

  return {
    generateFlashcards,
    isGenerating: generateMutation.isPending,
  };
}

// ============================================
// Study/Review hooks
// ============================================

export const studyKeys = {
  all: ['study'] as const,
  deckStats: (deckId: string) => [...studyKeys.all, 'stats', deckId] as const,
  studySession: (deckId: string, mode: StudyMode) =>
    [...studyKeys.all, 'session', deckId, mode] as const,
};

export function useDeckStats(deckId: string | undefined) {
  return useQuery({
    queryKey: studyKeys.deckStats(deckId || ''),
    queryFn: () => flashcardsApi.getDeckStats(deckId!),
    enabled: !!deckId,
  });
}

export function useStudySession(
  deckId: string | undefined,
  mode: StudyMode = 'review',
  limit: number = 20
) {
  return useQuery({
    queryKey: studyKeys.studySession(deckId || '', mode),
    queryFn: () => flashcardsApi.getStudySession(deckId!, mode, limit),
    enabled: !!deckId,
  });
}

export function useSubmitReview() {
  // Don't invalidate queries on each review - the session uses local state
  // Stats will be refreshed when the session ends
  return useMutation({
    mutationFn: (payload: ReviewIn) => flashcardsApi.submitReview(payload),
  });
}

export function useSnoozeCard() {
  return useMutation({
    mutationFn: (payload: SnoozeIn) => flashcardsApi.snoozeCard(payload),
  });
}

export function useInvalidateStudyQueries() {
  const queryClient = useQueryClient();
  
  return () => {
    queryClient.invalidateQueries({ queryKey: studyKeys.all });
  };
}

export function useStudyMutations() {
  const submitReviewMutation = useSubmitReview();
  const snoozeCardMutation = useSnoozeCard();
  const invalidateStudyQueries = useInvalidateStudyQueries();

  const submitReview = async (
    cardId: string,
    response: ReviewResponse,
    mode: StudyMode,
    callbacks?: MutationCallbacks
  ) => {
    try {
      const result = await submitReviewMutation.mutateAsync({
        card_id: cardId,
        response,
        mode,
      });

      // Show XP earned if any
      if (result.xp_earned > 0) {
        toast.success(`+${result.xp_earned} XP`, {
          description: result.streak_updated
            ? `🔥 Streak: ${result.streak} days!`
            : undefined,
          duration: 2000,
        });
      }

      callbacks?.onSuccess?.();
      return result;
    } catch (error: any) {
      toast.error('Failed to submit review', {
        description: error?.response?.data?.detail || 'Please try again.',
      });
      callbacks?.onError?.();
      throw error;
    }
  };

  const snoozeCard = async (
    cardId: string,
    hours: number = 24,
    callbacks?: MutationCallbacks
  ) => {
    try {
      const result = await snoozeCardMutation.mutateAsync({
        card_id: cardId,
        hours,
      });
      
      const nextReview = new Date(result.next_review_at);
      toast.success(`Card snoozed for ${hours} hour${hours !== 1 ? 's' : ''}`, {
        description: `Next review: ${nextReview.toLocaleString()}`,
        duration: 3000,
      });

      callbacks?.onSuccess?.();
      return result;
    } catch (error: any) {
      toast.error('Failed to snooze card', {
        description: error?.response?.data?.detail || 'Please try again.',
      });
      callbacks?.onError?.();
      throw error;
    }
  };

  return {
    submitReview,
    snoozeCard,
    isSubmitting: submitReviewMutation.isPending,
    isSnoozeing: snoozeCardMutation.isPending,
    invalidateStudyQueries,
  };
}
