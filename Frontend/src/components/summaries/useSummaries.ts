import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { summariesApi } from '@/components/summaries/api';
import type { SummaryUpdate, SummaryLength } from '@/components/summaries/types';

export const summaryKeys = {
  all: ['summaries'] as const,
  list: (search?: string) => [...summaryKeys.all, 'list', { search }] as const,
  summary: (id: string) => [...summaryKeys.all, 'summary', id] as const,
};

// Query hooks
export function useSummaries(search?: string) {
  return useQuery({
    queryKey: summaryKeys.list(search),
    queryFn: () => summariesApi.listSummaries(search),
  });
}

export function useSummary(summaryId: string) {
  return useQuery({
    queryKey: summaryKeys.summary(summaryId),
    queryFn: () => summariesApi.getSummary(summaryId),
    enabled: !!summaryId,
  });
}

// Mutation hooks
export function useUpdateSummary() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ summaryId, payload }: { summaryId: string; payload: SummaryUpdate }) =>
      summariesApi.updateSummary(summaryId, payload),
    onSuccess: (_, { summaryId }) => {
      queryClient.invalidateQueries({ queryKey: summaryKeys.all });
      queryClient.invalidateQueries({ queryKey: summaryKeys.summary(summaryId) });
    },
  });
}

export function useDeleteSummary() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (summaryId: string) => summariesApi.deleteSummary(summaryId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: summaryKeys.all });
    },
  });
}

export function useGenerateSummary() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      files,
      title,
      summaryLength,
    }: {
      files: File[];
      title: string;
      summaryLength: SummaryLength;
    }) => summariesApi.generateSummary(files, title, summaryLength),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: summaryKeys.all });
    },
  });
}

// ============================================
// Enhanced hooks with toast notifications
// ============================================

interface MutationCallbacks {
  onSuccess?: () => void;
  onError?: () => void;
}

export function useSummaryMutations() {
  const updateSummaryMutation = useUpdateSummary();
  const deleteSummaryMutation = useDeleteSummary();

  const updateSummary = async (
    summaryId: string,
    payload: SummaryUpdate,
    callbacks?: MutationCallbacks
  ) => {
    try {
      const result = await updateSummaryMutation.mutateAsync({ summaryId, payload });
      toast.success('Summary updated successfully');
      callbacks?.onSuccess?.();
      return result;
    } catch (error: any) {
      toast.error('Failed to update summary', {
        description: error?.response?.data?.detail || 'Please try again.',
      });
      callbacks?.onError?.();
      throw error;
    }
  };

  const deleteSummary = async (summaryId: string, callbacks?: MutationCallbacks) => {
    try {
      await deleteSummaryMutation.mutateAsync(summaryId);
      toast.success('Summary deleted successfully');
      callbacks?.onSuccess?.();
    } catch (error: any) {
      toast.error('Failed to delete summary', {
        description: error?.response?.data?.detail || 'Please try again.',
      });
      callbacks?.onError?.();
    }
  };

  return {
    updateSummary,
    deleteSummary,
    isUpdating: updateSummaryMutation.isPending,
    isDeleting: deleteSummaryMutation.isPending,
  };
}

export function useAISummaryGeneration() {
  const generateMutation = useGenerateSummary();

  const generateSummary = async (
    params: {
      files: File[];
      title: string;
      summaryLength: SummaryLength;
    },
    callbacks?: MutationCallbacks
  ) => {
    try {
      const result = await generateMutation.mutateAsync(params);
      toast.success(`Summary generated!`, {
        description: `"${result.title}" - ${result.word_count} words`,
      });
      callbacks?.onSuccess?.();
      return result;
    } catch (error: any) {
      toast.error('Failed to generate summary', {
        description: error?.response?.data?.detail || 'Please try again.',
      });
      callbacks?.onError?.();
      throw error;
    }
  };

  return {
    generateSummary,
    isGenerating: generateMutation.isPending,
  };
}

