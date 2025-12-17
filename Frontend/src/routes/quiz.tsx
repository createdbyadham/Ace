import { createFileRoute } from '@tanstack/react-router';
import QuizPage from '@/components/quiz/components/quiz';

export const Route = createFileRoute('/quiz')({
  component: QuizPage,
});
