
import { LoginForm } from './LoginForm';
// import { RegisterForm } from './RegisterForm'; // Commented out - only admin can create users

export function AuthPage() {
  // Registration disabled - only admin can create users
  return <LoginForm />;
}
