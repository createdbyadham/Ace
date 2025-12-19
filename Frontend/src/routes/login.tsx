import { createFileRoute, Link, useNavigate } from '@tanstack/react-router';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { motion } from 'framer-motion';
import { Mail, Lock, ArrowLeft, Loader2 } from 'lucide-react';
import { toast } from 'sonner';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { useLogin } from '@/application/auth/useAuth';
import { useAuth } from '@/context/AuthContext';
import Particles from '@/components/ui/Particles';

export const Route = createFileRoute('/login')({
  component: LoginPage,
});

const loginSchema = z.object({
  email: z.string().email('Please enter a valid email address'),
  password: z.string().min(6, 'Password must be at least 6 characters'),
});

type LoginFormData = z.infer<typeof loginSchema>;

function LoginPage() {
  const navigate = useNavigate();
  const { login: setAuth } = useAuth();
  const loginMutation = useLogin();

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: '',
      password: '',
    },
  });

  const onSubmit = async (data: LoginFormData) => {
    try {
      const response = await loginMutation.mutateAsync(data);
      setAuth(response.access_token, response.refresh_token, {
        id: response.user_id,
        email: response.email,
      });
      toast.success('Welcome back!', {
        description: 'You have successfully logged in.',
      });
      navigate({ to: '/' });
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } } };
      toast.error('Login failed', {
        description: err?.response?.data?.detail || 'Invalid email or password. Please try again.',
      });
    }
  };

  return (
    <div className="relative min-h-screen flex items-center justify-center p-4 overflow-hidden">
      {/* Particle Background */}
      <div className="fixed inset-0 z-0">
        <Particles
          particleCount={100}
          particleSpread={12}
          speed={0.03}
          particleColors={['#6366f1', '#8b5cf6', '#a855f7']}
          moveParticlesOnHover
          particleHoverFactor={0.3}
          alphaParticles
          particleBaseSize={60}
          sizeRandomness={1}
          cameraDistance={30}
        />
      </div>

      {/* Gradient Overlays */}
      <div className="fixed inset-0 z-0 bg-gradient-to-b from-background via-background/95 to-background pointer-events-none" />
      <div className="fixed inset-0 z-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-indigo-900/20 via-transparent to-transparent pointer-events-none" />

      {/* Back Button */}
      <motion.div
        className="absolute top-6 left-6 z-20"
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.4 }}
      >
        <Link to="/">
          <Button variant="ghost" className="gap-2 text-foreground/70 hover:text-foreground">
            <ArrowLeft className="w-4 h-4" />
            Back
          </Button>
        </Link>
      </motion.div>

      {/* Login Card */}
      <motion.div
        className="relative z-10 w-full max-w-md"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <Card className="border-white/10 bg-background/60 backdrop-blur-xl shadow-2xl shadow-indigo-500/10">
          <CardHeader className="text-center space-y-2 pb-2">
            <Link to="/" className="flex items-center justify-center gap-2 mb-4">
              <div className="h-10 w-10 rounded-xl bg-black outline outline-2 outline-white/10 flex items-center justify-center shadow-lg shadow-indigo-500/30">
                <span className="text-white font-bold text-xl">C</span>
              </div>
              <span className="text-xl font-bold">Cardify</span>
            </Link>
            <CardTitle className="text-2xl font-bold">Welcome back</CardTitle>
            <CardDescription className="text-foreground/60">
              Sign in to your account to continue learning
            </CardDescription>
          </CardHeader>

          <CardContent className="pt-6">
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
              <div className="space-y-2">
                <Label htmlFor="email" className="text-sm font-medium">
                  Email
                </Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-foreground/40" />
                  <Input
                    id="email"
                    type="email"
                    placeholder="you@example.com"
                    className="pl-10 bg-white/5 border-white/10 focus:border-indigo-500/50 h-11"
                    {...register('email')}
                  />
                </div>
                {errors.email && (
                  <p className="text-sm text-red-400">{errors.email.message}</p>
                )}
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label htmlFor="password" className="text-sm font-medium">
                    Password
                  </Label>
                  <Link
                    to="/"
                    className="text-xs text-indigo-400 hover:text-indigo-300 transition-colors"
                  >
                    Forgot password?
                  </Link>
                </div>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-foreground/40" />
                  <Input
                    id="password"
                    type="password"
                    placeholder="••••••••"
                    className="pl-10 bg-white/5 border-white/10 focus:border-indigo-500/50 h-11"
                    {...register('password')}
                  />
                </div>
                {errors.password && (
                  <p className="text-sm text-red-400">{errors.password.message}</p>
                )}
              </div>

              <Button
                type="submit"
                className="w-full h-11 bg-black hover:bg-black/80 text-white px-8 py-6 rounded-xl
                  outline outline-2 outline-white/10
                  shadow-[0_0_20px_4px_rgba(99,102,241,0.25)]
                  transition-all duration-300"
                disabled={isSubmitting || loginMutation.isPending}
              >
                {(isSubmitting || loginMutation.isPending) ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Signing in...
                  </>
                ) : (
                  'Sign In'
                )}
              </Button>
            </form>

            <div className="mt-6 text-center text-sm text-foreground/60">
              Don't have an account?{' '}
              <Link
                to="/register"
                className="text-indigo-400 hover:text-indigo-300 font-medium transition-colors"
              >
                Sign up
              </Link>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
}

