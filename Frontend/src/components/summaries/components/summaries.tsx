import { useNavigate } from '@tanstack/react-router';
import { useCallback, useState } from 'react';
import { motion } from 'framer-motion';
import { useDropzone } from 'react-dropzone';
import { ArrowLeft, BookOpen, Calendar, ChevronRight, Clock, FileText, Key,Loader2, Pencil, Plus, Search, Sparkles, Trash2, Upload, X
} from 'lucide-react';
import { toast } from 'sonner';
import type { Summary, SummaryLength } from '@/components/summaries/types';
import { useSummaries, useSummaryMutations, useAISummaryGeneration } from '@/components/summaries/useSummaries';
import { DeleteConfirmDialog, EditSummaryDialog } from '@/components/summaries/components/SummaryDialogs';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import Particles from '@/components/ui/Particles';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Footer } from '@/components/layout/Footer';
import { Navbar } from '@/components/layout/Navbar';
import { useAuth } from '@/context/AuthContext';

export default function SummariesPage() {
  const navigate = useNavigate();
  const { isAuthenticated, user, logout } = useAuth();

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    navigate({ to: '/login' });
    return null;
  }

  return <SummariesContent user={user} logout={logout} />;
}

function SummariesContent({ user, logout }: { user: any; logout: () => void }) {
  const [activeTab, setActiveTab] = useState('summaries');
  const [selectedSummary, setSelectedSummary] = useState<Summary | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  // Dialog states
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [editingSummary, setEditingSummary] = useState<Summary | null>(null);
  const [deletingSummaryId, setDeletingSummaryId] = useState<string | null>(null);

  // AI Generation state
  const [aiFiles, setAiFiles] = useState<Array<File>>([]);
  const [aiTitle, setAiTitle] = useState('');
  const [aiLength, setAiLength] = useState<SummaryLength>('medium');

  // Queries
  const { data: summariesData, isLoading: summariesLoading } = useSummaries(searchQuery || undefined);

  // Mutations
  const { updateSummary, deleteSummary, isUpdating, isDeleting } = useSummaryMutations();
  const { generateSummary, isGenerating } = useAISummaryGeneration();

  const summaries = summariesData?.summaries || [];

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
  const handleGenerateSummary = async () => {
    if (aiFiles.length === 0) {
      toast.error('Please upload at least one PDF file');
      return;
    }
    if (!aiTitle.trim()) {
      toast.error('Please enter a title');
      return;
    }

    await generateSummary(
      {
        files: aiFiles,
        title: aiTitle,
        summaryLength: aiLength,
      },
      {
        onSuccess: () => {
          setAiFiles([]);
          setAiTitle('');
          setAiLength('medium');
          setActiveTab('summaries');
        },
      }
    );
  };

  const handleUpdateSummary = (summaryId: string, data: { title?: string; content?: string }) => {
    updateSummary(summaryId, data, {
      onSuccess: () => {
        setShowEditDialog(false);
        setEditingSummary(null);
        // Update selected summary if viewing it
        if (selectedSummary?.summary_id === summaryId) {
          setSelectedSummary({
            ...selectedSummary,
            ...data,
          });
        }
      },
    });
  };

  const handleDeleteSummary = () => {
    if (!deletingSummaryId) return;
    deleteSummary(deletingSummaryId, {
      onSuccess: () => {
        setShowDeleteDialog(false);
        if (selectedSummary?.summary_id === deletingSummaryId) {
          setSelectedSummary(null);
        }
        setDeletingSummaryId(null);
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
          particleColors={['#10b981', '#14b8a6', '#06b6d4']}
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
              <h1 className="text-3xl font-bold">Summaries</h1>
              <p className="text-foreground/60 mt-1">Generate AI summaries from your lecture materials</p>
            </div>
          </div>

          {/* Main Tabs */}
          <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
            <TabsList className="bg-white/5 border border-white/10">
              <TabsTrigger value="summaries" className="data-[state=active]:bg-emerald-600">
                <BookOpen className="w-4 h-4 mr-2" />
                My Summaries
              </TabsTrigger>
              <TabsTrigger value="generate" className="data-[state=active]:bg-teal-600">
                <Sparkles className="w-4 h-4 mr-2" />
                AI Generate
              </TabsTrigger>
            </TabsList>

            {/* Summaries Tab */}
            <TabsContent value="summaries" className="space-y-6">
              {selectedSummary ? (
                <SummaryView
                  summary={selectedSummary}
                  onBack={() => setSelectedSummary(null)}
                  onEdit={() => {
                    setEditingSummary(selectedSummary);
                    setShowEditDialog(true);
                  }}
                  onDelete={() => {
                    setDeletingSummaryId(selectedSummary.summary_id);
                    setShowDeleteDialog(true);
                  }}
                />
              ) : (
                <SummariesGrid
                  summaries={summaries}
                  loading={summariesLoading}
                  searchQuery={searchQuery}
                  onSearchChange={setSearchQuery}
                  onSelect={setSelectedSummary}
                  onEdit={(summary) => {
                    setEditingSummary(summary);
                    setShowEditDialog(true);
                  }}
                  onDelete={(summaryId) => {
                    setDeletingSummaryId(summaryId);
                    setShowDeleteDialog(true);
                  }}
                  onGenerate={() => setActiveTab('generate')}
                />
              )}
            </TabsContent>

            {/* AI Generate Tab */}
            <TabsContent value="generate">
              <Card className="border-white/10 bg-white/[0.02]">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Sparkles className="w-5 h-5 text-teal-400" />
                    Generate Summary with AI
                  </CardTitle>
                  <CardDescription>
                    Upload PDF files and let AI create a comprehensive summary for you
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

                  {/* Summary Details */}
                  <div className="grid md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="summary-title">Summary Title</Label>
                      <Input
                        id="summary-title"
                        placeholder="e.g., Chapter 5 - Genetics"
                        value={aiTitle}
                        onChange={(e) => setAiTitle(e.target.value)}
                        className="bg-white/5 border-white/10"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="summary-length">Summary Length</Label>
                      <div className="flex gap-2">
                        {(['brief', 'medium', 'detailed'] as SummaryLength[]).map((length) => (
                          <Button
                            key={length}
                            type="button"
                            variant={aiLength === length ? 'default' : 'outline'}
                            onClick={() => setAiLength(length)}
                            className={
                              aiLength === length
                                ? 'bg-teal-600 hover:bg-teal-500 flex-1'
                                : 'border-white/10 flex-1'
                            }
                          >
                            {length.charAt(0).toUpperCase() + length.slice(1)}
                          </Button>
                        ))}
                      </div>
                      <p className="text-xs text-foreground/50">
                        {aiLength === 'brief' && '~200-300 words'}
                        {aiLength === 'medium' && '~500-700 words'}
                        {aiLength === 'detailed' && '~1000-1500 words'}
                      </p>
                    </div>
                  </div>

                  <Button
                    onClick={handleGenerateSummary}
                    disabled={isGenerating || aiFiles.length === 0}
                    className="w-full bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500"
                  >
                    {isGenerating ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Generating...
                      </>
                    ) : (
                      <>
                        <Sparkles className="w-4 h-4 mr-2" />
                        Generate Summary
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
      {editingSummary && (
        <EditSummaryDialog
          open={showEditDialog}
          onOpenChange={(open) => {
            setShowEditDialog(open);
            if (!open) setEditingSummary(null);
          }}
          summary={editingSummary}
          onSubmit={(data) => handleUpdateSummary(editingSummary.summary_id, data)}
          isLoading={isUpdating}
        />
      )}

      <DeleteConfirmDialog
        open={showDeleteDialog}
        onOpenChange={setShowDeleteDialog}
        onConfirm={handleDeleteSummary}
        isLoading={isDeleting}
        title="Delete Summary"
        description="Are you sure you want to delete this summary? This action cannot be undone."
      />
    </div>
  );
}

// ============================================
// Summaries Grid Component
// ============================================
function SummariesGrid({
  summaries,
  loading,
  searchQuery,
  onSearchChange,
  onSelect,
  onEdit,
  onDelete,
  onGenerate,
}: {
  summaries: Array<Summary>;
  loading: boolean;
  searchQuery: string;
  onSearchChange: (query: string) => void;
  onSelect: (summary: Summary) => void;
  onEdit: (summary: Summary) => void;
  onDelete: (summaryId: string) => void;
  onGenerate: () => void;
}) {
  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  return (
    <div className="space-y-6">
      {/* Search */}
      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-foreground/40" />
        <Input
          placeholder="Search summaries..."
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          className="pl-9 bg-white/5 border-white/10"
        />
        {searchQuery && (
          <button
            onClick={() => onSearchChange('')}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-foreground/40 hover:text-foreground"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 animate-spin text-emerald-400" />
        </div>
      ) : summaries.length === 0 ? (
        <Card className="border-white/10 bg-white/[0.02]">
          <CardContent className="flex flex-col items-center justify-center py-16 text-foreground/60">
            <BookOpen className="w-12 h-12 mb-4 opacity-50" />
            <p className="text-lg font-medium mb-2">
              {searchQuery ? 'No summaries found' : 'No summaries yet'}
            </p>
            <p className="text-sm mb-4">
              {searchQuery
                ? `No summaries matching "${searchQuery}"`
                : 'Generate your first summary from lecture PDFs'}
            </p>
            {!searchQuery && (
              <Button onClick={onGenerate} className="gap-2">
                <Sparkles className="w-4 h-4" />
                Generate Summary
              </Button>
            )}
          </CardContent>
        </Card>
      ) : (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {/* Create New Card */}
          <motion.div
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={onGenerate}
            className="cursor-pointer"
          >
            <Card className="h-full border-dashed border-white/20 bg-white/[0.02] hover:bg-white/[0.05] hover:border-emerald-500/50 transition-all">
              <CardContent className="flex flex-col items-center justify-center h-full min-h-[180px] text-foreground/60">
                <Plus className="w-10 h-10 mb-3" />
                <span className="font-medium">Generate New Summary</span>
              </CardContent>
            </Card>
          </motion.div>

          {/* Summary Cards */}
          {summaries.map((summary, index) => (
            <motion.div
              key={summary.summary_id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: index * 0.05 }}
            >
              <Card className="group h-full border-white/10 bg-white/[0.02] hover:bg-white/[0.05] hover:border-emerald-500/30 transition-all">
                <CardHeader className="pb-2">
                  <div className="flex items-start justify-between">
                    <div className="flex-1 cursor-pointer" onClick={() => onSelect(summary)}>
                      <CardTitle className="text-lg flex items-center gap-2">
                        <BookOpen className="w-5 h-5 text-emerald-400" />
                        {summary.title}
                      </CardTitle>
                      <div className="flex items-center gap-3 mt-1 text-xs text-foreground/50">
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {summary.word_count} words
                        </span>
                        <span className="flex items-center gap-1">
                          <Key className="w-3 h-3" />
                          {summary.key_points.length} key points
                        </span>
                      </div>
                    </div>
                    <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          onEdit(summary);
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
                          onDelete(summary.summary_id);
                        }}
                        className="h-8 w-8 p-0 text-red-400 hover:text-red-300 hover:bg-red-500/10"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="cursor-pointer pt-0" onClick={() => onSelect(summary)}>
                  <p className="text-sm text-foreground/60 mb-3 line-clamp-3">
                    {summary.content.substring(0, 150)}...
                  </p>
                  {summary.source_files.length > 0 && (
                    <div className="flex flex-wrap gap-1 mb-2">
                      {summary.source_files.slice(0, 2).map((file, i) => (
                        <span
                          key={i}
                          className="text-xs px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-300 truncate max-w-[120px]"
                        >
                          {file}
                        </span>
                      ))}
                      {summary.source_files.length > 2 && (
                        <span className="text-xs text-foreground/40">
                          +{summary.source_files.length - 2} more
                        </span>
                      )}
                    </div>
                  )}
                  <div className="flex items-center justify-between text-sm text-foreground/50">
                    <span className="flex items-center gap-1">
                      <Calendar className="w-3 h-3" />
                      {formatDate(summary.created_at)}
                    </span>
                    <ChevronRight className="w-4 h-4" />
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

// ============================================
// Summary View Component (Full summary)
// ============================================
function SummaryView({
  summary,
  onBack,
  onEdit,
  onDelete,
}: {
  summary: Summary;
  onBack: () => void;
  onEdit: () => void;
  onDelete: () => void;
}) {
  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" onClick={onBack} className="gap-2">
            <ArrowLeft className="w-4 h-4" />
            Back
          </Button>
          <div>
            <h2 className="text-2xl font-bold">{summary.title}</h2>
            <div className="flex items-center gap-4 mt-1 text-sm text-foreground/50">
              <span className="flex items-center gap-1">
                <Calendar className="w-4 h-4" />
                {formatDate(summary.created_at)}
              </span>
              <span className="flex items-center gap-1">
                <Clock className="w-4 h-4" />
                {summary.word_count} words
              </span>
            </div>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={onEdit} className="gap-2 border-white/10">
            <Pencil className="w-4 h-4" />
            Edit
          </Button>
          <Button
            variant="outline"
            onClick={onDelete}
            className="gap-2 border-red-500/30 text-red-400 hover:bg-red-500/10"
          >
            <Trash2 className="w-4 h-4" />
            Delete
          </Button>
        </div>
      </div>

      {/* Source Files */}
      {summary.source_files.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {summary.source_files.map((file, i) => (
            <span
              key={i}
              className="text-sm px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-300 flex items-center gap-2"
            >
              <FileText className="w-4 h-4" />
              {file}
            </span>
          ))}
        </div>
      )}

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <Card className="lg:col-span-2 border-white/10 bg-white/[0.02]">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BookOpen className="w-5 h-5 text-emerald-400" />
              Summary
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="prose prose-invert max-w-none">
              {summary.content.split('\n\n').map((paragraph, i) => (
                <p key={i} className="text-foreground/80 leading-relaxed mb-4">
                  {paragraph}
                </p>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Key Points Sidebar */}
        <Card className="border-white/10 bg-white/[0.02] h-fit">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Key className="w-5 h-5 text-teal-400" />
              Key Points
            </CardTitle>
            <CardDescription>{summary.key_points.length} takeaways</CardDescription>
          </CardHeader>
          <CardContent>
            <ul className="space-y-3">
              {summary.key_points.map((point, i) => (
                <li key={i} className="flex items-start gap-3">
                  <span className="flex-shrink-0 w-6 h-6 rounded-full bg-teal-500/20 text-teal-400 flex items-center justify-center text-sm font-medium">
                    {i + 1}
                  </span>
                  <span className="text-sm text-foreground/80">{point}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

