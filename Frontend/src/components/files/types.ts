// File metadata types
export interface FileMetadata {
  file_id: string;
  filename: string;
  folder_path: string;
  size_bytes: number;
  content_type: string;
  created_at: string;
  document_id: string | null;
}

export interface FileListResponse {
  files: FileMetadata[];
  total: number;
}

export interface FoldersResponse {
  folders: string[];
}

// Request types
export interface FileMoveRequest {
  folder_path?: string | null;
  filename?: string | null;
}

export interface FileUploadParams {
  file: File;
  folder_path?: string;
}

// UI state types
export interface FolderNode {
  name: string;
  path: string;
  files: FileMetadata[];
  subfolders: FolderNode[];
}

