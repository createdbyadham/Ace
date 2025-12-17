import { createFileRoute, Link } from '@tanstack/react-router';
import { motion } from 'framer-motion';
import { ArrowRight, Sparkles, Brain, Zap, BookOpen } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Navbar } from '@/components/layout/Navbar';
import { Footer } from '@/components/layout/Footer';
import { useAuth } from '@/context/AuthContext';
import Particles from '@/components/ui/Particles';

export const Route = createFileRoute('/')({
  component: LandingPage,
});

function LandingPage() {
  const { isAuthenticated, logout, user } = useAuth();

  const features = [
    {
      icon: Brain,
      title: 'Spaced Repetition',
      description: 'Our SM-2 algorithm optimizes your learning by scheduling reviews at the perfect moment.',
    },
    {
      icon: Zap,
      title: 'Smart Flashcards',
      description: 'Create and study flashcards that adapt to your learning pace and retention.',
    },
    {
      icon: BookOpen,
      title: 'Lecture Notes',
      description: 'Transform your lectures into structured summaries and quiz questions instantly.',
    },
    {
      icon: Sparkles,
      title: 'AI-Powered',
      description: 'Let AI generate questions, summaries, and study materials from your content.',
    },
  ];

  return (
    <div className="relative min-h-screen flex flex-col overflow-hidden">
      {/* Particle Background */}
      <div className="fixed inset-0 z-0">
        <Particles
          particleCount={150}
          particleSpread={15}
          speed={0.05}
          particleColors={['#6366f1', '#8b5cf6', '#a855f7']}
          moveParticlesOnHover
          particleHoverFactor={0.5}
          alphaParticles
          particleBaseSize={80}
          sizeRandomness={1.5}
          cameraDistance={25}
        />
      </div>

      {/* Gradient Overlays */}
      <div className="fixed inset-0 z-0 bg-gradient-to-b from-background via-background/90 to-background pointer-events-none" />
      <div className="fixed inset-0 z-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-indigo-900/20 via-transparent to-transparent pointer-events-none" />

      <Navbar
        isAuthenticated={isAuthenticated}
        user={user}
        onLogout={logout}
        className="relative z-10"
      />

      <main className="relative z-10 flex-1">
        {/* Hero Section */}
        <section className="relative px-4 pt-20 pb-32 md:pt-32 md:pb-40">
          <div className="max-w-6xl mx-auto text-center">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
            >
              <span className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-sm font-medium mb-8">
                <Sparkles className="w-4 h-4" />
                AI-Powered Learning Platform
              </span>
            </motion.div>

            <motion.h1
              className="text-5xl md:text-7xl font-bold tracking-tight mb-6"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.1 }}
            >
              <span className="bg-gradient-to-r from-white via-indigo-200 to-purple-200 bg-clip-text text-transparent">
                Master anything
              </span>
              <br />
              <span className="bg-gradient-to-r from-indigo-200 to-purple-800 bg-clip-text text-transparent">
                with Cardify
              </span>
            </motion.h1>

            <motion.p
              className="text-lg md:text-xl text-foreground/60 max-w-2xl mx-auto mb-10"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
            >
              Transform your study sessions with intelligent flashcards, spaced repetition,
              and AI-generated content. Learn smarter, not harder.
            </motion.p>

            <motion.div
              className="flex flex-col sm:flex-row gap-4 justify-center"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.3 }}
            >
              {isAuthenticated ? (
                <Link to="/quiz">
                  <Button size="lg" className="group bg-black hover:bg-black/80 text-white
                  px-8 py-6 text-lg rounded-xl
                  outline outline-2 outline-white/10
                  shadow-[0_0_20px_4px_rgba(99,102,241,0.25)]
                  transition-all duration-300">
                    Try it out now
                    <ArrowRight className="ml-2 w-5 h-5 transition-transform group-hover:translate-x-1" />
                  </Button>
                </Link>
              ) : (
                <>
                  <Link to="/register">
                    <Button size="lg" className="group bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white px-8 py-6 text-lg rounded-xl shadow-lg shadow-indigo-500/25">
                      Start Learning Free
                      <ArrowRight className="ml-2 w-5 h-5 transition-transform group-hover:translate-x-1" />
                    </Button>
                  </Link>
                  <Link to="/login">
                    <Button size="lg" variant="outline" className="px-8 py-6 text-lg rounded-xl border-white/20 hover:bg-white/5">
                      Sign In
                    </Button>
                  </Link>
                </>
              )}
            </motion.div>
          </div>
        </section>

        {/* Features Section */}
        <section className="relative px-4 py-24">
          <div className="max-w-6xl mx-auto">
            <motion.div
              className="text-center mb-16"
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
            >
              <h2 className="text-3xl md:text-4xl font-bold mb-4">
                Everything you need to{' '}
                <span className="bg-gradient-to-r from-indigo-100 to-purple-800 bg-clip-text text-transparent">
                  excel
                </span>
              </h2>
              <p className="text-foreground/60 max-w-xl mx-auto">
                Powerful tools designed to make your learning journey efficient and enjoyable.
              </p>
            </motion.div>

            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
              {features.map((feature, index) => (
                <motion.div
                  key={feature.title}
                  className="group relative p-6 rounded-2xl bg-white/[0.02] border border-white/10 hover:border-indigo-500/30 transition-all duration-300"
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.4, delay: index * 0.1 }}
                  whileHover={{ y: -5 }}
                >
                  <div className="absolute inset-0 rounded-2xl bg-gradient-to-b from-indigo-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                  <div className="relative">
                    <div className="w-12 h-12 rounded-xl bg-indigo-500/10  flex items-center justify-center mb-4">
                      <feature.icon className="w-6 h-6 text-indigo-400" />
                    </div>
                    <h3 className="text-lg font-semibold mb-2">{feature.title}</h3>
                    <p className="text-sm text-foreground/60">{feature.description}</p>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        </section>
      </main>

      <Footer className="relative z-10" />
    </div>
  );
}

