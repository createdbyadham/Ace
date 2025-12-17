import { createFileRoute } from '@tanstack/react-router';
import FlashcardsPage from '@/components/flashcards/components/flashcards';

export const Route = createFileRoute('/flashcards')({
  component: FlashcardsPage,
});
