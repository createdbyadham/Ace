import { useEffect, useState } from 'react';
import { Loader2 } from 'lucide-react';
import type { FileMetadata, FileMoveRequest } from '@/components/files/types';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

// ============================================
// Move/Rename File Dialog
// ============================================
interface MoveFileDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  file: FileMetadata | null;
  folders: string[];
  onSubmit: (data: FileMoveRequest) => void;
  isLoading: boolean;
}

export function MoveFileDialog({
  open,
  onOpenChange,
  file,
  folders,
  onSubmit,
  isLoading,
}: MoveFileDialogProps) {
  const [filename, setFilename] = useState('');
  const [folderPath, setFolderPath] = useState('/');
  const [newFolder, setNewFolder] = useState('');
  const [useNewFolder, setUseNewFolder] = useState(false);

  // Reset form when dialog opens or file changes
  useEffect(() => {
    if (open && file) {
      setFilename(file.filename);
      setFolderPath(file.folder_path);
      setNewFolder('');
      setUseNewFolder(false);
    }
  }, [open, file]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!filename.trim()) return;

    const targetFolder = useNewFolder && newFolder.trim() 
      ? (newFolder.startsWith('/') ? newFolder.trim() : `/${newFolder.trim()}`)
      : folderPath;

    const payload: FileMoveRequest = {};
    
    if (filename.trim() !== file?.filename) {
      payload.filename = filename.trim();
    }
    if (targetFolder !== file?.folder_path) {
      payload.folder_path = targetFolder;
    }

    if (Object.keys(payload).length === 0) {
      onOpenChange(false);
      return;
    }

    onSubmit(payload);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="bg-background border-white/10 max-w-lg">
        <DialogHeader>
          <DialogTitle>Move / Rename File</DialogTitle>
          <DialogDescription>
            Update the file name or move it to a different folder
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="filename">Filename</Label>
            <Input
              id="filename"
              placeholder="document.pdf"
              value={filename}
              onChange={(e) => setFilename(e.target.value)}
              className="bg-white/5 border-white/10"
            />
          </div>

          <div className="space-y-2">
            <Label>Folder</Label>
            {!useNewFolder ? (
              <Select value={folderPath} onValueChange={setFolderPath}>
                <SelectTrigger className="bg-white/5 border-white/10">
                  <SelectValue placeholder="Select folder" />
                </SelectTrigger>
                <SelectContent className="bg-background border-white/10">
                  {folders.map((folder) => (
                    <SelectItem key={folder} value={folder}>
                      {folder === '/' ? 'Root (/)' : folder}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            ) : (
              <Input
                placeholder="/lectures/week1"
                value={newFolder}
                onChange={(e) => setNewFolder(e.target.value)}
                className="bg-white/5 border-white/10"
              />
            )}
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => setUseNewFolder(!useNewFolder)}
              className="text-xs text-foreground/50 hover:text-foreground/80"
            >
              {useNewFolder ? 'Choose existing folder' : 'Create new folder'}
            </Button>
          </div>

          <DialogFooter>
            <Button type="button" variant="ghost" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={isLoading || !filename.trim()}>
              {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Save'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

// ============================================
// Delete Confirm Dialog
// ============================================
interface DeleteFileDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onConfirm: () => void;
  isLoading: boolean;
  filename?: string;
}

export function DeleteFileDialog({
  open,
  onOpenChange,
  onConfirm,
  isLoading,
  filename,
}: DeleteFileDialogProps) {
  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent className="bg-background border-white/10">
        <AlertDialogHeader>
          <AlertDialogTitle>Delete File</AlertDialogTitle>
          <AlertDialogDescription>
            Are you sure you want to delete{' '}
            {filename ? (
              <span className="font-medium text-foreground">"{filename}"</span>
            ) : (
              'this file'
            )}
            ? This will also remove it from the AI knowledge base. This action cannot be
            undone.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>Cancel</AlertDialogCancel>
          <AlertDialogAction
            onClick={onConfirm}
            disabled={isLoading}
            className="bg-red-600 hover:bg-red-500"
          >
            {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Delete'}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}

// ============================================
// Create Folder Dialog
// ============================================
interface CreateFolderDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (folderPath: string) => void;
  currentPath?: string;
}

export function CreateFolderDialog({
  open,
  onOpenChange,
  onSubmit,
  currentPath = '/',
}: CreateFolderDialogProps) {
  const [folderName, setFolderName] = useState('');

  useEffect(() => {
    if (open) {
      setFolderName('');
    }
  }, [open]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!folderName.trim()) return;

    const basePath = currentPath === '/' ? '' : currentPath;
    const newPath = `${basePath}/${folderName.trim()}`;
    onSubmit(newPath);
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="bg-background border-white/10 max-w-md">
        <DialogHeader>
          <DialogTitle>Create Folder</DialogTitle>
          <DialogDescription>
            Create a new folder in {currentPath === '/' ? 'root' : currentPath}
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="folder-name">Folder Name</Label>
            <Input
              id="folder-name"
              placeholder="e.g., lectures"
              value={folderName}
              onChange={(e) => setFolderName(e.target.value)}
              className="bg-white/5 border-white/10"
              autoFocus
            />
          </div>
          <DialogFooter>
            <Button type="button" variant="ghost" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={!folderName.trim()}>
              Create
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

