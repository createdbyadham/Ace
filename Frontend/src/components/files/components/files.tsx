import { useNavigate } from '@tanstack/react-router';
import { useCallback, useState, useMemo, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useDropzone } from 'react-dropzone';
import {
  ChevronRight,
  Download,
  File,
  FileText,
  Folder,
  FolderOpen,
  Grid3X3,
  Home,
  List,
  Loader2,
  MoreVertical,
  Pencil,
  Plus,
  Search,
  Trash2,
  Upload,
  X,
} from 'lucide-react';
import { toast } from 'sonner';
import type { FileMetadata, FileMoveRequest } from '@/components/files/types';
import { useFiles, useFolders, useFileMutations, downloadFile } from '@/components/files/useFiles';
import {
  MoveFileDialog,
  DeleteFileDialog,
  CreateFolderDialog,
} from '@/components/files/components/FileDialogs';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import Particles from '@/components/ui/Particles';
import { Footer } from '@/components/layout/Footer';
import { Navbar } from '@/components/layout/Navbar';
import { useAuth } from '@/context/AuthContext';

export default function FilesPage() {
  const navigate = useNavigate();
  const { isAuthenticated, user, logout } = useAuth();

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    navigate({ to: '/login' });
    return null;
  }

  return <FilesContent user={user} logout={logout} />;
}

function FilesContent({ user, logout }: { user: any; logout: () => void }) {
  // View state
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [currentPath, setCurrentPath] = useState('/');
  const [searchQuery, setSearchQuery] = useState('');

  // Dialog states
  const [showMoveDialog, setShowMoveDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [showCreateFolderDialog, setShowCreateFolderDialog] = useState(false);
  const [selectedFile, setSelectedFile] = useState<FileMetadata | null>(null);

  // Upload state
  const [uploadingFiles, setUploadingFiles] = useState<File[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Queries
  const { data: filesData, isLoading: filesLoading } = useFiles();
  const { data: foldersData } = useFolders();

  // Mutations
  const { uploadFile, moveFile, deleteFile, isUploading, isMoving, isDeleting } =
    useFileMutations();

  const files = filesData?.files || [];
  const folders = foldersData?.folders || ['/'];

  // Filter files by current path and search query
  const filteredFiles = useMemo(() => {
    let result = files;

    // Filter by path
    if (currentPath !== '/') {
      result = result.filter((f) => f.folder_path === currentPath);
    } else {
      result = result.filter((f) => f.folder_path === '/');
    }

    // Filter by search
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      result = result.filter((f) => f.filename.toLowerCase().includes(query));
    }

    return result;
  }, [files, currentPath, searchQuery]);

  // Get subfolders of current path
  const subfolders = useMemo(() => {
    const currentDepth = currentPath === '/' ? 0 : currentPath.split('/').filter(Boolean).length;
    
    return folders
      .filter((f) => {
        if (f === '/') return false;
        const parts = f.split('/').filter(Boolean);
        if (currentPath === '/') {
          return parts.length === 1;
        }
        return f.startsWith(currentPath + '/') && parts.length === currentDepth + 1;
      })
      .map((f) => {
        const parts = f.split('/').filter(Boolean);
        return {
          path: f,
          name: parts[parts.length - 1],
        };
      });
  }, [folders, currentPath]);

  // Breadcrumb parts
  const breadcrumbParts = useMemo(() => {
    if (currentPath === '/') return [];
    return currentPath.split('/').filter(Boolean);
  }, [currentPath]);

  // File dropzone
  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      const pdfFiles = acceptedFiles.filter((f) => f.type === 'application/pdf');
      if (pdfFiles.length !== acceptedFiles.length) {
        toast.error('Only PDF files are accepted');
      }

      if (pdfFiles.length === 0) return;

      setUploadingFiles(pdfFiles);

      for (const file of pdfFiles) {
        try {
          await uploadFile(file, currentPath);
        } catch {
          // Error toast already shown in hook
        }
      }

      setUploadingFiles([]);
    },
    [uploadFile, currentPath]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'] },
    multiple: true,
    noClick: true,
  });

  // Handlers
  const handleMoveFile = (data: FileMoveRequest) => {
    if (!selectedFile) return;
    moveFile(selectedFile.file_id, data, {
      onSuccess: () => {
        setShowMoveDialog(false);
        setSelectedFile(null);
      },
    });
  };

  const handleDeleteFile = () => {
    if (!selectedFile) return;
    deleteFile(selectedFile.file_id, {
      onSuccess: () => {
        setShowDeleteDialog(false);
        setSelectedFile(null);
      },
    });
  };

  const handleDownload = async (file: FileMetadata) => {
    await downloadFile(file.file_id, file.filename);
  };

  const navigateToFolder = (path: string) => {
    setCurrentPath(path);
    setSearchQuery('');
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  return (
    <div {...getRootProps()} className="relative min-h-screen flex flex-col">
      <input {...getInputProps()} />

      {/* Background */}
      <div className="fixed inset-0 z-0">
        <Particles
          particleCount={80}
          particleSpread={12}
          speed={0.03}
          particleColors={['#6366f1', '#8b5cf6', '#a855f7']}
          moveParticlesOnHover
          particleHoverFactor={0.3}
          alphaParticles
          particleBaseSize={50}
          sizeRandomness={1}
          cameraDistance={30}
        />
      </div>
      <div className="fixed inset-0 z-0 bg-gradient-to-b from-background via-background/95 to-background pointer-events-none" />

      {/* Drag overlay */}
      <AnimatePresence>
        {isDragActive && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 bg-indigo-600/20 backdrop-blur-sm flex items-center justify-center"
          >
            <motion.div
              initial={{ scale: 0.9 }}
              animate={{ scale: 1 }}
              className="bg-background/90 border-2 border-dashed border-indigo-500 rounded-2xl p-12 text-center"
            >
              <Upload className="w-16 h-16 mx-auto mb-4 text-indigo-400" />
              <p className="text-xl font-medium text-indigo-300">Drop your PDFs here</p>
              <p className="text-sm text-foreground/50 mt-2">Files will be uploaded to {currentPath}</p>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      <Navbar isAuthenticated={true} user={user} onLogout={logout} className="relative z-10" />

      <main className="relative z-10 flex-1 max-w-7xl mx-auto w-full px-4 py-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-3xl font-bold">My Files</h1>
              <p className="text-foreground/60 mt-1">
                Upload and manage your lecture materials
              </p>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="icon"
                onClick={() => setViewMode(viewMode === 'grid' ? 'list' : 'grid')}
                className="border-white/10"
              >
                {viewMode === 'grid' ? (
                  <List className="w-4 h-4" />
                ) : (
                  <Grid3X3 className="w-4 h-4" />
                )}
              </Button>
              <Button
                onClick={() => setShowCreateFolderDialog(true)}
                variant="outline"
                className="gap-2 border-white/10"
              >
                <Plus className="w-4 h-4" />
                New Folder
              </Button>
              <Button
                onClick={() => fileInputRef.current?.click()}
                className="gap-2 bg-indigo-600 hover:bg-indigo-500"
              >
                <Upload className="w-4 h-4" />
                Upload
              </Button>
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf"
                multiple
                className="hidden"
                onChange={(e) => {
                  if (e.target.files) {
                    onDrop(Array.from(e.target.files));
                    e.target.value = ''; // Reset to allow same file selection
                  }
                }}
              />
            </div>
          </div>

          {/* Breadcrumb & Search */}
          <div className="flex items-center justify-between mb-6 gap-4">
            <div className="flex items-center gap-2 text-sm">
              <button
                onClick={() => navigateToFolder('/')}
                className="flex items-center gap-1 text-foreground/60 hover:text-foreground transition-colors"
              >
                <Home className="w-4 h-4" />
              </button>
              {breadcrumbParts.map((part, index) => {
                const path = '/' + breadcrumbParts.slice(0, index + 1).join('/');
                const isLast = index === breadcrumbParts.length - 1;
                return (
                  <div key={path} className="flex items-center gap-2">
                    <ChevronRight className="w-4 h-4 text-foreground/40" />
                    <button
                      onClick={() => navigateToFolder(path)}
                      className={`hover:text-foreground transition-colors ${
                        isLast ? 'text-foreground font-medium' : 'text-foreground/60'
                      }`}
                    >
                      {part}
                    </button>
                  </div>
                );
              })}
            </div>

            <div className="relative w-64">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-foreground/40" />
              <Input
                placeholder="Search files..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9 bg-white/5 border-white/10"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery('')}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-foreground/40 hover:text-foreground"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>
          </div>

          {/* Uploading indicator */}
          {uploadingFiles.length > 0 && (
            <Card className="mb-6 border-indigo-500/30 bg-indigo-500/10">
              <CardContent className="py-4">
                <div className="flex items-center gap-3">
                  <Loader2 className="w-5 h-5 animate-spin text-indigo-400" />
                  <span className="text-sm">
                    Uploading {uploadingFiles.length} file{uploadingFiles.length > 1 ? 's' : ''}...
                  </span>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Content */}
          {filesLoading ? (
            <div className="flex items-center justify-center py-20">
              <Loader2 className="w-8 h-8 animate-spin text-indigo-400" />
            </div>
          ) : (
            <>
              {/* Folders */}
              {subfolders.length > 0 && (
                <div className="mb-6">
                  <h3 className="text-sm font-medium text-foreground/50 mb-3">Folders</h3>
                  <div className={viewMode === 'grid' ? 'grid sm:grid-cols-2 lg:grid-cols-4 gap-3' : 'space-y-2'}>
                    {subfolders.map((folder) => (
                      <motion.div
                        key={folder.path}
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        onClick={() => navigateToFolder(folder.path)}
                        className="cursor-pointer"
                      >
                        <Card className="border-white/10 bg-white/[0.02] hover:bg-white/[0.05] hover:border-amber-500/30 transition-all">
                          <CardContent className={`flex items-center gap-3 ${viewMode === 'grid' ? 'p-4' : 'p-3'}`}>
                            <div className="p-2 rounded-lg bg-amber-500/20">
                              <Folder className="w-5 h-5 text-amber-400" />
                            </div>
                            <span className="font-medium truncate">{folder.name}</span>
                          </CardContent>
                        </Card>
                      </motion.div>
                    ))}
                  </div>
                </div>
              )}

              {/* Files */}
              {filteredFiles.length > 0 ? (
                <div>
                  <h3 className="text-sm font-medium text-foreground/50 mb-3">Files</h3>
                  {viewMode === 'grid' ? (
                    <div className="grid sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                      {filteredFiles.map((file, index) => (
                        <motion.div
                          key={file.file_id}
                          initial={{ opacity: 0, y: 10 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ duration: 0.2, delay: index * 0.03 }}
                        >
                          <Card className="group border-white/10 bg-white/[0.02] hover:bg-white/[0.05] hover:border-indigo-500/30 transition-all">
                            <CardContent className="p-4">
                              <div className="flex items-start justify-between">
                                <div
                                  className="flex-1 min-w-0 cursor-pointer"
                                  onClick={() => handleDownload(file)}
                                >
                                  <div className="p-3 rounded-xl bg-red-500/20 w-fit mb-3">
                                    <FileText className="w-8 h-8 text-red-400" />
                                  </div>
                                  <p className="font-medium truncate mb-1" title={file.filename}>
                                    {file.filename}
                                  </p>
                                  <p className="text-xs text-foreground/50">
                                    {formatFileSize(file.size_bytes)} • {formatDate(file.created_at)}
                                  </p>
                                </div>
                                <DropdownMenu>
                                  <DropdownMenuTrigger asChild>
                                    <Button
                                      variant="ghost"
                                      size="sm"
                                      className="h-8 w-8 p-0 opacity-0 group-hover:opacity-100 transition-opacity"
                                    >
                                      <MoreVertical className="w-4 h-4" />
                                    </Button>
                                  </DropdownMenuTrigger>
                                  <DropdownMenuContent align="end" className="bg-background border-white/10">
                                    <DropdownMenuItem onClick={() => handleDownload(file)}>
                                      <Download className="w-4 h-4 mr-2" />
                                      Download
                                    </DropdownMenuItem>
                                    <DropdownMenuItem
                                      onClick={() => {
                                        setSelectedFile(file);
                                        setShowMoveDialog(true);
                                      }}
                                    >
                                      <Pencil className="w-4 h-4 mr-2" />
                                      Move / Rename
                                    </DropdownMenuItem>
                                    <DropdownMenuSeparator className="bg-white/10" />
                                    <DropdownMenuItem
                                      onClick={() => {
                                        setSelectedFile(file);
                                        setShowDeleteDialog(true);
                                      }}
                                      className="text-red-400 focus:text-red-400"
                                    >
                                      <Trash2 className="w-4 h-4 mr-2" />
                                      Delete
                                    </DropdownMenuItem>
                                  </DropdownMenuContent>
                                </DropdownMenu>
                              </div>
                            </CardContent>
                          </Card>
                        </motion.div>
                      ))}
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {filteredFiles.map((file, index) => (
                        <motion.div
                          key={file.file_id}
                          initial={{ opacity: 0, x: -10 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ duration: 0.2, delay: index * 0.02 }}
                        >
                          <Card className="group border-white/10 bg-white/[0.02] hover:bg-white/[0.05] hover:border-indigo-500/30 transition-all">
                            <CardContent className="p-3">
                              <div className="flex items-center gap-4">
                                <div className="p-2 rounded-lg bg-red-500/20">
                                  <FileText className="w-5 h-5 text-red-400" />
                                </div>
                                <div
                                  className="flex-1 min-w-0 cursor-pointer"
                                  onClick={() => handleDownload(file)}
                                >
                                  <p className="font-medium truncate" title={file.filename}>
                                    {file.filename}
                                  </p>
                                  <p className="text-xs text-foreground/50">
                                    {formatFileSize(file.size_bytes)} • {formatDate(file.created_at)}
                                  </p>
                                </div>
                                <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    className="h-8 w-8 p-0"
                                    onClick={() => handleDownload(file)}
                                  >
                                    <Download className="w-4 h-4" />
                                  </Button>
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    className="h-8 w-8 p-0"
                                    onClick={() => {
                                      setSelectedFile(file);
                                      setShowMoveDialog(true);
                                    }}
                                  >
                                    <Pencil className="w-4 h-4" />
                                  </Button>
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    className="h-8 w-8 p-0 text-red-400 hover:text-red-300 hover:bg-red-500/10"
                                    onClick={() => {
                                      setSelectedFile(file);
                                      setShowDeleteDialog(true);
                                    }}
                                  >
                                    <Trash2 className="w-4 h-4" />
                                  </Button>
                                </div>
                              </div>
                            </CardContent>
                          </Card>
                        </motion.div>
                      ))}
                    </div>
                  )}
                </div>
              ) : (
                /* Empty state */
                subfolders.length === 0 && (
                  <Card className="border-white/10 bg-white/[0.02]">
                    <CardContent className="flex flex-col items-center justify-center py-16 text-foreground/60">
                      <div className="p-4 rounded-2xl bg-indigo-500/10 mb-4">
                        <FolderOpen className="w-12 h-12 text-indigo-400" />
                      </div>
                      <p className="text-lg font-medium mb-2">
                        {searchQuery ? 'No files found' : 'No files yet'}
                      </p>
                      <p className="text-sm text-center max-w-md mb-6">
                        {searchQuery
                          ? `No files matching "${searchQuery}" in this folder`
                          : 'Upload your lecture PDFs to get started. They will be indexed for AI-powered search and chat.'}
                      </p>
                      {!searchQuery && (
                        <Button
                          onClick={() => fileInputRef.current?.click()}
                          className="gap-2"
                        >
                          <Upload className="w-4 h-4" />
                          Upload PDFs
                        </Button>
                      )}
                    </CardContent>
                  </Card>
                )
              )}
            </>
          )}
        </motion.div>
      </main>

      <Footer className="relative z-10" />

      {/* Dialogs */}
      <MoveFileDialog
        open={showMoveDialog}
        onOpenChange={(open) => {
          setShowMoveDialog(open);
          if (!open) setSelectedFile(null);
        }}
        file={selectedFile}
        folders={folders}
        onSubmit={handleMoveFile}
        isLoading={isMoving}
      />

      <DeleteFileDialog
        open={showDeleteDialog}
        onOpenChange={(open) => {
          setShowDeleteDialog(open);
          if (!open) setSelectedFile(null);
        }}
        onConfirm={handleDeleteFile}
        isLoading={isDeleting}
        filename={selectedFile?.filename}
      />

      <CreateFolderDialog
        open={showCreateFolderDialog}
        onOpenChange={setShowCreateFolderDialog}
        onSubmit={(path) => {
          // Navigate to the new folder (it will be created when a file is uploaded there)
          setCurrentPath(path);
          toast.success('Folder path set', {
            description: 'Upload a file to create this folder.',
          });
        }}
        currentPath={currentPath}
      />
    </div>
  );
}

