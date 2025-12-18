import { useState, useEffect } from 'react';
import { Loader2 } from 'lucide-react';
import type { Summary } from '@/components/summaries/types';
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
import { Textarea } from '@/components/ui/textarea';

// ============================================
// Edit Summary Dialog
// ============================================
interface EditSummaryDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  summary: Summary;
  onSubmit: (data: { title?: string; content?: string }) => void;
  isLoading?: boolean;
}

export function EditSummaryDialog({
  open,
  onOpenChange,
  summary,
  onSubmit,
  isLoading,
}: EditSummaryDialogProps) {
  const [title, setTitle] = useState(summary.title);
  const [content, setContent] = useState(summary.content);

  useEffect(() => {
    if (open) {
      setTitle(summary.title);
      setContent(summary.content);
    }
  }, [open, summary]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const updates: { title?: string; content?: string } = {};
    
    if (title !== summary.title) {
      updates.title = title;
    }
    if (content !== summary.content) {
      updates.content = content;
    }
    
    if (Object.keys(updates).length > 0) {
      onSubmit(updates);
    } else {
      onOpenChange(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px] bg-background border-white/10">
        <DialogHeader>
          <DialogTitle>Edit Summary</DialogTitle>
          <DialogDescription>Update the title or content of your summary.</DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="edit-title">Title</Label>
            <Input
              id="edit-title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="bg-white/5 border-white/10"
              required
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="edit-content">Content</Label>
            <Textarea
              id="edit-content"
              value={content}
              onChange={(e) => setContent(e.target.value)}
              className="bg-white/5 border-white/10 min-h-[300px] font-mono text-sm"
              required
            />
          </div>
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              className="border-white/10"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={isLoading}
              className="bg-emerald-600 hover:bg-emerald-500"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Saving...
                </>
              ) : (
                'Save Changes'
              )}
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
interface DeleteConfirmDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onConfirm: () => void;
  isLoading?: boolean;
  title: string;
  description: string;
}

export function DeleteConfirmDialog({
  open,
  onOpenChange,
  onConfirm,
  isLoading,
  title,
  description,
}: DeleteConfirmDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px] bg-background border-white/10">
        <DialogHeader>
          <DialogTitle className="text-red-400">{title}</DialogTitle>
          <DialogDescription>{description}</DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button
            type="button"
            variant="outline"
            onClick={() => onOpenChange(false)}
            className="border-white/10"
          >
            Cancel
          </Button>
          <Button
            onClick={onConfirm}
            disabled={isLoading}
            variant="destructive"
            className="bg-red-600 hover:bg-red-500"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Deleting...
              </>
            ) : (
              'Delete'
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

