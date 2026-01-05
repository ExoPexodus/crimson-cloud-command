import { useState } from "react";
import { useAuth } from "@/hooks/useAuth";
import { SidebarProvider } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { AlertCircle, Shield, User, Mail, Calendar, Key, Clock } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { apiClient } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";
import { formatLocalDate } from "@/lib/dateUtils";

const Settings = () => {
  const { user, sessionTimeoutMinutes } = useAuth();
  const { toast } = useToast();
  const [isLoading, setIsLoading] = useState(false);
  const [formData, setFormData] = useState({
    full_name: user?.full_name || '',
    email: user?.email || '',
    current_password: '',
    new_password: '',
    confirm_password: ''
  });

  const isKeycloakUser = user?.auth_provider === 'keycloak';

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleUpdateProfile = async () => {
    if (isKeycloakUser) return; // Should not be called for Keycloak users

    setIsLoading(true);
    try {
      const updateData: any = {
        full_name: formData.full_name,
        email: formData.email
      };

      // Only include password if user wants to change it
      if (formData.new_password) {
        if (formData.new_password !== formData.confirm_password) {
          toast({
            title: "Error",
            description: "New passwords do not match",
            variant: "destructive"
          });
          return;
        }
        updateData.current_password = formData.current_password;
        updateData.new_password = formData.new_password;
      }

      await apiClient.updateProfile(updateData);
      
      toast({
        title: "Success",
        description: "Profile updated successfully"
      });
      
      // Clear password fields
      setFormData(prev => ({
        ...prev,
        current_password: '',
        new_password: '',
        confirm_password: ''
      }));
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to update profile",
        variant: "destructive"
      });
    } finally {
      setIsLoading(false);
    }
  };

  const getRoleBadgeColor = (role: string) => {
    switch (role?.toUpperCase()) {
      case 'ADMIN': return 'bg-red-500/20 text-red-400 border-red-500/30';
      case 'DEVOPS': return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
      default: return 'bg-gray-500/20 text-gray-400 border-gray-500/30';
    }
  };

  return (
    <SidebarProvider>
      <div className="min-h-screen flex w-full">
        <AppSidebar />
        <div className="flex-1 flex flex-col overflow-hidden">
          <Header />
          <div className="flex-1 overflow-auto p-4 md:p-6 teal-scrollbar">
            <div className="max-w-4xl mx-auto space-y-6">
              <div>
                <h1 className="text-2xl font-bold mb-2">Settings</h1>
                <p className="text-muted-foreground">
                  Manage your account settings and preferences
                </p>
              </div>

              {isKeycloakUser && (
                <Alert className="border-blue-500/30 bg-blue-500/10">
                  <AlertCircle className="h-4 w-4 text-blue-400" />
                  <AlertDescription className="text-blue-400">
                    Your account is managed by Keycloak. Profile information is read-only and managed through your organization's identity provider.
                  </AlertDescription>
                </Alert>
              )}

              <div className="grid gap-6 md:grid-cols-2">
                {/* Profile Information */}
                <Card className="bg-dark-bg-lighter border-dark-bg-light">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-foreground">
                      <User className="h-5 w-5" />
                      Profile Information
                    </CardTitle>
                    <CardDescription>
                      {isKeycloakUser ? 'View your profile details' : 'Update your profile details'}
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="full_name" className="text-foreground">Full Name</Label>
                      <Input
                        id="full_name"
                        value={formData.full_name}
                        onChange={(e) => handleInputChange('full_name', e.target.value)}
                        disabled={isKeycloakUser}
                        className="bg-dark-bg border-dark-bg-light text-foreground disabled:opacity-60"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="email" className="text-foreground">Email</Label>
                      <Input
                        id="email"
                        type="email"
                        value={formData.email}
                        onChange={(e) => handleInputChange('email', e.target.value)}
                        disabled={isKeycloakUser}
                        className="bg-dark-bg border-dark-bg-light text-foreground disabled:opacity-60"
                      />
                    </div>
                    {!isKeycloakUser && (
                      <Button 
                        onClick={handleUpdateProfile}
                        disabled={isLoading}
                        className="w-full bg-dark-blue-600 hover:bg-dark-blue-700 text-white"
                      >
                        {isLoading ? 'Updating...' : 'Update Profile'}
                      </Button>
                    )}
                  </CardContent>
                </Card>

                {/* Account Information */}
                <Card className="bg-dark-bg-lighter border-dark-bg-light">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-foreground">
                      <Shield className="h-5 w-5" />
                      Account Information
                    </CardTitle>
                    <CardDescription>
                      View your account details and permissions
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Mail className="h-4 w-4 text-muted-foreground" />
                        <span className="text-sm text-muted-foreground">Role</span>
                      </div>
                      <Badge className={getRoleBadgeColor(user?.role || 'user')}>
                        {user?.role?.toUpperCase() || 'USER'}
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Key className="h-4 w-4 text-muted-foreground" />
                        <span className="text-sm text-muted-foreground">Auth Provider</span>
                      </div>
                      <Badge variant="outline" className="text-foreground border-dark-bg-light">
                        {user?.auth_provider?.toUpperCase() || 'LOCAL'}
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Calendar className="h-4 w-4 text-muted-foreground" />
                        <span className="text-sm text-muted-foreground">Member Since</span>
                      </div>
                      <span className="text-sm text-foreground">
                        {user?.created_at ? formatLocalDate(user.created_at) : 'Unknown'}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Clock className="h-4 w-4 text-muted-foreground" />
                        <span className="text-sm text-muted-foreground">Session Timeout</span>
                      </div>
                      <span className="text-sm text-foreground">
                        {sessionTimeoutMinutes} minutes
                      </span>
                    </div>
                  </CardContent>
                </Card>

                {/* Password Change - Only for local users */}
                {!isKeycloakUser && (
                  <Card className="bg-dark-bg-lighter border-dark-bg-light md:col-span-2">
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2 text-foreground">
                        <Key className="h-5 w-5" />
                        Change Password
                      </CardTitle>
                      <CardDescription>
                        Update your account password
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="grid gap-4 md:grid-cols-3">
                        <div className="space-y-2">
                          <Label htmlFor="current_password" className="text-foreground">Current Password</Label>
                          <Input
                            id="current_password"
                            type="password"
                            value={formData.current_password}
                            onChange={(e) => handleInputChange('current_password', e.target.value)}
                            className="bg-dark-bg border-dark-bg-light text-foreground"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="new_password" className="text-foreground">New Password</Label>
                          <Input
                            id="new_password"
                            type="password"
                            value={formData.new_password}
                            onChange={(e) => handleInputChange('new_password', e.target.value)}
                            className="bg-dark-bg border-dark-bg-light text-foreground"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="confirm_password" className="text-foreground">Confirm Password</Label>
                          <Input
                            id="confirm_password"
                            type="password"
                            value={formData.confirm_password}
                            onChange={(e) => handleInputChange('confirm_password', e.target.value)}
                            className="bg-dark-bg border-dark-bg-light text-foreground"
                          />
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </SidebarProvider>
  );
};

export default Settings;