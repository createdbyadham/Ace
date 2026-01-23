import { useNavigate } from '@tanstack/react-router';
import { useCallback, useState } from 'react';
import { motion } from 'framer-motion';
import { useDropzone } from 'react-dropzone';
import {
  ArrowLeft,
  BookOpen,
  Brain,
  CheckCircle,
  ChevronRight,
  Clock,
  FileText,
  FolderOpen,
  Frown,
  Layers,
  Loader2,
  Meh,
  Pencil,
  Plus,
  Sparkles,
  ThumbsUp,
  Trash2,
  Upload,
  X,
  Zap,
} from 'lucide-react';
import { toast } from 'sonner';
import type {
  CardCreate,
  Deck,
  DeckCreate,
  Card as FlashcardType,
  StudyCard,
  StudyMode,
  ReviewResponse,
} from '@/components/flashcards/types';
import {
  useCards,
  useDecks,
  useDeckMutations,
  useCardMutations,
  useAIGeneration,
  useDeckStats,
  useStudySession,
  useStudyMutations,
  useAvailableModels,
} from '@/components/flashcards/useFlashcards';
import { CardDialog, DeckDialog, DeleteConfirmDialog } from '@/components/flashcards/components/FlashcardDialogs';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import Particles from '@/components/ui/Particles';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Textarea } from '@/components/ui/textarea';
import { Footer } from '@/components/layout/Footer';
import { Navbar } from '@/components/layout/Navbar';
import { useAuth } from '@/context/AuthContext';

export default function FlashcardsPage() {
  const navigate = useNavigate();
  const { isAuthenticated, user, logout } = useAuth();

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    navigate({ to: '/login' });
    return null;
  }

  return <FlashcardsContent user={user} logout={logout} />;
}

function FlashcardsContent({ user, logout }: { user: any; logout: () => void }) {
  const [activeTab, setActiveTab] = useState('decks');
  const [selectedDeck, setSelectedDeck] = useState<Deck | null>(null);

  // Dialog states
  const [showCreateDeck, setShowCreateDeck] = useState(false);
  const [showEditDeck, setShowEditDeck] = useState(false);
  const [showDeleteDeck, setShowDeleteDeck] = useState(false);
  const [showCreateCard, setShowCreateCard] = useState(false);
  const [showEditCard, setShowEditCard] = useState(false);
  const [showDeleteCard, setShowDeleteCard] = useState(false);
  const [editingDeck, setEditingDeck] = useState<Deck | null>(null);
  const [editingCard, setEditingCard] = useState<FlashcardType | null>(null);
  const [deletingDeckId, setDeletingDeckId] = useState<string | null>(null);
  const [deletingCardId, setDeletingCardId] = useState<string | null>(null);

  // AI Generation state
  const [aiFiles, setAiFiles] = useState<Array<File>>([]);
  const [aiDeckTitle, setAiDeckTitle] = useState('');
  const [aiDeckDescription, setAiDeckDescription] = useState('');
  const [aiNumCards, setAiNumCards] = useState(10);
  const [aiModel, setAiModel] = useState<'openai' | 'ace'>('openai');

  // Queries
  const { data: decks = [], isLoading: decksLoading } = useDecks();
  const { data: availableModels } = useAvailableModels();
  const { data: cards = [], isLoading: cardsLoading } = useCards(selectedDeck?.deck_id);

  // Mutations (with toast notifications built-in)
  const { createDeck, updateDeck, deleteDeck, isCreating: isDeckCreating, isUpdating: isDeckUpdating, isDeleting: isDeckDeleting } = useDeckMutations();
  const { createCard, updateCard, deleteCard, isCreating: isCardCreating, isUpdating: isCardUpdating, isDeleting: isCardDeleting } = useCardMutations();
  const { generateFlashcards, isGenerating } = useAIGeneration();

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
  const handleGenerateFlashcards = async () => {
    if (aiFiles.length === 0) {
      toast.error('Please upload at least one PDF file');
      return;
    }
    if (!aiDeckTitle.trim()) {
      toast.error('Please enter a deck title');
      return;
    }
    if (aiNumCards < 1 || aiNumCards > 100) {
      toast.error('Number of cards must be between 1 and 100');
      return;
    }

    await generateFlashcards(
      {
        files: aiFiles,
        numCards: aiNumCards,
        deckTitle: aiDeckTitle,
        deckDescription: aiDeckDescription || undefined,
        model: aiModel,
      },
      {
        onSuccess: () => {
          setAiFiles([]);
          setAiDeckTitle('');
          setAiDeckDescription('');
          setAiNumCards(10);
          setActiveTab('decks');
        },
      }
    );
  };

  const handleCreateDeck = (data: DeckCreate) => {
    createDeck(data, { onSuccess: () => setShowCreateDeck(false) });
  };

  const handleUpdateDeck = (deckId: string, data: DeckCreate) => {
    updateDeck(deckId, data, {
      onSuccess: () => {
        setShowEditDeck(false);
        setEditingDeck(null);
      },
    });
  };

  const handleDeleteDeck = () => {
    if (!deletingDeckId) return;
    deleteDeck(deletingDeckId, {
      onSuccess: () => {
        setShowDeleteDeck(false);
        if (selectedDeck?.deck_id === deletingDeckId) {
          setSelectedDeck(null);
        }
        setDeletingDeckId(null);
      },
    });
  };

  const handleCreateCard = (data: CardCreate) => {
    createCard(data, { onSuccess: () => setShowCreateCard(false) });
  };

  const handleUpdateCard = (cardId: string, data: CardCreate) => {
    updateCard(cardId, data, {
      onSuccess: () => {
        setShowEditCard(false);
        setEditingCard(null);
      },
    });
  };

  const handleDeleteCard = () => {
    if (!deletingCardId) return;
    deleteCard(deletingCardId, {
      onSuccess: () => {
        setShowDeleteCard(false);
        setDeletingCardId(null);
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
              <h1 className="text-3xl font-bold">Flashcards</h1>
              <p className="text-foreground/60 mt-1">Create, manage, and study your flashcards</p>
            </div>
          </div>

          {/* Main Tabs */}
          <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
            <TabsList className="bg-white/5 border border-white/10">
              <TabsTrigger value="decks" className="data-[state=active]:bg-indigo-600">
                <FolderOpen className="w-4 h-4 mr-2" />
                My Decks
              </TabsTrigger>
              <TabsTrigger value="generate" className="data-[state=active]:bg-purple-600">
                <Sparkles className="w-4 h-4 mr-2" />
                AI Generate
              </TabsTrigger>
            </TabsList>

            {/* Decks Tab */}
            <TabsContent value="decks" className="space-y-6">
              {selectedDeck ? (
                <DeckView
                  deck={selectedDeck}
                  cards={cards}
                  cardsLoading={cardsLoading}
                  onBack={() => setSelectedDeck(null)}
                  onCreateCard={() => setShowCreateCard(true)}
                  onEditCard={(card) => {
                    setEditingCard(card);
                    setShowEditCard(true);
                  }}
                  onDeleteCard={(cardId) => {
                    setDeletingCardId(cardId);
                    setShowDeleteCard(true);
                  }}
                />
              ) : (
                <DecksGrid
                  decks={decks}
                  loading={decksLoading}
                  onSelect={setSelectedDeck}
                  onCreate={() => setShowCreateDeck(true)}
                  onEdit={(deck) => {
                    setEditingDeck(deck);
                    setShowEditDeck(true);
                  }}
                  onDelete={(deckId) => {
                    setDeletingDeckId(deckId);
                    setShowDeleteDeck(true);
                  }}
                />
              )}
            </TabsContent>

            {/* AI Generate Tab */}
            <TabsContent value="generate">
              <Card className="border-white/10 bg-white/[0.02]">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Sparkles className="w-5 h-5 text-purple-400" />
                    Generate Flashcards with AI
                  </CardTitle>
                  <CardDescription>
                    Upload PDF files and let AI create flashcards for you automatically
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
                          ? 'border-purple-500 bg-purple-500/10'
                          : 'border-white/20 hover:border-white/40 hover:bg-white/5'
                      }`}
                    >
                      <input {...getInputProps()} />
                      <Upload className="w-10 h-10 mx-auto mb-3 text-foreground/40" />
                      {isDragActive ? (
                        <p className="text-purple-400">Drop your PDFs here...</p>
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
                              <FileText className="w-5 h-5 text-purple-400" />
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

                  {/* Deck Details */}
                  <div className="grid md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="deck-title">Deck Title</Label>
                      <Input
                        id="deck-title"
                        placeholder="e.g., Biology Chapter 5"
                        value={aiDeckTitle}
                        onChange={(e) => setAiDeckTitle(e.target.value)}
                        className="bg-white/5 border-white/10"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="num-cards">Number of Cards</Label>
                      <Input
                        id="num-cards"
                        type="number"
                        min={1}
                        max={100}
                        value={aiNumCards}
                        onChange={(e) => setAiNumCards(parseInt(e.target.value) || 10)}
                        className="bg-white/5 border-white/10"
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="deck-desc">Description (optional)</Label>
                    <Textarea
                      id="deck-desc"
                      placeholder="Add a description for your deck..."
                      value={aiDeckDescription}
                      onChange={(e) => setAiDeckDescription(e.target.value)}
                      className="bg-white/5 border-white/10 min-h-[80px]"
                    />
                  </div>

                  {/* Model Selector */}
                  <div className="space-y-3">
                    <Label>AI Model</Label>
                    <div className="flex gap-3">
                      <button
                        type="button"
                        onClick={() => setAiModel('openai')}
                        className={`flex-1 p-4 rounded-xl border-2 transition-all ${
                          aiModel === 'openai'
                            ? 'border-purple-500 bg-purple-500/10'
                            : 'border-white/10 bg-white/[0.02] hover:border-white/20'
                        }`}
                      >
                        <div className="flex items-center gap-3">
                          <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                            aiModel === 'openai' ? 'bg-purple-500/20' : 'bg-white/5'
                          }`}>
                            <svg className="w-6 h-6" viewBox="0 0 24 24" fill="currentColor">
                              <path d="M22.2819 9.8211a5.9847 5.9847 0 0 0-.5157-4.9108 6.0462 6.0462 0 0 0-6.5098-2.9A6.0651 6.0651 0 0 0 4.9807 4.1818a5.9847 5.9847 0 0 0-3.9977 2.9 6.0462 6.0462 0 0 0 .7427 7.0966 5.98 5.98 0 0 0 .511 4.9107 6.051 6.051 0 0 0 6.5146 2.9001A5.9847 5.9847 0 0 0 13.2599 24a6.0557 6.0557 0 0 0 5.7718-4.2058 5.9894 5.9894 0 0 0 3.9977-2.9001 6.0557 6.0557 0 0 0-.7475-7.0729zm-9.022 12.6081a4.4755 4.4755 0 0 1-2.8764-1.0408l.1419-.0804 4.7783-2.7582a.7948.7948 0 0 0 .3927-.6813v-6.7369l2.02 1.1686a.071.071 0 0 1 .038.052v5.5826a4.504 4.504 0 0 1-4.4945 4.4944zm-9.6607-4.1254a4.4708 4.4708 0 0 1-.5346-3.0137l.142.0852 4.783 2.7582a.7712.7712 0 0 0 .7806 0l5.8428-3.3685v2.3324a.0804.0804 0 0 1-.0332.0615L9.74 19.9502a4.4992 4.4992 0 0 1-6.1408-1.6464zM2.3408 7.8956a4.485 4.485 0 0 1 2.3655-1.9728V11.6a.7664.7664 0 0 0 .3879.6765l5.8144 3.3543-2.0201 1.1685a.0757.0757 0 0 1-.071 0l-4.8303-2.7865A4.504 4.504 0 0 1 2.3408 7.8956zm16.5963 3.8558L13.1038 8.364 15.1192 7.2a.0757.0757 0 0 1 .071 0l4.8303 2.7913a4.4944 4.4944 0 0 1-.6765 8.1042v-5.6772a.79.79 0 0 0-.407-.667zm2.0107-3.0231l-.142-.0852-4.7735-2.7818a.7759.7759 0 0 0-.7854 0L9.409 9.2297V6.8974a.0662.0662 0 0 1 .0284-.0615l4.8303-2.7866a4.4992 4.4992 0 0 1 6.6802 4.66zM8.3065 12.863l-2.02-1.1638a.0804.0804 0 0 1-.038-.0567V6.0742a4.4992 4.4992 0 0 1 7.3757-3.4537l-.142.0805L8.704 5.459a.7948.7948 0 0 0-.3927.6813zm1.0976-2.3654l2.602-1.4998 2.6069 1.4998v2.9994l-2.5974 1.4997-2.6067-1.4997Z"/>
                            </svg>
                          </div>
                          <div className="text-left">
                            <p className="font-medium">ChatGPT</p>
                            <p className="text-xs text-foreground/50">OpenAI API</p>
                          </div>
                        </div>
                      </button>
                      <button
                        type="button"
                        onClick={() => setAiModel('ace')}
                        disabled={!availableModels?.ace_available}
                        className={`flex-1 p-4 rounded-xl border-2 transition-all ${
                          aiModel === 'ace'
                            ? 'border-indigo-500 bg-indigo-500/10'
                            : availableModels?.ace_available
                              ? 'border-white/10 bg-white/[0.02] hover:border-white/20'
                              : 'border-white/5 bg-white/[0.01] opacity-50 cursor-not-allowed'
                        }`}
                      >
                        <div className="flex items-center gap-3">
                          <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                            aiModel === 'ace' ? 'bg-indigo-500/20' : 'bg-white/5'
                          }`}>
                            <Sparkles className="w-6 h-6" />
                          </div>
                          <div className="text-left">
                            <p className="font-medium">Ace Model</p>
                            <p className="text-xs text-foreground/50">
                              {availableModels?.ace_available ? 'Fine-tuned' : 'Requires GPU'}
                            </p>
                          </div>
                        </div>
                      </button>
                    </div>
                    <p className="text-xs text-foreground/40">
                      {aiModel === 'ace' 
                        ? 'Using your custom fine-tuned model for generation'
                        : 'Using OpenAI ChatGPT for generation'}
                    </p>
                  </div>

                  <Button
                    onClick={handleGenerateFlashcards}
                    disabled={isGenerating || aiFiles.length === 0}
                    className="w-full bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500"
                  >
                    {isGenerating ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Generating...
                      </>
                    ) : (
                      <>
                        <Sparkles className="w-4 h-4 mr-2" />
                        Generate Flashcards
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
      <DeckDialog
        open={showCreateDeck}
        onOpenChange={setShowCreateDeck}
        onSubmit={handleCreateDeck}
        isLoading={isDeckCreating}
      />

      {editingDeck && (
        <DeckDialog
          open={showEditDeck}
          onOpenChange={(open) => {
            setShowEditDeck(open);
            if (!open) setEditingDeck(null);
          }}
          deck={editingDeck}
          onSubmit={(data) => handleUpdateDeck(editingDeck.deck_id, data)}
          isLoading={isDeckUpdating}
        />
      )}

      {selectedDeck && (
        <CardDialog
          open={showCreateCard}
          onOpenChange={setShowCreateCard}
          deckId={selectedDeck.deck_id}
          onSubmit={handleCreateCard}
          isLoading={isCardCreating}
        />
      )}

      {editingCard && (
        <CardDialog
          open={showEditCard}
          onOpenChange={(open) => {
            setShowEditCard(open);
            if (!open) setEditingCard(null);
          }}
          deckId={editingCard.deck_id || selectedDeck?.deck_id}
          card={editingCard}
          onSubmit={(data) => handleUpdateCard(editingCard.card_id, data)}
          isLoading={isCardUpdating}
        />
      )}

      <DeleteConfirmDialog
        open={showDeleteDeck}
        onOpenChange={setShowDeleteDeck}
        onConfirm={handleDeleteDeck}
        isLoading={isDeckDeleting}
        title="Delete Deck"
        description="Are you sure you want to delete this deck? All cards in this deck will also be deleted. This action cannot be undone."
      />

      <DeleteConfirmDialog
        open={showDeleteCard}
        onOpenChange={setShowDeleteCard}
        onConfirm={handleDeleteCard}
        isLoading={isCardDeleting}
        title="Delete Card"
        description="Are you sure you want to delete this card? This action cannot be undone."
      />
    </div>
  );
}

// ============================================
// Decks Grid Component
// ============================================
function DecksGrid({
  decks,
  loading,
  onSelect,
  onCreate,
  onEdit,
  onDelete,
}: {
  decks: Array<Deck>;
  loading: boolean;
  onSelect: (deck: Deck) => void;
  onCreate: () => void;
  onEdit: (deck: Deck) => void;
  onDelete: (deckId: string) => void;
}) {
  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-400" />
      </div>
    );
  }

  return (
    <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
      {/* Create New Deck Card */}
      <motion.div
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        onClick={onCreate}
        className="cursor-pointer"
      >
        <Card className="h-full border-dashed border-white/20 bg-white/[0.02] hover:bg-white/[0.05] hover:border-indigo-500/50 transition-all">
          <CardContent className="flex flex-col items-center justify-center h-full min-h-[180px] text-foreground/60">
            <Plus className="w-10 h-10 mb-3" />
            <span className="font-medium">Create New Deck</span>
          </CardContent>
        </Card>
      </motion.div>

      {/* Deck Cards */}
      {decks.map((deck, index) => (
        <motion.div
          key={deck.deck_id}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: index * 0.05 }}
        >
          <Card className="group h-full border-white/10 bg-white/[0.02] hover:bg-white/[0.05] hover:border-indigo-500/30 transition-all">
            <CardHeader className="pb-2">
              <div className="flex items-start justify-between">
                <div className="flex-1 cursor-pointer" onClick={() => onSelect(deck)}>
                  <CardTitle className="text-lg flex items-center gap-2">
                    <Layers className="w-5 h-5 text-indigo-400" />
                    {deck.title}
                  </CardTitle>
                  {deck.language && (
                    <span className="text-xs text-foreground/50 mt-1 block">{deck.language}</span>
                  )}
                </div>
                <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation();
                      onEdit(deck);
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
                      onDelete(deck.deck_id);
                    }}
                    className="h-8 w-8 p-0 text-red-400 hover:text-red-300 hover:bg-red-500/10"
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent className="cursor-pointer pt-0" onClick={() => onSelect(deck)}>
              {deck.description && (
                <p className="text-sm text-foreground/60 mb-2 line-clamp-2">{deck.description}</p>
              )}
              {deck.tags && deck.tags.length > 0 && (
                <div className="flex flex-wrap gap-1 mb-2">
                  {deck.tags.slice(0, 3).map((tag) => (
                    <span
                      key={tag}
                      className="text-xs px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-300"
                    >
                      {tag}
                    </span>
                  ))}
                  {deck.tags.length > 3 && (
                    <span className="text-xs text-foreground/40">+{deck.tags.length - 3} more</span>
                  )}
                </div>
              )}
              <div className="flex items-center justify-between text-sm text-foreground/50">
                <span>Created {new Date(deck.created_at).toLocaleDateString()}</span>
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
// Deck View Component (Cards inside a deck)
// ============================================
function DeckView({
  deck,
  cards,
  cardsLoading,
  onBack,
  onCreateCard,
  onEditCard,
  onDeleteCard,
}: {
  deck: Deck;
  cards: Array<FlashcardType>;
  cardsLoading: boolean;
  onBack: () => void;
  onCreateCard: () => void;
  onEditCard: (card: FlashcardType) => void;
  onDeleteCard: (cardId: string) => void;
}) {
  // Study flow state
  const [studyMode, setStudyMode] = useState<StudyMode | null>(null);
  const [sessionCards, setSessionCards] = useState<StudyCard[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isFlipped, setIsFlipped] = useState(false);
  const [sessionComplete, setSessionComplete] = useState(false);
  const [cardsReviewed, setCardsReviewed] = useState(0);
  const [sessionStarted, setSessionStarted] = useState(false);

  // Fetch deck stats
  const { data: stats, isLoading: statsLoading } = useDeckStats(deck.deck_id);

  // Fetch study session when in study mode (only used to load initial cards)
  const { data: studySession, isLoading: sessionLoading } = useStudySession(
    studyMode && !sessionStarted ? deck.deck_id : undefined,
    studyMode || 'review'
  );

  // Review submission and snooze
  const { submitReview, snoozeCard, isSubmitting, isSnoozeing, invalidateStudyQueries } = useStudyMutations();

  // Store session cards in local state when loaded
  if (studySession && studyMode && !sessionStarted && studySession.cards.length >= 0) {
    setSessionCards(studySession.cards);
    setSessionStarted(true);
  }

  const currentCard = sessionCards[currentIndex];

  const handleStartStudy = (mode: StudyMode) => {
    setStudyMode(mode);
    setSessionCards([]);
    setCurrentIndex(0);
    setIsFlipped(false);
    setSessionComplete(false);
    setCardsReviewed(0);
    setSessionStarted(false);
  };

  const handleExitStudy = () => {
    setStudyMode(null);
    setSessionCards([]);
    setCurrentIndex(0);
    setIsFlipped(false);
    setSessionComplete(false);
    setSessionStarted(false);
    // Refresh stats when exiting
    invalidateStudyQueries();
  };

  const handleResponse = async (response: ReviewResponse) => {
    if (!currentCard || !studyMode || isSubmitting) return;

    await submitReview(currentCard.card_id, response, studyMode);
    setCardsReviewed((prev) => prev + 1);

    // Move to next card
    setIsFlipped(false);
    setTimeout(() => {
      if (currentIndex + 1 >= sessionCards.length) {
        setSessionComplete(true);
      } else {
        setCurrentIndex((prev) => prev + 1);
      }
    }, 150);
  };

  const handleSnooze = async (hours: number = 24) => {
    if (!currentCard || isSnoozeing) return;

    await snoozeCard(currentCard.card_id, hours);
    
    // Remove the snoozed card from session and move to next
    setIsFlipped(false);
    const remainingCards = sessionCards.filter((_, i) => i !== currentIndex);
    setSessionCards(remainingCards);
    
    if (remainingCards.length === 0) {
      setSessionComplete(true);
    } else if (currentIndex >= remainingCards.length) {
      setCurrentIndex(remainingCards.length - 1);
    }
  };

  // Study Session UI
  if (studyMode) {
    // Loading session
    if (sessionLoading) {
      return (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 animate-spin text-indigo-400" />
          <span className="ml-3 text-foreground/60">Loading cards...</span>
        </div>
      );
    }

    // Session complete
    if (sessionComplete || sessionCards.length === 0) {
      return (
        <div className="space-y-6">
          <Card className="border-white/10 bg-gradient-to-br from-green-500/10 to-emerald-500/10">
            <CardContent className="flex flex-col items-center justify-center py-16">
              <CheckCircle className="w-16 h-16 text-green-400 mb-4" />
              <h3 className="text-2xl font-bold mb-2">
                {sessionCards.length === 0 ? 'No Cards to Review!' : 'Session Complete!'}
              </h3>
              <p className="text-foreground/60 mb-6">
                {sessionCards.length === 0
                  ? studyMode === 'review'
                    ? "You're all caught up! No cards due for review."
                    : 'This deck has no cards yet.'
                  : `You reviewed ${cardsReviewed} card${cardsReviewed !== 1 ? 's' : ''}.`}
              </p>
              <Button onClick={handleExitStudy} className="gap-2">
                <ArrowLeft className="w-4 h-4" />
                Back to Deck
              </Button>
            </CardContent>
          </Card>
        </div>
      );
    }

    // Guard: Wait for current card to be available
    if (!currentCard) {
      return (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 animate-spin text-indigo-400" />
        </div>
      );
    }

    // Active study session
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <Button variant="ghost" onClick={handleExitStudy} className="gap-2">
            <ArrowLeft className="w-4 h-4" />
            Exit Study
          </Button>
          <div className="flex items-center gap-4">
            {studyMode === 'review' && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleSnooze(24)}
                disabled={isSnoozeing}
                className="gap-2 border-blue-500/30 hover:bg-blue-500/10 hover:border-blue-500/50 text-blue-400"
              >
                <Clock className="w-4 h-4" />
                Snooze 24h
              </Button>
            )}
            <span className="text-sm text-foreground/50">
              {studyMode === 'review' ? 'Review Mode' : 'Practice Mode'}
            </span>
            <span className="text-foreground/60">
              Card {currentIndex + 1} of {sessionCards.length}
            </span>
          </div>
        </div>

        {/* Card display */}
        <div className="flex justify-center">
          <motion.div
            className="w-full max-w-lg perspective-1000"
            onClick={() => setIsFlipped(!isFlipped)}
          >
            <motion.div
              className="relative w-full h-80 cursor-pointer preserve-3d"
              animate={{ rotateY: isFlipped ? 180 : 0 }}
              transition={{ duration: 0.4 }}
              style={{ transformStyle: 'preserve-3d' }}
            >
              {/* Front */}
              <div
                className="absolute inset-0 rounded-2xl bg-gradient-to-br from-indigo-600/20 to-purple-600/20 border border-white/10 p-6 flex flex-col items-center justify-center"
                style={{ backfaceVisibility: 'hidden' }}
              >
                <span className="text-xs text-foreground/50 mb-4">QUESTION</span>
                <p className="text-xl text-center">{currentCard.content.front}</p>
                <span className="text-xs text-foreground/40 mt-4">Click to reveal answer</span>
              </div>

              {/* Back */}
              <div
                className="absolute inset-0 rounded-2xl bg-gradient-to-br from-purple-600/20 to-pink-600/20 border border-white/10 p-6 flex flex-col items-center justify-center"
                style={{ backfaceVisibility: 'hidden', transform: 'rotateY(180deg)' }}
              >
                <span className="text-xs text-foreground/50 mb-4">ANSWER</span>
                <p className="text-xl text-center">{currentCard.content.back}</p>
              </div>
            </motion.div>
          </motion.div>
        </div>

        {/* Response buttons - only show when flipped */}
        {isFlipped && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex justify-center gap-3"
          >
            <Button
              variant="outline"
              onClick={() => handleResponse('forgot')}
              disabled={isSubmitting}
              className="gap-2 border-red-500/30 hover:bg-red-500/10 hover:border-red-500/50 text-red-400"
            >
              <Frown className="w-4 h-4" />
              Forgot
            </Button>
            <Button
              variant="outline"
              onClick={() => handleResponse('meh')}
              disabled={isSubmitting}
              className="gap-2 border-yellow-500/30 hover:bg-yellow-500/10 hover:border-yellow-500/50 text-yellow-400"
            >
              <Meh className="w-4 h-4" />
              Meh
            </Button>
            <Button
              onClick={() => handleResponse('got_it')}
              disabled={isSubmitting}
              className="gap-2 bg-green-600 hover:bg-green-500"
            >
              <ThumbsUp className="w-4 h-4" />
              Got it!
            </Button>
          </motion.div>
        )}
      </div>
    );
  }

  // Default deck view with study prompt
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
              <h2 className="text-2xl font-bold">{deck.title}</h2>
              {deck.language && (
                <span className="text-sm text-foreground/50">{deck.language}</span>
              )}
            </div>
          </div>
          <Button onClick={onCreateCard} className="gap-2 bg-indigo-600 hover:bg-indigo-500">
            <Plus className="w-4 h-4" />
            Add Card
          </Button>
        </div>
        {(deck.description || (deck.tags && deck.tags.length > 0)) && (
          <div className="ml-[52px] space-y-2">
            {deck.description && (
              <p className="text-foreground/70">{deck.description}</p>
            )}
            {deck.tags && deck.tags.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {deck.tags.map((tag) => (
                  <span
                    key={tag}
                    className="text-xs px-2 py-1 rounded-md bg-indigo-500/20 text-indigo-300 border border-indigo-500/30"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Study Prompt Card */}
      {statsLoading ? (
        <div className="flex items-center justify-center py-8">
          <Loader2 className="w-6 h-6 animate-spin text-indigo-400" />
        </div>
      ) : stats && stats.total_cards > 0 ? (
        <Card className={`border-white/10 ${stats.due_now > 0 ? 'bg-gradient-to-br from-orange-500/10 to-amber-500/10 border-orange-500/20' : 'bg-white/[0.02]'}`}>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                {stats.due_now > 0 ? (
                  <>
                    <div className="p-3 rounded-full bg-orange-500/20">
                      <Zap className="w-6 h-6 text-orange-400" />
                    </div>
                    <div>
                      <p className="font-semibold text-lg">
                        {stats.due_now} card{stats.due_now !== 1 ? 's' : ''} to review!
                      </p>
                      <p className="text-sm text-foreground/60">
                        Keep your streak going by reviewing now
                      </p>
                    </div>
                  </>
                ) : (
                  <>
                    <div className="p-3 rounded-full bg-green-500/20">
                      <CheckCircle className="w-6 h-6 text-green-400" />
                    </div>
                    <div>
                      <p className="font-semibold text-lg">All caught up!</p>
                      <p className="text-sm text-foreground/60">
                        No cards due for review right now
                      </p>
                    </div>
                  </>
                )}
              </div>
              <div className="flex gap-2">
                {stats.due_now > 0 && (
                  <Button
                    onClick={() => handleStartStudy('review')}
                    className="gap-2 bg-orange-600 hover:bg-orange-500"
                  >
                    <Brain className="w-4 h-4" />
                    Review Weak
                  </Button>
                )}
                <Button
                  variant="outline"
                  onClick={() => handleStartStudy('all')}
                  className="gap-2"
                >
                  <BookOpen className="w-4 h-4" />
                  Practice All
                </Button>
              </div>
            </div>

            {/* Stats row */}
            <div className="grid grid-cols-4 gap-4 mt-6 pt-4 border-t border-white/10">
              <div className="text-center">
                <p className="text-2xl font-bold text-indigo-400">{stats.total_cards}</p>
                <p className="text-xs text-foreground/50">Total</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-green-400">{stats.mastered}</p>
                <p className="text-xs text-foreground/50">Mastered</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-yellow-400">{stats.learning}</p>
                <p className="text-xs text-foreground/50">Learning</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-purple-400">{stats.new}</p>
                <p className="text-xs text-foreground/50">New</p>
              </div>
            </div>
          </CardContent>
        </Card>
      ) : null}

      {/* Cards List */}
      {cardsLoading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 animate-spin text-indigo-400" />
        </div>
      ) : cards.length === 0 ? (
        <Card className="border-white/10 bg-white/[0.02]">
          <CardContent className="flex flex-col items-center justify-center py-16 text-foreground/60">
            <Layers className="w-12 h-12 mb-4 opacity-50" />
            <p className="text-lg font-medium mb-2">No cards yet</p>
            <p className="text-sm mb-4">Add your first card to start studying</p>
            <Button onClick={onCreateCard} className="gap-2">
              <Plus className="w-4 h-4" />
              Add Card
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {cards.map((card, index) => (
            <motion.div
              key={card.card_id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.2, delay: index * 0.03 }}
            >
              <Card className="group border-white/10 bg-white/[0.02] hover:bg-white/[0.04] transition-all">
                <CardContent className="p-4">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 grid md:grid-cols-2 gap-4">
                      <div>
                        <span className="text-xs text-foreground/50 uppercase tracking-wider">
                          Front
                        </span>
                        <p className="mt-1">{card.content.front}</p>
                      </div>
                      <div>
                        <span className="text-xs text-foreground/50 uppercase tracking-wider">
                          Back
                        </span>
                        <p className="mt-1">{card.content.back}</p>
                      </div>
                    </div>
                    <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onEditCard(card)}
                        className="h-8 w-8 p-0"
                      >
                        <Pencil className="w-4 h-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onDeleteCard(card.card_id)}
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
