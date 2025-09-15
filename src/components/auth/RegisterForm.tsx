
import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useAuth } from '@/hooks/useAuth';
import { useToast } from '@/hooks/use-toast';
import { Server, ArrowLeft } from 'lucide-react';

interface RegisterFormProps {
  onBackToLogin: () => void;
}

export function RegisterForm({ onBackToLogin }: RegisterFormProps) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();
  const { toast } = useToast();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validate password confirmation
    if (password !== confirmPassword) {
      toast({
        title: 'Error',
        description: 'Passwords do not match. Please try again.',
        variant: 'destructive',
      });
      return;
    }
    
    if (password.length < 6) {
      toast({
        title: 'Error',
        description: 'Password must be at least 6 characters long.',
        variant: 'destructive',
      });
      return;
    }

    setLoading(true);

    try {
      const success = await register(email, password, fullName);
      if (success) {
        toast({
          title: 'Success',
          description: 'Account created and logged in successfully',
        });
      } else {
        toast({
          title: 'Error',
          description: 'Registration failed. Please try again.',
          variant: 'destructive',
        });
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Registration failed. Please try again.',
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
            Create Account
          </CardTitle>
          <CardDescription className="text-muted-foreground">
            Sign up for your autoscaling management dashboard
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="fullName">Full Name</Label>
              <Input
                id="fullName"
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                required
                className="bg-dark-bg/60 border-dark-bg-light/40 text-white focus-visible:ring-dark-blue-500"
              />
            </div>
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
                minLength={6}
                className="bg-dark-bg/60 border-dark-bg-light/40 text-white focus-visible:ring-dark-blue-500"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="confirmPassword">Confirm Password</Label>
              <Input
                id="confirmPassword"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                minLength={6}
                className={`bg-dark-bg/60 border-dark-bg-light/40 text-white focus-visible:ring-dark-blue-500 ${
                  confirmPassword && password !== confirmPassword 
                    ? 'border-red-500 focus-visible:ring-red-500' 
                    : ''
                }`}
              />
              {confirmPassword && password !== confirmPassword && (
                <p className="text-sm text-red-500">Passwords do not match</p>
              )}
            </div>
            <Button
              type="submit"
              className="w-full bg-dark-blue-600 hover:bg-dark-blue-700 text-white shadow-md"
              disabled={loading || (confirmPassword && password !== confirmPassword)}
            >
              {loading ? 'Creating Account...' : 'Create Account'}
            </Button>
          </form>
          
          <div className="mt-6 text-center">
            <Button
              variant="ghost"
              onClick={onBackToLogin}
              className="text-muted-foreground hover:text-white hover:bg-dark-blue-800/20"
            >
              <ArrowLeft size={16} className="mr-2" />
              Back to Login
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
