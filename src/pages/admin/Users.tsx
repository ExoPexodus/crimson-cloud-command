import { useState, useEffect } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { apiClient } from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useToast } from '@/hooks/use-toast';
import { Users, Shield, User } from 'lucide-react';

interface User {
  id: number;
  email: string;
  full_name: string;
  role: 'user' | 'devops' | 'admin';
  auth_provider: 'local' | 'keycloak';
  is_active: boolean;
  created_at: string;
}

export default function UsersPage() {
  const { user: currentUser, hasRole } = useAuth();
  const { toast } = useToast();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [updatingUser, setUpdatingUser] = useState<number | null>(null);

  useEffect(() => {
    if (!hasRole('admin')) {
      return;
    }
    fetchUsers();
  }, [hasRole]);

  const fetchUsers = async () => {
    try {
      const result = await apiClient.getAllUsers();
      if (result.data) {
        setUsers(result.data);
      }
    } catch (error) {
      console.error('Failed to fetch users:', error);
      toast({
        title: "Error",
        description: "Failed to fetch users",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const updateUserRole = async (userId: number, newRole: string) => {
    console.log(`🔧 Frontend: Updating user ${userId} role to: "${newRole}"`);
    setUpdatingUser(userId);
    try {
      const result = await apiClient.updateUserRole(userId, newRole);
      console.log('✅ Frontend: Update role result:', result);
      if (result.data) {
        setUsers(users.map(user => 
          user.id === userId ? { ...user, role: newRole as any } : user
        ));
        toast({
          title: "Success",
          description: "User role updated successfully",
        });
      }
    } catch (error) {
      console.error('❌ Frontend: Failed to update user role:', error);
      toast({
        title: "Error",
        description: "Failed to update user role",
        variant: "destructive",
      });
    } finally {
      setUpdatingUser(null);
    }
  };

  const getRoleIcon = (role: string) => {
    switch (role) {
      case 'admin': return <Shield className="h-4 w-4" />;
      case 'devops': return <Users className="h-4 w-4" />;
      default: return <User className="h-4 w-4" />;
    }
  };

  const getRoleBadgeVariant = (role: string) => {
    switch (role) {
      case 'admin': return 'destructive';
      case 'devops': return 'default';
      default: return 'secondary';
    }
  };

  if (!hasRole('admin')) {
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
                      Created: {new Date(user.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  
                  <div className="flex items-center gap-3">
                    {user.auth_provider === 'local' && user.id !== currentUser?.id && (
                      <Select 
                        value={user.role} 
                        onValueChange={(value) => updateUserRole(user.id, value)}
                        disabled={updatingUser === user.id}
                      >
                        <SelectTrigger className="w-32">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="user">User</SelectItem>
                          <SelectItem value="devops">DevOps</SelectItem>
                          <SelectItem value="admin">Admin</SelectItem>
                        </SelectContent>
                      </Select>
                    )}
                    
                    {user.auth_provider === 'keycloak' && (
                      <Badge variant="outline" className="text-xs">
                        Managed in Keycloak
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