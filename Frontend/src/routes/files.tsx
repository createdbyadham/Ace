import { createFileRoute } from '@tanstack/react-router';
import FilesPage from '@/components/files/components/files';

export const Route = createFileRoute('/files')({
  component: FilesPage,
});
