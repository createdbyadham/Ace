import apiClient from '@/infrastructure/api/client';
import type {
  FileMetadata,
  FileListResponse,
  FoldersResponse,
  FileMoveRequest,
} from '@/components/files/types';

export const filesApi = {
  // Upload a file
  uploadFile: async (file: File, folderPath: string = '/'): Promise<FileMetadata> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('folder_path', folderPath);

    const { data } = await apiClient.post<FileMetadata>('/files/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return data;
  },

  // List files
  listFiles: async (folderPath?: string): Promise<FileListResponse> => {
    const params = folderPath ? { folder_path: folderPath } : {};
    const { data } = await apiClient.get<FileListResponse>('/files', { params });
    return data;
  },

  // Get file metadata
  getFile: async (fileId: string): Promise<FileMetadata> => {
    const { data } = await apiClient.get<FileMetadata>(`/files/${fileId}`);
    return data;
  },

  // Download file
  downloadFile: async (fileId: string): Promise<Blob> => {
    const { data } = await apiClient.get<Blob>(`/files/${fileId}/download`, {
      responseType: 'blob',
    });
    return data;
  },

  // Move/rename file
  moveFile: async (fileId: string, payload: FileMoveRequest): Promise<FileMetadata> => {
    const { data } = await apiClient.patch<FileMetadata>(`/files/${fileId}`, payload);
    return data;
  },

  // Delete file
  deleteFile: async (fileId: string): Promise<void> => {
    await apiClient.delete(`/files/${fileId}`);
  },

  // List folders
  listFolders: async (): Promise<FoldersResponse> => {
    const { data } = await apiClient.get<FoldersResponse>('/files/folders');
    return data;
  },
};

export default filesApi;

