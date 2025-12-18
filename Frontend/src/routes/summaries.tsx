import { createFileRoute } from '@tanstack/react-router';
import SummariesPage from '@/components/summaries/components/summaries';

export const Route = createFileRoute('/summaries')({
  component: SummariesPage,
});
