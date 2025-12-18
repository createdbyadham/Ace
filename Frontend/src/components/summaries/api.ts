import apiClient from '@/infrastructure/api/client';
import type {
  Summary,
  SummaryListResponse,
  SummaryUpdate,
  SummaryGenerationResponse,
  SummaryLength,
} from '@/components/summaries/types';

export const summariesApi = {
  // List summaries
  listSummaries: async (search?: string, limit: number = 50, offset: number = 0): Promise<SummaryListResponse> => {
    const params: Record<string, any> = { limit, offset };
    if (search) {
      params.search = search;
    }
    const { data } = await apiClient.get<SummaryListResponse>('/summaries', { params });
    return data;
  },

  // Get a single summary
  getSummary: async (summaryId: string): Promise<Summary> => {
    const { data } = await apiClient.get<Summary>(`/summaries/${summaryId}`);
    return data;
  },

  // Update a summary
  updateSummary: async (summaryId: string, payload: SummaryUpdate): Promise<Summary> => {
    const { data } = await apiClient.patch<Summary>(`/summaries/${summaryId}`, null, {
      params: payload,
    });
    return data;
  },

  // Delete a summary
  deleteSummary: async (summaryId: string): Promise<void> => {
    await apiClient.delete(`/summaries/${summaryId}`);
  },

  // AI Generation
  generateSummary: async (
    files: Array<File>,
    title: string,
    summaryLength: SummaryLength = 'medium'
  ): Promise<SummaryGenerationResponse> => {
    const formData = new FormData();
    files.forEach((file) => formData.append('files', file));
    formData.append('title', title);
    formData.append('summary_length', summaryLength);

    const { data } = await apiClient.post<SummaryGenerationResponse>(
      '/agents/summary',
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

export default summariesApi;

