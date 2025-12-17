import { createFileRoute, useNavigate } from '@tanstack/react-router';
import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useDropzone } from 'react-dropzone';
import {
  ArrowLeft,
  ArrowRight,
  Check,
  CheckCircle,
  ChevronRight,
  Clock,
  FileQuestion,
  FileText,
  FolderOpen,
  HelpCircle,
  Loader2,
  Pencil,
  Play,
  Plus,
  RefreshCcw,
  Sparkles,
  Trash2,
  Trophy,
  Upload,
  X,
  XCircle,
} from 'lucide-react';
import { toast } from 'sonner';
import type {
  QuestionSet,
  QuestionSetCreate,
  Question,
  QuestionCreate,
  QuizQuestion,
  QuizResult,
} from '@/components/quiz/types';
import {
  useQuestionSets,
  useQuestionSet,
  useQuestionSetMutations,
  useQuestionMutations,
  useQuizMutations,
  useAIGeneration,
} from '@/components/quiz/useQuiz';
import {
  QuestionSetDialog,
  QuestionDialog,
  DeleteConfirmDialog,
  QuizStartDialog,
} from '@/components/quiz/components/QuizDialogs';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Textarea } from '@/components/ui/textarea';
import Particles from '@/components/ui/Particles';
import { Footer } from '@/components/layout/Footer';
import { Navbar } from '@/components/layout/Navbar';
import { useAuth } from '@/context/AuthContext';

export const Route = createFileRoute('/quiz')({
  component: QuizPage,
});

function QuizPage() {
  const navigate = useNavigate();
  const { isAuthenticated, user, logout } = useAuth();

  if (!isAuthenticated) {
    navigate({ to: '/login' });
    return null;
  }

  return <QuizContent user={user} logout={logout} />;
}

function QuizContent({ user, logout }: { user: any; logout: () => void }) {
  const [activeTab, setActiveTab] = useState('sets');
  const [selectedSet, setSelectedSet] = useState<QuestionSet | null>(null);

  // Dialog states
  const [showCreateSet, setShowCreateSet] = useState(false);
  const [showEditSet, setShowEditSet] = useState(false);
  const [showDeleteSet, setShowDeleteSet] = useState(false);
  const [showCreateQuestion, setShowCreateQuestion] = useState(false);
  const [showEditQuestion, setShowEditQuestion] = useState(false);
  const [showDeleteQuestion, setShowDeleteQuestion] = useState(false);
  const [showQuizStart, setShowQuizStart] = useState(false);

  const [editingSet, setEditingSet] = useState<QuestionSet | null>(null);
  const [editingQuestion, setEditingQuestion] = useState<Question | null>(null);
  const [deletingSetId, setDeletingSetId] = useState<string | null>(null);
  const [deletingQuestionId, setDeletingQuestionId] = useState<string | null>(null);

  // AI Generation state
  const [aiFiles, setAiFiles] = useState<Array<File>>([]);
  const [aiSetTitle, setAiSetTitle] = useState('');
  const [aiSetDescription, setAiSetDescription] = useState('');
  const [aiNumQuestions, setAiNumQuestions] = useState(10);

  // Queries
  const { data: questionSets = [], isLoading: setsLoading } = useQuestionSets();
  const { data: questionSetDetails, isLoading: detailsLoading } = useQuestionSet(selectedSet?.set_id);

  // Mutations
  const {
    createQuestionSet,
    updateQuestionSet,
    deleteQuestionSet,
    isCreating: isSetCreating,
    isUpdating: isSetUpdating,
    isDeleting: isSetDeleting,
  } = useQuestionSetMutations();

  const {
    createQuestion,
    updateQuestion,
    deleteQuestion,
    isCreating: isQuestionCreating,
    isUpdating: isQuestionUpdating,
    isDeleting: isQuestionDeleting,
  } = useQuestionMutations();

  const { generateQuestions, isGenerating } = useAIGeneration();

  // File dropzone
  const onDrop = useCallback((acceptedFiles: Array<File>) => {
    const pdfFiles = acceptedFiles.filter((f) => f.type === 'application/pdf');
    if (pdfFiles.length !== acceptedFiles.length) {
      toast.error('Only PDF files are accepted');
    }
    setAiFiles((prev) => [...prev, ...pdfFiles]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'] },
    multiple: true,
  });

  const removeFile = (index: number) => {
    setAiFiles((prev) => prev.filter((_, i) => i !== index));
  };

  // Handlers
  const handleGenerateQuestions = async () => {
    if (aiFiles.length === 0) {
      toast.error('Please upload at least one PDF file');
      return;
    }
    if (!aiSetTitle.trim()) {
      toast.error('Please enter a question set title');
      return;
    }
    if (aiNumQuestions < 1 || aiNumQuestions > 100) {
      toast.error('Number of questions must be between 1 and 100');
      return;
    }

    await generateQuestions(
      {
        files: aiFiles,
        numQuestions: aiNumQuestions,
        setTitle: aiSetTitle,
        setDescription: aiSetDescription || undefined,
      },
      {
        onSuccess: () => {
          setAiFiles([]);
          setAiSetTitle('');
          setAiSetDescription('');
          setAiNumQuestions(10);
          setActiveTab('sets');
        },
      }
    );
  };

  const handleCreateSet = (data: QuestionSetCreate) => {
    createQuestionSet(data, { onSuccess: () => setShowCreateSet(false) });
  };

  const handleUpdateSet = (setId: string, data: QuestionSetCreate) => {
    updateQuestionSet(setId, data, {
      onSuccess: () => {
        setShowEditSet(false);
        setEditingSet(null);
      },
    });
  };

  const handleDeleteSet = () => {
    if (!deletingSetId) return;
    deleteQuestionSet(deletingSetId, {
      onSuccess: () => {
        setShowDeleteSet(false);
        if (selectedSet?.set_id === deletingSetId) {
          setSelectedSet(null);
        }
        setDeletingSetId(null);
      },
    });
  };

  const handleCreateQuestion = (data: QuestionCreate) => {
    if (!selectedSet) return;
    createQuestion(selectedSet.set_id, data, {
      onSuccess: () => setShowCreateQuestion(false),
    });
  };

  const handleUpdateQuestion = (questionId: string, data: QuestionCreate) => {
    updateQuestion(questionId, data, {
      onSuccess: () => {
        setShowEditQuestion(false);
        setEditingQuestion(null);
      },
    });
  };

  const handleDeleteQuestion = () => {
    if (!deletingQuestionId) return;
    deleteQuestion(deletingQuestionId, {
      onSuccess: () => {
        setShowDeleteQuestion(false);
        setDeletingQuestionId(null);
      },
    });
  };

  return (
    <div className="relative min-h-screen flex flex-col">
      {/* Background */}
      <div className="fixed inset-0 z-0">
        <Particles
          particleCount={80}
          particleSpread={12}
          speed={0.03}
          particleColors={['#10b981', '#34d399', '#6ee7b7']}
          moveParticlesOnHover
          particleHoverFactor={0.3}
          alphaParticles
          particleBaseSize={50}
          sizeRandomness={1}
          cameraDistance={30}
        />
      </div>
      <div className="fixed inset-0 z-0 bg-gradient-to-b from-background via-background/95 to-background pointer-events-none" />

      <Navbar isAuthenticated={true} user={user} onLogout={logout} className="relative z-10" />

      <main className="relative z-10 flex-1 max-w-7xl mx-auto w-full px-4 py-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          {/* Header */}
          <div className="flex items-center justify-between mb-8">
            <div>
              <h1 className="text-3xl font-bold">Quiz</h1>
              <p className="text-foreground/60 mt-1">Create, manage, and take quizzes</p>
            </div>
          </div>

          {/* Main Tabs */}
          <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
            <TabsList className="bg-white/5 border border-white/10">
              <TabsTrigger value="sets" className="data-[state=active]:bg-emerald-600">
                <FolderOpen className="w-4 h-4 mr-2" />
                My Question Sets
              </TabsTrigger>
              <TabsTrigger value="generate" className="data-[state=active]:bg-teal-600">
                <Sparkles className="w-4 h-4 mr-2" />
                AI Generate
              </TabsTrigger>
            </TabsList>

            {/* Question Sets Tab */}
            <TabsContent value="sets" className="space-y-6">
              {selectedSet ? (
                <QuestionSetView
                  questionSet={selectedSet}
                  details={questionSetDetails}
                  detailsLoading={detailsLoading}
                  onBack={() => setSelectedSet(null)}
                  onCreateQuestion={() => setShowCreateQuestion(true)}
                  onEditQuestion={(q) => {
                    setEditingQuestion(q);
                    setShowEditQuestion(true);
                  }}
                  onDeleteQuestion={(id) => {
                    setDeletingQuestionId(id);
                    setShowDeleteQuestion(true);
                  }}
                  onStartQuiz={() => setShowQuizStart(true)}
                />
              ) : (
                <QuestionSetsGrid
                  questionSets={questionSets}
                  loading={setsLoading}
                  onSelect={setSelectedSet}
                  onCreate={() => setShowCreateSet(true)}
                  onEdit={(set) => {
                    setEditingSet(set);
                    setShowEditSet(true);
                  }}
                  onDelete={(setId) => {
                    setDeletingSetId(setId);
                    setShowDeleteSet(true);
                  }}
                />
              )}
            </TabsContent>

            {/* AI Generate Tab */}
            <TabsContent value="generate">
              <Card className="border-white/10 bg-white/[0.02]">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Sparkles className="w-5 h-5 text-teal-400" />
                    Generate Quiz Questions with AI
                  </CardTitle>
                  <CardDescription>
                    Upload PDF files and let AI create multiple choice questions for you automatically
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  {/* File Upload */}
                  <div className="space-y-3">
                    <Label>PDF Files</Label>
                    <div
                      {...getRootProps()}
                      className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all ${
                        isDragActive
                          ? 'border-teal-500 bg-teal-500/10'
                          : 'border-white/20 hover:border-white/40 hover:bg-white/5'
                      }`}
                    >
                      <input {...getInputProps()} />
                      <Upload className="w-10 h-10 mx-auto mb-3 text-foreground/40" />
                      {isDragActive ? (
                        <p className="text-teal-400">Drop your PDFs here...</p>
                      ) : (
                        <>
                          <p className="text-foreground/70">Drag & drop PDF files here</p>
                          <p className="text-sm text-foreground/50 mt-1">or click to browse</p>
                        </>
                      )}
                    </div>

                    {/* File List */}
                    {aiFiles.length > 0 && (
                      <div className="space-y-2">
                        {aiFiles.map((file, index) => (
                          <div
                            key={index}
                            className="flex items-center justify-between p-3 rounded-lg bg-white/5 border border-white/10"
                          >
                            <div className="flex items-center gap-3">
                              <FileText className="w-5 h-5 text-teal-400" />
                              <span className="text-sm truncate max-w-[300px]">{file.name}</span>
                              <span className="text-xs text-foreground/50">
                                ({(file.size / 1024 / 1024).toFixed(2)} MB)
                              </span>
                            </div>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => removeFile(index)}
                              className="text-red-400 hover:text-red-300 hover:bg-red-500/10"
                            >
                              <X className="w-4 h-4" />
                            </Button>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Set Details */}
                  <div className="grid md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="set-title">Question Set Title</Label>
                      <Input
                        id="set-title"
                        placeholder="e.g., Biology Chapter 5 Quiz"
                        value={aiSetTitle}
                        onChange={(e) => setAiSetTitle(e.target.value)}
                        className="bg-white/5 border-white/10"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="num-questions">Number of Questions</Label>
                      <Input
                        id="num-questions"
                        type="number"
                        min={1}
                        max={100}
                        value={aiNumQuestions}
                        onChange={(e) => setAiNumQuestions(parseInt(e.target.value) || 10)}
                        className="bg-white/5 border-white/10"
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="set-desc">Description (optional)</Label>
                    <Textarea
                      id="set-desc"
                      placeholder="Add a description for your question set..."
                      value={aiSetDescription}
                      onChange={(e) => setAiSetDescription(e.target.value)}
                      className="bg-white/5 border-white/10 min-h-[80px]"
                    />
                  </div>

                  <Button
                    onClick={handleGenerateQuestions}
                    disabled={isGenerating || aiFiles.length === 0}
                    className="w-full bg-gradient-to-r from-teal-600 to-emerald-600 hover:from-teal-500 hover:to-emerald-500"
                  >
                    {isGenerating ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Generating...
                      </>
                    ) : (
                      <>
                        <Sparkles className="w-4 h-4 mr-2" />
                        Generate Questions
                      </>
                    )}
                  </Button>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </motion.div>
      </main>

      <Footer className="relative z-10" />

      {/* Dialogs */}
      <QuestionSetDialog
        open={showCreateSet}
        onOpenChange={setShowCreateSet}
        onSubmit={handleCreateSet}
        isLoading={isSetCreating}
      />

      {editingSet && (
        <QuestionSetDialog
          open={showEditSet}
          onOpenChange={(open) => {
            setShowEditSet(open);
            if (!open) setEditingSet(null);
          }}
          questionSet={editingSet}
          onSubmit={(data) => handleUpdateSet(editingSet.set_id, data)}
          isLoading={isSetUpdating}
        />
      )}

      {selectedSet && (
        <QuestionDialog
          open={showCreateQuestion}
          onOpenChange={setShowCreateQuestion}
          onSubmit={handleCreateQuestion}
          isLoading={isQuestionCreating}
        />
      )}

      {editingQuestion && (
        <QuestionDialog
          open={showEditQuestion}
          onOpenChange={(open) => {
            setShowEditQuestion(open);
            if (!open) setEditingQuestion(null);
          }}
          question={editingQuestion}
          onSubmit={(data) => handleUpdateQuestion(editingQuestion.question_id, data)}
          isLoading={isQuestionUpdating}
        />
      )}

      <DeleteConfirmDialog
        open={showDeleteSet}
        onOpenChange={setShowDeleteSet}
        onConfirm={handleDeleteSet}
        isLoading={isSetDeleting}
        title="Delete Question Set"
        description="Are you sure you want to delete this question set? All questions will also be deleted. This action cannot be undone."
      />

      <DeleteConfirmDialog
        open={showDeleteQuestion}
        onOpenChange={setShowDeleteQuestion}
        onConfirm={handleDeleteQuestion}
        isLoading={isQuestionDeleting}
        title="Delete Question"
        description="Are you sure you want to delete this question? This action cannot be undone."
      />

      {selectedSet && questionSetDetails && (
        <QuizStartDialogWrapper
          open={showQuizStart}
          onOpenChange={setShowQuizStart}
          questionSet={selectedSet}
          questionCount={questionSetDetails.questions.length}
        />
      )}
    </div>
  );
}

// ============================================
// Quiz Start Dialog Wrapper (includes quiz flow)
// ============================================
function QuizStartDialogWrapper({
  open,
  onOpenChange,
  questionSet,
  questionCount,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  questionSet: QuestionSet;
  questionCount: number;
}) {
  const [quizMode, setQuizMode] = useState<'config' | 'active' | 'results' | 'revision'>('config');
  const [quizSessionId, setQuizSessionId] = useState<string | null>(null);
  const [questions, setQuestions] = useState<QuizQuestion[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, number>>({});
  const [results, setResults] = useState<QuizResult | null>(null);
  const [timeLimit, setTimeLimit] = useState<number | null>(null);
  const [timeRemaining, setTimeRemaining] = useState<number | null>(null);
  const [startTime, setStartTime] = useState<number>(0);

  const { startQuiz, submitQuiz, startRevision, isStarting, isSubmitting, isStartingRevision } =
    useQuizMutations();

  // Timer effect
  useEffect(() => {
    if (quizMode !== 'active' || timeLimit === null) return;

    const interval = setInterval(() => {
      const elapsed = Math.floor((Date.now() - startTime) / 1000);
      const remaining = timeLimit - elapsed;

      if (remaining <= 0) {
        clearInterval(interval);
        handleSubmitQuiz();
      } else {
        setTimeRemaining(remaining);
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [quizMode, timeLimit, startTime]);

  const handleStartQuiz = async (options: { timeLimit: number | null; shuffle: boolean }) => {
    try {
      const result = await startQuiz(questionSet.set_id, {
        time_limit_seconds: options.timeLimit,
        shuffle: options.shuffle,
      });
      setQuizSessionId(result.quiz_session_id);
      setQuestions(result.questions);
      setTimeLimit(options.timeLimit);
      setTimeRemaining(options.timeLimit);
      setStartTime(Date.now());
      setCurrentIndex(0);
      setAnswers({});
      setQuizMode('active');
    } catch {
      // Error handled in mutation
    }
  };

  const handleSubmitQuiz = async () => {
    if (!quizSessionId) return;

    const submission = {
      answers: questions.map((q) => ({
        question_id: q.question_id,
        selected_answer: answers[q.question_id] ?? -1,
      })),
      time_taken_seconds: timeLimit ? timeLimit - (timeRemaining || 0) : Math.floor((Date.now() - startTime) / 1000),
    };

    try {
      const result = await submitQuiz(questionSet.set_id, quizSessionId, submission);
      setResults(result);
      setQuizMode('results');
    } catch {
      // Error handled in mutation
    }
  };

  const handleStartRevision = async () => {
    if (!results || !quizSessionId || results.wrong_question_ids.length === 0) return;

    try {
      const revision = await startRevision(
        questionSet.set_id,
        quizSessionId,
        results.wrong_question_ids,
        true
      );
      setQuizSessionId(revision.revision_session_id);
      setQuestions(revision.questions);
      setTimeLimit(null);
      setTimeRemaining(null);
      setStartTime(Date.now());
      setCurrentIndex(0);
      setAnswers({});
      setQuizMode('revision');
    } catch {
      // Error handled in mutation
    }
  };

  const handleAnswer = (questionId: string, answerIndex: number) => {
    setAnswers((prev) => ({ ...prev, [questionId]: answerIndex }));
  };

  const handleClose = () => {
    setQuizMode('config');
    setQuizSessionId(null);
    setQuestions([]);
    setCurrentIndex(0);
    setAnswers({});
    setResults(null);
    setTimeLimit(null);
    setTimeRemaining(null);
    onOpenChange(false);
  };

  const currentQuestion = questions[currentIndex];
  const answeredCount = Object.keys(answers).length;
  const progress = questions.length > 0 ? (answeredCount / questions.length) * 100 : 0;

  // Config mode
  if (quizMode === 'config') {
    return (
      <QuizStartDialog
        open={open}
        onOpenChange={handleClose}
        questionCount={questionCount}
        onStart={handleStartQuiz}
        isLoading={isStarting}
      />
    );
  }

  // Active quiz mode
  if (quizMode === 'active' || quizMode === 'revision') {
    return (
      <div className="fixed inset-0 z-50 bg-background">
        <div className="max-w-4xl mx-auto px-4 py-6 h-full flex flex-col">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <Button variant="ghost" onClick={handleClose} className="gap-2">
              <X className="w-4 h-4" />
              Exit Quiz
            </Button>
            <div className="flex items-center gap-4">
              {timeRemaining !== null && (
                <div className={`flex items-center gap-2 px-3 py-1.5 rounded-lg ${
                  timeRemaining < 60 ? 'bg-red-500/20 text-red-400' : 'bg-white/5'
                }`}>
                  <Clock className="w-4 h-4" />
                  <span className="font-mono">
                    {Math.floor(timeRemaining / 60)}:{(timeRemaining % 60).toString().padStart(2, '0')}
                  </span>
                </div>
              )}
              <span className="text-foreground/60">
                {quizMode === 'revision' ? 'Revision' : 'Quiz'}: {currentIndex + 1} / {questions.length}
              </span>
            </div>
          </div>

          {/* Progress */}
          <div className="mb-6">
            <Progress value={progress} className="h-2" />
            <p className="text-sm text-foreground/50 mt-2">
              {answeredCount} of {questions.length} answered
            </p>
          </div>

          {/* Question */}
          {currentQuestion && (
            <div className="flex-1 flex flex-col">
              <AnimatePresence mode="wait">
                <motion.div
                  key={currentQuestion.question_id}
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  className="flex-1"
                >
                  <Card className="border-white/10 bg-white/[0.02] mb-6">
                    <CardHeader>
                      <CardTitle className="text-xl leading-relaxed">
                        {currentQuestion.question_text}
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      {currentQuestion.options.map((option, index) => {
                        const isSelected = answers[currentQuestion.question_id] === index;
                        return (
                          <button
                            key={index}
                            onClick={() => handleAnswer(currentQuestion.question_id, index)}
                            className={`w-full p-4 rounded-lg text-left transition-all flex items-center gap-3 ${
                              isSelected
                                ? 'bg-emerald-500/20 border-emerald-500/50 border-2'
                                : 'bg-white/[0.02] border border-white/10 hover:bg-white/[0.05] hover:border-white/20'
                            }`}
                          >
                            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                              isSelected ? 'bg-emerald-500 text-white' : 'bg-white/10'
                            }`}>
                              {String.fromCharCode(65 + index)}
                            </div>
                            <span className="flex-1">{option}</span>
                            {isSelected && <Check className="w-5 h-5 text-emerald-400" />}
                          </button>
                        );
                      })}
                    </CardContent>
                  </Card>
                </motion.div>
              </AnimatePresence>

              {/* Navigation */}
              <div className="flex items-center justify-between">
                <Button
                  variant="outline"
                  onClick={() => setCurrentIndex((i) => Math.max(0, i - 1))}
                  disabled={currentIndex === 0}
                  className="gap-2"
                >
                  <ArrowLeft className="w-4 h-4" />
                  Previous
                </Button>

                <div className="flex gap-2">
                  {questions.map((_, i) => (
                    <button
                      key={i}
                      onClick={() => setCurrentIndex(i)}
                      className={`w-3 h-3 rounded-full transition-all ${
                        i === currentIndex
                          ? 'bg-emerald-500 scale-125'
                          : answers[questions[i].question_id] !== undefined
                          ? 'bg-emerald-500/50'
                          : 'bg-white/20'
                      }`}
                    />
                  ))}
                </div>

                {currentIndex === questions.length - 1 ? (
                  <Button
                    onClick={handleSubmitQuiz}
                    disabled={isSubmitting}
                    className="gap-2 bg-emerald-600 hover:bg-emerald-500"
                  >
                    {isSubmitting ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <>
                        Submit Quiz
                        <CheckCircle className="w-4 h-4" />
                      </>
                    )}
                  </Button>
                ) : (
                  <Button
                    variant="outline"
                    onClick={() => setCurrentIndex((i) => Math.min(questions.length - 1, i + 1))}
                    className="gap-2"
                  >
                    Next
                    <ArrowRight className="w-4 h-4" />
                  </Button>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    );
  }

  // Results mode
  if (quizMode === 'results' && results) {
    const percentage = results.percentage;
    const isPassing = percentage >= 70;

    return (
      <div className="fixed inset-0 z-50 bg-background overflow-y-auto">
        <div className="max-w-4xl mx-auto px-4 py-8">
          {/* Results Header */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="text-center mb-8"
          >
            <div className={`w-24 h-24 mx-auto rounded-full flex items-center justify-center mb-4 ${
              isPassing ? 'bg-emerald-500/20' : 'bg-amber-500/20'
            }`}>
              {isPassing ? (
                <Trophy className="w-12 h-12 text-emerald-400" />
              ) : (
                <RefreshCcw className="w-12 h-12 text-amber-400" />
              )}
            </div>
            <h2 className="text-3xl font-bold mb-2">
              {isPassing ? 'Great Job!' : 'Keep Practicing!'}
            </h2>
            <p className="text-foreground/60">
              You scored {results.correct_count} out of {results.total_questions} questions
            </p>
          </motion.div>

          {/* Score Card */}
          <Card className="border-white/10 bg-white/[0.02] mb-8">
            <CardContent className="p-6">
              <div className="grid grid-cols-3 gap-6 text-center">
                <div>
                  <p className={`text-4xl font-bold ${isPassing ? 'text-emerald-400' : 'text-amber-400'}`}>
                    {percentage.toFixed(0)}%
                  </p>
                  <p className="text-sm text-foreground/50">Score</p>
                </div>
                <div>
                  <p className="text-4xl font-bold text-emerald-400">{results.correct_count}</p>
                  <p className="text-sm text-foreground/50">Correct</p>
                </div>
                <div>
                  <p className="text-4xl font-bold text-red-400">{results.wrong_count}</p>
                  <p className="text-sm text-foreground/50">Wrong</p>
                </div>
              </div>
              {results.time_taken_seconds && (
                <div className="mt-4 pt-4 border-t border-white/10 text-center">
                  <p className="text-foreground/60">
                    Time: {Math.floor(results.time_taken_seconds / 60)}m {results.time_taken_seconds % 60}s
                  </p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Action Buttons */}
          <div className="flex justify-center gap-4 mb-8">
            <Button variant="outline" onClick={handleClose} className="gap-2">
              <ArrowLeft className="w-4 h-4" />
              Back to Questions
            </Button>
            {results.wrong_question_ids.length > 0 && (
              <Button
                onClick={handleStartRevision}
                disabled={isStartingRevision}
                className="gap-2 bg-amber-600 hover:bg-amber-500"
              >
                {isStartingRevision ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <>
                    <RefreshCcw className="w-4 h-4" />
                    Review Wrong Answers ({results.wrong_question_ids.length})
                  </>
                )}
              </Button>
            )}
          </div>

          {/* Detailed Results */}
          <h3 className="text-xl font-semibold mb-4">Question Review</h3>
          <div className="space-y-4">
            {results.results.map((result, index) => (
              <Card
                key={result.question_id}
                className={`border-white/10 ${
                  result.is_correct ? 'bg-emerald-500/5' : 'bg-red-500/5'
                }`}
              >
                <CardContent className="p-4">
                  <div className="flex items-start gap-3">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${
                      result.is_correct ? 'bg-emerald-500/20' : 'bg-red-500/20'
                    }`}>
                      {result.is_correct ? (
                        <CheckCircle className="w-5 h-5 text-emerald-400" />
                      ) : (
                        <XCircle className="w-5 h-5 text-red-400" />
                      )}
                    </div>
                    <div className="flex-1">
                      <p className="font-medium mb-3">
                        {index + 1}. {result.question_text}
                      </p>
                      <div className="space-y-2">
                        {result.options.map((option, optIndex) => {
                          const isCorrect = optIndex === result.correct_answer;
                          const isUserAnswer = optIndex === result.user_answer;
                          const isWrongAnswer = isUserAnswer && !isCorrect;

                          return (
                            <div
                              key={optIndex}
                              className={`flex items-center gap-2 p-2 rounded text-sm ${
                                isCorrect
                                  ? 'bg-emerald-500/20 text-emerald-300'
                                  : isWrongAnswer
                                  ? 'bg-red-500/20 text-red-300'
                                  : 'text-foreground/60'
                              }`}
                            >
                              <span className="w-6 h-6 rounded-full bg-white/10 flex items-center justify-center text-xs">
                                {String.fromCharCode(65 + optIndex)}
                              </span>
                              <span className="flex-1">{option}</span>
                              {isCorrect && <Check className="w-4 h-4" />}
                              {isWrongAnswer && <X className="w-4 h-4" />}
                            </div>
                          );
                        })}
                      </div>
                      {result.explanation && (
                        <div className="mt-3 p-3 rounded-lg bg-white/5 border border-white/10">
                          <p className="text-sm text-foreground/70">
                            <span className="font-medium text-foreground/90">Explanation: </span>
                            {result.explanation}
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Bottom Actions */}
          <div className="mt-8 flex justify-center">
            <Button onClick={handleClose} className="gap-2">
              Done
              <Check className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return null;
}

// ============================================
// Question Sets Grid
// ============================================
function QuestionSetsGrid({
  questionSets,
  loading,
  onSelect,
  onCreate,
  onEdit,
  onDelete,
}: {
  questionSets: QuestionSet[];
  loading: boolean;
  onSelect: (set: QuestionSet) => void;
  onCreate: () => void;
  onEdit: (set: QuestionSet) => void;
  onDelete: (setId: string) => void;
}) {
  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="w-8 h-8 animate-spin text-emerald-400" />
      </div>
    );
  }

  return (
    <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
      {/* Create New Set Card */}
      <motion.div
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        onClick={onCreate}
        className="cursor-pointer"
      >
        <Card className="h-full border-dashed border-white/20 bg-white/[0.02] hover:bg-white/[0.05] hover:border-emerald-500/50 transition-all">
          <CardContent className="flex flex-col items-center justify-center h-full min-h-[180px] text-foreground/60">
            <Plus className="w-10 h-10 mb-3" />
            <span className="font-medium">Create Question Set</span>
          </CardContent>
        </Card>
      </motion.div>

      {/* Question Set Cards */}
      {questionSets.map((set, index) => (
        <motion.div
          key={set.set_id}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: index * 0.05 }}
        >
          <Card className="group h-full border-white/10 bg-white/[0.02] hover:bg-white/[0.05] hover:border-emerald-500/30 transition-all">
            <CardHeader className="pb-2">
              <div className="flex items-start justify-between">
                <div className="flex-1 cursor-pointer" onClick={() => onSelect(set)}>
                  <CardTitle className="text-lg flex items-center gap-2">
                    <FileQuestion className="w-5 h-5 text-emerald-400" />
                    {set.title}
                  </CardTitle>
                  <span className="text-xs text-foreground/50 mt-1 block">
                    {set.questions_count} question{set.questions_count !== 1 ? 's' : ''}
                  </span>
                </div>
                <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation();
                      onEdit(set);
                    }}
                    className="h-8 w-8 p-0"
                  >
                    <Pencil className="w-4 h-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation();
                      onDelete(set.set_id);
                    }}
                    className="h-8 w-8 p-0 text-red-400 hover:text-red-300 hover:bg-red-500/10"
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent className="cursor-pointer pt-0" onClick={() => onSelect(set)}>
              {set.description && (
                <p className="text-sm text-foreground/60 mb-2 line-clamp-2">{set.description}</p>
              )}
              {set.tags && set.tags.length > 0 && (
                <div className="flex flex-wrap gap-1 mb-2">
                  {set.tags.slice(0, 3).map((tag) => (
                    <span
                      key={tag}
                      className="text-xs px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-300"
                    >
                      {tag}
                    </span>
                  ))}
                  {set.tags.length > 3 && (
                    <span className="text-xs text-foreground/40">+{set.tags.length - 3} more</span>
                  )}
                </div>
              )}
              <div className="flex items-center justify-between text-sm text-foreground/50">
                <span>Created {new Date(set.created_at).toLocaleDateString()}</span>
                <ChevronRight className="w-4 h-4" />
              </div>
            </CardContent>
          </Card>
        </motion.div>
      ))}
    </div>
  );
}

// ============================================
// Question Set View
// ============================================
function QuestionSetView({
  questionSet,
  details,
  detailsLoading,
  onBack,
  onCreateQuestion,
  onEditQuestion,
  onDeleteQuestion,
  onStartQuiz,
}: {
  questionSet: QuestionSet;
  details: any;
  detailsLoading: boolean;
  onBack: () => void;
  onCreateQuestion: () => void;
  onEditQuestion: (q: Question) => void;
  onDeleteQuestion: (id: string) => void;
  onStartQuiz: () => void;
}) {
  const questions: Question[] = details?.questions || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button variant="ghost" onClick={onBack} className="gap-2">
              <ArrowLeft className="w-4 h-4" />
              Back
            </Button>
            <div>
              <h2 className="text-2xl font-bold">{questionSet.title}</h2>
              <span className="text-sm text-foreground/50">
                {questionSet.questions_count} question{questionSet.questions_count !== 1 ? 's' : ''}
              </span>
            </div>
          </div>
          <div className="flex gap-2">
            <Button onClick={onCreateQuestion} variant="outline" className="gap-2">
              <Plus className="w-4 h-4" />
              Add Question
            </Button>
            {questions.length > 0 && (
              <Button onClick={onStartQuiz} className="gap-2 bg-emerald-600 hover:bg-emerald-500">
                <Play className="w-4 h-4" />
                Start Quiz
              </Button>
            )}
          </div>
        </div>
        {(questionSet.description || (questionSet.tags && questionSet.tags.length > 0)) && (
          <div className="ml-[52px] space-y-2">
            {questionSet.description && (
              <p className="text-foreground/70">{questionSet.description}</p>
            )}
            {questionSet.tags && questionSet.tags.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {questionSet.tags.map((tag) => (
                  <span
                    key={tag}
                    className="text-xs px-2 py-1 rounded-md bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Questions List */}
      {detailsLoading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 animate-spin text-emerald-400" />
        </div>
      ) : questions.length === 0 ? (
        <Card className="border-white/10 bg-white/[0.02]">
          <CardContent className="flex flex-col items-center justify-center py-16 text-foreground/60">
            <HelpCircle className="w-12 h-12 mb-4 opacity-50" />
            <p className="text-lg font-medium mb-2">No questions yet</p>
            <p className="text-sm mb-4">Add your first question to start building your quiz</p>
            <Button onClick={onCreateQuestion} className="gap-2">
              <Plus className="w-4 h-4" />
              Add Question
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {questions.map((question, index) => (
            <motion.div
              key={question.question_id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.2, delay: index * 0.03 }}
            >
              <Card className="group border-white/10 bg-white/[0.02] hover:bg-white/[0.04] transition-all">
                <CardContent className="p-4">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <div className="flex items-start gap-3 mb-3">
                        <span className="shrink-0 w-7 h-7 rounded-full bg-emerald-500/20 flex items-center justify-center text-sm font-medium text-emerald-400">
                          {index + 1}
                        </span>
                        <p className="font-medium">{question.question_text}</p>
                      </div>
                      <div className="grid sm:grid-cols-2 gap-2 ml-10">
                        {question.options.map((option, optIndex) => (
                          <div
                            key={optIndex}
                            className={`flex items-center gap-2 p-2 rounded text-sm ${
                              optIndex === question.correct_answer
                                ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                                : 'bg-white/5 text-foreground/70'
                            }`}
                          >
                            <span className="w-5 h-5 rounded-full bg-white/10 flex items-center justify-center text-xs shrink-0">
                              {String.fromCharCode(65 + optIndex)}
                            </span>
                            <span className="flex-1 truncate">{option}</span>
                            {optIndex === question.correct_answer && (
                              <CheckCircle className="w-4 h-4 shrink-0" />
                            )}
                          </div>
                        ))}
                      </div>
                      {question.explanation && (
                        <p className="text-xs text-foreground/50 mt-2 ml-10">
                          💡 {question.explanation}
                        </p>
                      )}
                    </div>
                    <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onEditQuestion(question)}
                        className="h-8 w-8 p-0"
                      >
                        <Pencil className="w-4 h-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onDeleteQuestion(question.question_id)}
                        className="h-8 w-8 p-0 text-red-400 hover:text-red-300 hover:bg-red-500/10"
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
  );
}

