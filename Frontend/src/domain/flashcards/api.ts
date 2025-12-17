import apiClient from '@/infrastructure/api/client';
import type {
  Deck,
  DeckCreate,
  DeckUpdate,
  Card,
  CardCreate,
  CardUpdate,
  FlashcardGenerationResponse,
  DeckStats,
  StudySession,
  StudyMode,
  ReviewIn,
  ReviewOut,
} from './types';

export const flashcardsApi = {
  // Deck operations
  listDecks: async (): Promise<Array<Deck>> => {
    const { data } = await apiClient.get<Array<Deck>>('/flashcards/decks');
    return data;
  },

  getDeck: async (deckId: string): Promise<Deck> => {
    const { data } = await apiClient.get<Deck>(`/flashcards/decks/${deckId}`);
    return data;
  },

  createDeck: async (payload: DeckCreate): Promise<Deck> => {
    const { data } = await apiClient.post<Deck>('/flashcards/decks', payload);
    return data;
  },

  updateDeck: async (deckId: string, payload: DeckUpdate): Promise<Deck> => {
    const { data } = await apiClient.patch<Deck>(`/flashcards/decks/${deckId}`, payload);
    return data;
  },

  deleteDeck: async (deckId: string): Promise<void> => {
    await apiClient.delete(`/flashcards/decks/${deckId}`);
  },

  // Card operations
  listCards: async (deckId?: string): Promise<Array<Card>> => {
    const params = deckId ? { deck_id: deckId } : {};
    const { data } = await apiClient.get<Array<Card>>('/flashcards/cards', { params });
    return data;
  },

  getCard: async (cardId: string): Promise<Card> => {
    const { data } = await apiClient.get<Card>(`/flashcards/cards/${cardId}`);
    return data;
  },

  createCard: async (payload: CardCreate): Promise<Card> => {
    const { data } = await apiClient.post<Card>('/flashcards/cards', payload);
    return data;
  },

  updateCard: async (cardId: string, payload: CardUpdate): Promise<Card> => {
    const { data } = await apiClient.patch<Card>(`/flashcards/cards/${cardId}`, payload);
    return data;
  },

  deleteCard: async (cardId: string): Promise<void> => {
    await apiClient.delete(`/flashcards/cards/${cardId}`);
  },

  // AI Generation
  generateFlashcards: async (
    files: Array<File>,
    numCards: number,
    deckTitle: string,
    deckDescription?: string
  ): Promise<FlashcardGenerationResponse> => {
    const formData = new FormData();
    files.forEach((file) => formData.append('files', file));
    formData.append('num_cards', numCards.toString());
    formData.append('deck_title', deckTitle);
    if (deckDescription) {
      formData.append('deck_description', deckDescription);
    }

    const { data } = await apiClient.post<FlashcardGenerationResponse>(
      '/agents/flashcards',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return data;
  },

  // ===========================================
  // Study/Review Operations
  // ===========================================

  getDeckStats: async (deckId: string): Promise<DeckStats> => {
    const { data } = await apiClient.get<DeckStats>(`/decks/${deckId}/stats`);
    return data;
  },

  getStudySession: async (
    deckId: string,
    mode: StudyMode = 'review',
    limit: number = 20
  ): Promise<StudySession> => {
    const { data } = await apiClient.get<StudySession>(`/decks/${deckId}/study`, {
      params: { mode, limit },
    });
    return data;
  },

  submitReview: async (payload: ReviewIn): Promise<ReviewOut> => {
    const { data } = await apiClient.post<ReviewOut>('/review', payload);
    return data;
  },
};

export default flashcardsApi;

