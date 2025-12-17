import { useEffect, useState } from 'react';
import { Loader2, X, Plus, Trash2 } from 'lucide-react';
import type {
  QuestionSet,
  QuestionSetCreate,
  Question,
  QuestionCreate,
} from '@/components/quiz/types';
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
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';

// ============================================
// Question Set Dialog
// ============================================
interface QuestionSetDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  questionSet?: QuestionSet | null;
  onSubmit: (data: QuestionSetCreate) => void;
  isLoading: boolean;
}

export function QuestionSetDialog({
  open,
  onOpenChange,
  questionSet,
  onSubmit,
  isLoading,
}: QuestionSetDialogProps) {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [tags, setTags] = useState<string[]>([]);
  const [tagInput, setTagInput] = useState('');

  useEffect(() => {
    if (open) {
      setTitle(questionSet?.title || '');
      setDescription(questionSet?.description || '');
      setTags(questionSet?.tags || []);
      setTagInput('');
    }
  }, [open, questionSet]);

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

    const isEditing = !!questionSet;

    onSubmit({
      title: title.trim(),
      description: isEditing ? (description.trim() || null) : (description.trim() || undefined),
      tags: isEditing ? tags : (tags.length > 0 ? tags : undefined),
    });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="bg-background border-white/10 max-w-lg">
        <DialogHeader>
          <DialogTitle>{questionSet ? 'Edit Question Set' : 'Create Question Set'}</DialogTitle>
          <DialogDescription>
            {questionSet ? 'Update your question set details' : 'Create a new question set for your quizzes'}
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="title">Title *</Label>
            <Input
              id="title"
              placeholder="e.g., Biology Chapter 5 Quiz"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="bg-white/5 border-white/10"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              placeholder="Add a description for your question set..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="bg-white/5 border-white/10 min-h-[80px]"
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
                    className="inline-flex items-center gap-1 px-2 py-1 text-sm rounded-md bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
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
              {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : questionSet ? 'Save' : 'Create'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

// ============================================
// Question Dialog (MCQ)
// ============================================
interface QuestionDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  question?: Question | null;
  onSubmit: (data: QuestionCreate) => void;
  isLoading: boolean;
}

export function QuestionDialog({
  open,
  onOpenChange,
  question,
  onSubmit,
  isLoading,
}: QuestionDialogProps) {
  const [questionText, setQuestionText] = useState('');
  const [options, setOptions] = useState<string[]>(['', '', '', '']);
  const [correctAnswer, setCorrectAnswer] = useState<number>(0);
  const [explanation, setExplanation] = useState('');

  useEffect(() => {
    if (open) {
      setQuestionText(question?.question_text || '');
      setOptions(question?.options || ['', '', '', '']);
      setCorrectAnswer(question?.correct_answer ?? 0);
      setExplanation(question?.explanation || '');
    }
  }, [open, question]);

  const handleOptionChange = (index: number, value: string) => {
    const newOptions = [...options];
    newOptions[index] = value;
    setOptions(newOptions);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!questionText.trim()) return;
    if (options.some((opt) => !opt.trim())) return;

    onSubmit({
      question_text: questionText.trim(),
      options: options.map((opt) => opt.trim()),
      correct_answer: correctAnswer,
      explanation: explanation.trim() || null,
    });
  };

  const isValid = questionText.trim() && options.every((opt) => opt.trim());

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="bg-background border-white/10 max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{question ? 'Edit Question' : 'Add New Question'}</DialogTitle>
          <DialogDescription>
            {question ? 'Update your multiple choice question' : 'Create a new multiple choice question with 4 options'}
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-2">
            <Label htmlFor="question-text">Question *</Label>
            <Textarea
              id="question-text"
              placeholder="Enter your question..."
              value={questionText}
              onChange={(e) => setQuestionText(e.target.value)}
              className="bg-white/5 border-white/10 min-h-[100px]"
            />
          </div>

          <div className="space-y-3">
            <Label>Options * (select the correct answer)</Label>
            <RadioGroup
              value={correctAnswer.toString()}
              onValueChange={(v) => setCorrectAnswer(parseInt(v))}
              className="space-y-3"
            >
              {options.map((option, index) => (
                <div
                  key={index}
                  className={`flex items-center gap-3 p-3 rounded-lg border transition-all ${
                    correctAnswer === index
                      ? 'border-emerald-500/50 bg-emerald-500/10'
                      : 'border-white/10 bg-white/[0.02]'
                  }`}
                >
                  <RadioGroupItem
                    value={index.toString()}
                    id={`option-${index}`}
                    className="border-white/30"
                  />
                  <div className="flex-1">
                    <Input
                      placeholder={`Option ${String.fromCharCode(65 + index)}`}
                      value={option}
                      onChange={(e) => handleOptionChange(index, e.target.value)}
                      className="bg-transparent border-white/10"
                    />
                  </div>
                  {correctAnswer === index && (
                    <span className="text-xs text-emerald-400 font-medium">Correct</span>
                  )}
                </div>
              ))}
            </RadioGroup>
          </div>

          <div className="space-y-2">
            <Label htmlFor="explanation">Explanation (optional)</Label>
            <Textarea
              id="explanation"
              placeholder="Add an explanation for the correct answer..."
              value={explanation}
              onChange={(e) => setExplanation(e.target.value)}
              className="bg-white/5 border-white/10 min-h-[80px]"
            />
          </div>

          <DialogFooter>
            <Button type="button" variant="ghost" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={isLoading || !isValid}>
              {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : question ? 'Save' : 'Add Question'}
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

// ============================================
// Quiz Start Dialog
// ============================================
interface QuizStartDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  questionCount: number;
  onStart: (options: { timeLimit: number | null; shuffle: boolean }) => void;
  isLoading: boolean;
}

export function QuizStartDialog({
  open,
  onOpenChange,
  questionCount,
  onStart,
  isLoading,
}: QuizStartDialogProps) {
  const [useTimeLimit, setUseTimeLimit] = useState(false);
  const [timeLimit, setTimeLimit] = useState(30);
  const [shuffle, setShuffle] = useState(true);

  const handleStart = () => {
    onStart({
      timeLimit: useTimeLimit ? timeLimit * 60 : null, // Convert minutes to seconds
      shuffle,
    });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="bg-background border-white/10 max-w-md">
        <DialogHeader>
          <DialogTitle>Start Quiz</DialogTitle>
          <DialogDescription>
            Configure your quiz settings before starting
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-6 py-4">
          <div className="flex items-center justify-between p-4 rounded-lg bg-white/[0.02] border border-white/10">
            <span className="text-foreground/70">Questions</span>
            <span className="text-xl font-bold text-emerald-400">{questionCount}</span>
          </div>

          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <Label htmlFor="shuffle" className="cursor-pointer">Shuffle questions</Label>
              <input
                type="checkbox"
                id="shuffle"
                checked={shuffle}
                onChange={(e) => setShuffle(e.target.checked)}
                className="w-5 h-5 rounded accent-emerald-500"
              />
            </div>

            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <Label htmlFor="time-limit" className="cursor-pointer">Time limit</Label>
                <input
                  type="checkbox"
                  id="time-limit"
                  checked={useTimeLimit}
                  onChange={(e) => setUseTimeLimit(e.target.checked)}
                  className="w-5 h-5 rounded accent-emerald-500"
                />
              </div>
              {useTimeLimit && (
                <div className="flex items-center gap-3">
                  <Input
                    type="number"
                    min={1}
                    max={180}
                    value={timeLimit}
                    onChange={(e) => setTimeLimit(parseInt(e.target.value) || 30)}
                    className="bg-white/5 border-white/10 w-24"
                  />
                  <span className="text-foreground/60">minutes</span>
                </div>
              )}
            </div>
          </div>
        </div>
        <DialogFooter>
          <Button type="button" variant="ghost" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button
            onClick={handleStart}
            disabled={isLoading || questionCount === 0}
            className="bg-emerald-600 hover:bg-emerald-500"
          >
            {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Start Quiz'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

