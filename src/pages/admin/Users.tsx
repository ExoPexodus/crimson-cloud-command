import { useState, useEffect } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { apiClient } from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useToast } from '@/hooks/use-toast';
import { Users, Shield, User, ArrowLeft, UserPlus } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form';
import { formatLocalDate } from '@/lib/dateUtils';

interface User {
  id: number;
  email: string;
  full_name: string;
  role: 'USER' | 'DEVOPS' | 'ADMIN';
  auth_provider: 'local' | 'keycloak';
  is_active: boolean;
  role_override?: boolean;
  created_at: string;
}

const createUserSchema = z.object({
  email: z.string().email('Invalid email address'),
  password: z.string().min(6, 'Password must be at least 6 characters'),
  full_name: z.string().min(1, 'Full name is required'),
  role: z.enum(['USER', 'DEVOPS', 'ADMIN']),
});

type CreateUserFormData = z.infer<typeof createUserSchema>;

export default function UsersPage() {
  const { user: currentUser, hasRole } = useAuth();
  const { toast } = useToast();
  const navigate = useNavigate();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [updatingUser, setUpdatingUser] = useState<number | null>(null);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [creatingUser, setCreatingUser] = useState(false);

  const form = useForm<CreateUserFormData>({
    resolver: zodResolver(createUserSchema),
    defaultValues: {
      email: '',
      password: '',
      full_name: '',
      role: 'USER',
    },
  });

  useEffect(() => {
    if (!hasRole('ADMIN')) {
      return;
    }
    fetchUsers();
  }, [hasRole]);

  const fetchUsers = async () => {
    try {
      console.log('[Users] Fetching all users...');
      const result = await apiClient.getAllUsers();
      console.log('[Users] Fetch result:', result);
      
      if (result.data) {
        console.log('[Users] Users loaded:', result.data.length);
        setUsers(result.data);
      }
    } catch (error: any) {
      console.error('[Users] Failed to fetch users:', error);
      console.error('[Users] Error details:', {
        message: error.message,
        response: error.response?.data,
        status: error.response?.status,
      });
      
      toast({
        title: "Error",
        description: error.response?.data?.detail || "Failed to fetch users",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const updateUserRole = async (userId: number, newRole: string) => {
    setUpdatingUser(userId);
    try {
      console.log(`[Users] Updating user ${userId} role to ${newRole}`);
      const result = await apiClient.updateUserRole(userId, newRole);
      console.log('[Users] Role update result:', result);
      
      if (result.data) {
        setUsers(users.map(user => 
          user.id === userId ? { ...user, role: newRole as any } : user
        ));
        toast({
          title: "Success",
          description: "User role updated successfully",
        });
      }
    } catch (error: any) {
      console.error('[Users] Failed to update user role:', error);
      console.error('[Users] Error details:', {
        message: error.message,
        response: error.response?.data,
        status: error.response?.status,
      });
      
      toast({
        title: "Error",
        description: error.response?.data?.detail || "Failed to update user role",
        variant: "destructive",
      });
    } finally {
      setUpdatingUser(null);
    }
  };

  const createUser = async (data: CreateUserFormData) => {
    setCreatingUser(true);
    try {
      console.log('[Users] Creating new user:', { email: data.email, role: data.role });
      const result = await apiClient.register(data.email, data.password, data.full_name);
      
      console.log('[Users] User creation result:', result);
      
      if (result.data) {
        // Update the user's role if not 'USER'
        if (data.role !== 'USER' && result.data.id) {
          console.log(`[Users] Updating user ${result.data.id} role to ${data.role}`);
          await apiClient.updateUserRole(result.data.id, data.role);
          console.log('[Users] Role update successful');
        }
        
        toast({
          title: "Success",
          description: "User created successfully",
        });
        
        form.reset();
        setCreateDialogOpen(false);
        fetchUsers();
      }
    } catch (error: any) {
      console.error('[Users] Failed to create user:', error);
      console.error('[Users] Error details:', {
        message: error.message,
        response: error.response?.data,
        status: error.response?.status,
      });
      
      const errorMessage = error.response?.data?.detail || error.message || "Failed to create user";
      
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setCreatingUser(false);
    }
  };

  const getRoleIcon = (role: string) => {
    switch (role) {
      case 'ADMIN': return <Shield className="h-4 w-4" />;
      case 'DEVOPS': return <Users className="h-4 w-4" />;
      default: return <User className="h-4 w-4" />;
    }
  };

  const getRoleBadgeVariant = (role: string) => {
    switch (role) {
      case 'ADMIN': return 'destructive';
      case 'DEVOPS': return 'default';
      default: return 'secondary';
    }
  };

  if (!hasRole('ADMIN')) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-dark-bg">
        <Card className="w-96">
          <CardHeader>
            <CardTitle className="text-center">Access Denied</CardTitle>
            <CardDescription className="text-center">
              You need admin privileges to access this page.
            </CardDescription>
          </CardHeader>
        </Card>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-dark-bg">
        <div className="text-white">Loading users...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-dark-bg p-6">
      <div className="max-w-6xl mx-auto">
        <div className="mb-6">
          <div className="flex items-center justify-between mb-4">
            <Button variant="ghost" onClick={() => navigate('/')} className="gap-2">
              <ArrowLeft className="h-4 w-4" />
              Back to Dashboard
            </Button>
            <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
              <DialogTrigger asChild>
                <Button className="gap-2">
                  <UserPlus className="h-4 w-4" />
                  Create Local User
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Create New Local User</DialogTitle>
                  <DialogDescription>
                    Create a new user account with local authentication
                  </DialogDescription>
                </DialogHeader>
                <Form {...form}>
                  <form onSubmit={form.handleSubmit(createUser)} className="space-y-4">
                    <FormField
                      control={form.control}
                      name="email"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Email</FormLabel>
                          <FormControl>
                            <Input type="email" placeholder="user@example.com" {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                    <FormField
                      control={form.control}
                      name="full_name"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Full Name</FormLabel>
                          <FormControl>
                            <Input placeholder="John Doe" {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                    <FormField
                      control={form.control}
                      name="password"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Password</FormLabel>
                          <FormControl>
                            <Input type="password" placeholder="••••••" {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                    <FormField
                      control={form.control}
                      name="role"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Role</FormLabel>
                          <Select onValueChange={field.onChange} defaultValue={field.value}>
                            <FormControl>
                              <SelectTrigger>
                                <SelectValue />
                              </SelectTrigger>
                            </FormControl>
                            <SelectContent>
                              <SelectItem value="USER">User</SelectItem>
                              <SelectItem value="DEVOPS">DevOps</SelectItem>
                              <SelectItem value="ADMIN">Admin</SelectItem>
                            </SelectContent>
                          </Select>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                    <div className="flex justify-end gap-2">
                      <Button type="button" variant="outline" onClick={() => setCreateDialogOpen(false)}>
                        Cancel
                      </Button>
                      <Button type="submit" disabled={creatingUser}>
                        {creatingUser ? 'Creating...' : 'Create User'}
                      </Button>
                    </div>
                  </form>
                </Form>
              </DialogContent>
            </Dialog>
          </div>
          <h1 className="text-3xl font-bold text-white mb-2">User Management</h1>
          <p className="text-gray-400">Manage user roles and permissions</p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="h-5 w-5" />
              All Users
            </CardTitle>
            <CardDescription>
              Manage roles for local users. Keycloak users' roles are managed externally.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {users.map((user) => (
                <div key={user.id} className="flex items-center justify-between p-4 border rounded-lg">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="font-medium">{user.full_name}</h3>
                      <Badge variant={getRoleBadgeVariant(user.role)}>
                        <div className="flex items-center gap-1">
                          {getRoleIcon(user.role)}
                          {user.role}
                        </div>
                      </Badge>
                      <Badge variant="outline">
                        {user.auth_provider}
                      </Badge>
                    </div>
                    <p className="text-sm text-gray-600">{user.email}</p>
                    <p className="text-xs text-gray-400">
                      Created: {formatLocalDate(user.created_at)}
                    </p>
                  </div>
                  
                  <div className="flex items-center gap-3">
                    {user.id !== currentUser?.id && (
                      <Select 
                        value={user.role} 
                        onValueChange={(value) => updateUserRole(user.id, value)}
                        disabled={updatingUser === user.id}
                      >
                        <SelectTrigger className="w-32">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="USER">User</SelectItem>
                          <SelectItem value="DEVOPS">DevOps</SelectItem>
                          <SelectItem value="ADMIN">Admin</SelectItem>
                        </SelectContent>
                      </Select>
                    )}
                    
                    {user.auth_provider === 'keycloak' && user.role_override && (
                      <Badge variant="outline" className="text-xs text-yellow-500 border-yellow-500">
                        Role Overridden
                      </Badge>
                    )}
                    
                    {user.auth_provider === 'keycloak' && !user.role_override && (
                      <Badge variant="outline" className="text-xs text-blue-500 border-blue-500">
                        Keycloak Managed
                      </Badge>
                    )}
                    
                    {user.id === currentUser?.id && (
                      <Badge variant="outline" className="text-xs">
                        Current User
                      </Badge>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}