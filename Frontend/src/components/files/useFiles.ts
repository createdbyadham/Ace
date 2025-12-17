import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { filesApi } from '@/components/files/api';
import type { FileMoveRequest } from '@/components/files/types';

export const fileKeys = {
  all: ['files'] as const,
  list: (folderPath?: string) => [...fileKeys.all, 'list', { folderPath }] as const,
  file: (id: string) => [...fileKeys.all, 'file', id] as const,
  folders: () => [...fileKeys.all, 'folders'] as const,
};

// Query hooks
export function useFiles(folderPath?: string) {
  return useQuery({
    queryKey: fileKeys.list(folderPath),
    queryFn: () => filesApi.listFiles(folderPath),
  });
}

export function useFile(fileId: string) {
  return useQuery({
    queryKey: fileKeys.file(fileId),
    queryFn: () => filesApi.getFile(fileId),
    enabled: !!fileId,
  });
}

export function useFolders() {
  return useQuery({
    queryKey: fileKeys.folders(),
    queryFn: filesApi.listFolders,
  });
}

// Mutation hooks
export function useUploadFile() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ file, folderPath }: { file: File; folderPath?: string }) =>
      filesApi.uploadFile(file, folderPath),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: fileKeys.all });
    },
  });
}

export function useMoveFile() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ fileId, payload }: { fileId: string; payload: FileMoveRequest }) =>
      filesApi.moveFile(fileId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: fileKeys.all });
    },
  });
}

export function useDeleteFile() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (fileId: string) => filesApi.deleteFile(fileId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: fileKeys.all });
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

export function useFileMutations() {
  const uploadFileMutation = useUploadFile();
  const moveFileMutation = useMoveFile();
  const deleteFileMutation = useDeleteFile();

  const uploadFile = async (
    file: File,
    folderPath?: string,
    callbacks?: MutationCallbacks
  ) => {
    try {
      const result = await uploadFileMutation.mutateAsync({ file, folderPath });
      toast.success('File uploaded successfully', {
        description: `"${result.filename}" has been added to your library.`,
      });
      callbacks?.onSuccess?.();
      return result;
    } catch (error: any) {
      toast.error('Failed to upload file', {
        description: error?.response?.data?.detail || 'Please try again.',
      });
      callbacks?.onError?.();
      throw error;
    }
  };

  const moveFile = async (
    fileId: string,
    payload: FileMoveRequest,
    callbacks?: MutationCallbacks
  ) => {
    try {
      const result = await moveFileMutation.mutateAsync({ fileId, payload });
      toast.success('File updated successfully');
      callbacks?.onSuccess?.();
      return result;
    } catch (error: any) {
      toast.error('Failed to update file', {
        description: error?.response?.data?.detail || 'Please try again.',
      });
      callbacks?.onError?.();
      throw error;
    }
  };

  const deleteFile = async (fileId: string, callbacks?: MutationCallbacks) => {
    try {
      await deleteFileMutation.mutateAsync(fileId);
      toast.success('File deleted successfully');
      callbacks?.onSuccess?.();
    } catch (error: any) {
      toast.error('Failed to delete file', {
        description: error?.response?.data?.detail || 'Please try again.',
      });
      callbacks?.onError?.();
    }
  };

  return {
    uploadFile,
    moveFile,
    deleteFile,
    isUploading: uploadFileMutation.isPending,
    isMoving: moveFileMutation.isPending,
    isDeleting: deleteFileMutation.isPending,
  };
}

// Download helper (doesn't need react-query since it's a one-off action)
export async function downloadFile(fileId: string, filename: string) {
  try {
    const blob = await filesApi.downloadFile(fileId);
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  } catch (error: any) {
    toast.error('Failed to download file', {
      description: error?.response?.data?.detail || 'Please try again.',
    });
    throw error;
  }
}

