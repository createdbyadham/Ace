import { useEffect, useState } from 'react';
import { Loader2, X } from 'lucide-react';
import type { Card, CardCreate, Deck, DeckCreate } from '@/components/flashcards/types';
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
import { Textarea } from '@/components/ui/textarea';

// ============================================
// Deck Dialog
// ============================================
interface DeckDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  deck?: Deck | null;
  onSubmit: (data: DeckCreate) => void;
  isLoading: boolean;
}

export function DeckDialog({
  open,
  onOpenChange,
  deck,
  onSubmit,
  isLoading,
}: DeckDialogProps) {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [language, setLanguage] = useState('');
  const [tags, setTags] = useState<string[]>([]);
  const [tagInput, setTagInput] = useState('');

  // Reset form when dialog opens or deck changes
  useEffect(() => {
    if (open) {
      setTitle(deck?.title || '');
      setDescription(deck?.description || '');
      setLanguage(deck?.language || '');
      setTags(deck?.tags || []);
      setTagInput('');
    }
  }, [open, deck]);

  const handleAddTag = () => {
    const trimmed = tagInput.trim();
    if (trimmed && !tags.includes(trimmed)) {
      setTags([...tags, trimmed]);
      setTagInput('');
    }
  };

  const handleRemoveTag = (tagToRemove: string) => {
    setTags(tags.filter((t) => t !== tagToRemove));
  };

  const handleTagKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddTag();
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;
    
    // When editing, always include fields so they can be cleared
    // When creating, only include non-empty fields
    const isEditing = !!deck;
    
    onSubmit({
      title: title.trim(),
      description: isEditing ? (description.trim() || null) : (description.trim() || undefined),
      tags: isEditing ? tags : (tags.length > 0 ? tags : undefined),
      language: isEditing ? (language.trim() || null) : (language.trim() || undefined),
    });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="bg-background border-white/10 max-w-lg">
        <DialogHeader>
          <DialogTitle>{deck ? 'Edit Deck' : 'Create New Deck'}</DialogTitle>
          <DialogDescription>
            {deck ? 'Update your deck details' : 'Create a new deck to organize your flashcards'}
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="title">Title *</Label>
            <Input
              id="title"
              placeholder="e.g., Spanish Vocabulary"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="bg-white/5 border-white/10"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              placeholder="Add a description for your deck..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="bg-white/5 border-white/10 min-h-[80px]"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="language">Language</Label>
            <Input
              id="language"
              placeholder="e.g., English, Spanish, Japanese"
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              className="bg-white/5 border-white/10"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="tags">Tags</Label>
            <div className="flex gap-2">
              <Input
                id="tags"
                placeholder="Add a tag and press Enter"
                value={tagInput}
                onChange={(e) => setTagInput(e.target.value)}
                onKeyDown={handleTagKeyDown}
                className="bg-white/5 border-white/10 flex-1"
              />
              <Button type="button" variant="outline" onClick={handleAddTag} className="shrink-0">
                Add
              </Button>
            </div>
            {tags.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-2">
                {tags.map((tag) => (
                  <span
                    key={tag}
                    className="inline-flex items-center gap-1 px-2 py-1 text-sm rounded-md bg-indigo-500/20 text-indigo-300 border border-indigo-500/30"
                  >
                    {tag}
                    <button
                      type="button"
                      onClick={() => handleRemoveTag(tag)}
                      className="hover:text-red-400 transition-colors"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </span>
                ))}
              </div>
            )}
          </div>

          <DialogFooter>
            <Button type="button" variant="ghost" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={isLoading || !title.trim()}>
              {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : deck ? 'Save' : 'Create'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

// ============================================
// Card Dialog
// ============================================
interface CardDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  deckId?: string;
  card?: Card | null;
  onSubmit: (data: CardCreate) => void;
  isLoading: boolean;
}

export function CardDialog({
  open,
  onOpenChange,
  deckId,
  card,
  onSubmit,
  isLoading,
}: CardDialogProps) {
  const [front, setFront] = useState('');
  const [back, setBack] = useState('');

  // Reset form when dialog opens or card changes
  useEffect(() => {
    if (open) {
      setFront(card?.content?.front || '');
      setBack(card?.content?.back || '');
    }
  }, [open, card]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!front.trim() || !back.trim()) return;
    // Use the card's deck_id when editing, otherwise use the provided deckId
    const targetDeckId = card?.deck_id || deckId;
    onSubmit({
      deck_id: targetDeckId,
      content: {
        front: front.trim(),
        back: back.trim(),
      },
    });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="bg-background border-white/10">
        <DialogHeader>
          <DialogTitle>{card ? 'Edit Card' : 'Create New Card'}</DialogTitle>
          <DialogDescription>
            {card ? 'Update your flashcard' : 'Add a new flashcard to this deck'}
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="front">Front (Question)</Label>
            <Textarea
              id="front"
              placeholder="Enter the question or prompt..."
              value={front}
              onChange={(e) => setFront(e.target.value)}
              className="bg-white/5 border-white/10 min-h-[100px]"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="back">Back (Answer)</Label>
            <Textarea
              id="back"
              placeholder="Enter the answer..."
              value={back}
              onChange={(e) => setBack(e.target.value)}
              className="bg-white/5 border-white/10 min-h-[100px]"
            />
          </div>
          <DialogFooter>
            <Button type="button" variant="ghost" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={isLoading || !front.trim() || !back.trim()}>
              {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : card ? 'Save' : 'Create'}
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
  isLoading: boolean;
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
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent className="bg-background border-white/10">
        <AlertDialogHeader>
          <AlertDialogTitle>{title}</AlertDialogTitle>
          <AlertDialogDescription>{description}</AlertDialogDescription>
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
