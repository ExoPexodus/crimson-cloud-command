
import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useAuth } from '@/hooks/useAuth';
import { useToast } from '@/hooks/use-toast';
import { Server } from 'lucide-react';
import { KeycloakLoginButton } from './KeycloakLoginButton';
import { Separator } from '@/components/ui/separator';

// Registration disabled - only admin can create users
export function LoginForm() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const { toast } = useToast();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const success = await login(email, password);
      if (success) {
        toast({
          title: 'Success',
          description: 'Logged in successfully',
        });
      } else {
        toast({
          title: 'Error',
          description: 'Invalid email or password',
          variant: 'destructive',
        });
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Login failed. Please try again.',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-dark-bg bg-gradient-mesh p-4">
      <Card className="w-full max-w-md glass-card shadow-xl">
        <CardHeader className="text-center">
          <div className="mx-auto h-12 w-12 rounded-md bg-gradient-dark-blue flex items-center justify-center mb-4 shadow-lg animate-glow">
            <Server size={24} className="text-white" />
          </div>
          <CardTitle className="text-2xl font-bold text-white">
            OracleOps<span className="text-dark-blue-400">.</span>
          </CardTitle>
          <CardDescription className="text-muted-foreground">
            Sign in to your autoscaling management dashboard
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="bg-dark-bg/60 border-dark-bg-light/40 text-white focus-visible:ring-dark-blue-500"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="bg-dark-bg/60 border-dark-bg-light/40 text-white focus-visible:ring-dark-blue-500"
              />
            </div>
            <Button
              type="submit"
              className="w-full bg-dark-blue-600 hover:bg-dark-blue-700 text-white shadow-md"
              disabled={loading}
            >
              {loading ? 'Signing in...' : 'Sign In'}
            </Button>
          </form>

          <div className="mt-6">
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <Separator className="w-full" />
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-card px-2 text-muted-foreground">Or continue with</span>
              </div>
            </div>
            
            <div className="mt-6">
              <KeycloakLoginButton />
            </div>
          </div>
          
          {/* Registration disabled - contact admin for account creation */}
          <div className="mt-6 text-center">
            <p className="text-xs text-muted-foreground">
              Need an account? Contact your administrator.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
