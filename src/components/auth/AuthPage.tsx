
import { useState } from 'react';
import { LoginForm } from './LoginForm';
import { RegisterForm } from './RegisterForm';

export function AuthPage() {
  const [showRegister, setShowRegister] = useState(false);

  return showRegister ? (
    <RegisterForm onBackToLogin={() => setShowRegister(false)} />
  ) : (
    <LoginForm onShowRegister={() => setShowRegister(true)} />
  );
}
