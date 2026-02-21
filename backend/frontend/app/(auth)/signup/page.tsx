'use client';

import React, { Suspense, lazy, useState } from 'react';
import Image from 'next/image';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/app/authProvider';
import axios from 'axios';
import { ArrowLeft, Eye, EyeOff, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
// import BannerCard from '@/components/banner-card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import Loading from '@/components/loading';
import { GoogleLogin } from '@react-oauth/google';
const BannerCard = lazy(() => import('@/components/banner-card'));

function SignUpContent() {
  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    email: '',
    password: '',
    confirmPassword: '',
  });
  const [showPassword, setShowPassword] = useState<boolean>(false);
  const [showConfirmPassword, setShowConfirmPassword] =
    useState<boolean>(false);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isGoogleLoading, setIsGoogleLoading] = useState(false);
  const router = useRouter();
  const { login } = useAuth();
  const googleClientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;

  const togglePasswordVisibility = (field: 'password' | 'confirmPassword') => {
    if (field === 'password') {
      setShowPassword(!showPassword);
    } else {
      setShowConfirmPassword(!showConfirmPassword);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prevData) => ({ ...prevData, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    if (formData.password !== formData.confirmPassword) {
      setError("Passwords don't match");
      setIsLoading(false);
      return;
    }

    try {
      const baseUrl = process.env.NEXT_PUBLIC_SERVER_URL || 'http://localhost:8000';
      const response = await axios.post(
        `${baseUrl}/api/auth/signup`,
        {
          first_name: formData.firstName,
          last_name: formData.lastName,
          email: formData.email,
          password: formData.password,
        }
      );

      if (response.data.status === 'success') {
        toast('User Sign Up successful');
        router.push('/signin');
      }
    } catch (error: any) {
      toast(error.response?.data?.detail || 'An error occurred during sign up');
      setError(
        error.response?.data?.detail || 'An error occurred during sign up'
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoogleSuccess = async (credentialResponse: { credential?: string }) => {
    const credential = credentialResponse.credential;
    if (!credential) return;
    setIsGoogleLoading(true);
    setError('');
    try {
      const baseUrl = process.env.NEXT_PUBLIC_SERVER_URL || 'http://localhost:8000';
      const response = await axios.post<{ access_token: string; refresh_token: string }>(
        `${baseUrl}/api/auth/google`,
        { credential }
      );
      const { access_token, refresh_token } = response.data;
      const userResponse = await axios.get(
        `${baseUrl}/api/auth/me`,
        { headers: { Authorization: `Bearer ${access_token}` } }
      );
      const { email: userEmail, first_name, last_name } = userResponse.data;
      login(access_token, refresh_token, userEmail, first_name, last_name);
      toast.success('Account created with Google');
      router.push('/chat');
    } catch (err: unknown) {
      const msg = axios.isAxiosError(err) ? err.response?.data?.detail : 'Google sign-up failed';
      setError(String(msg));
      toast.error('Google sign-up failed');
    } finally {
      setIsGoogleLoading(false);
    }
  };

  return (
    <div className="flex h-full w-full flex-col lg:flex-row">
      <div className="flex flex-1 items-center justify-center p-6 lg:p-12">
        <div className="w-full max-w-[400px] space-y-6">
          <Button variant="ghost" className="mb-4" asChild>
            <Link href="/">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back
            </Link>
          </Button>
          <div className="space-y-4 text-center">
            <div className="flex justify-center">
              <Image
                src="/logo-black.png"
                alt="Nyayantar AI Logo"
                width={64}
                height={64}
                className="h-16 w-16"
              />
            </div>
            <div className="space-y-2">
              <h1 className="text-3xl font-bold">Join Nyayantar AI</h1>
              <p className="text-sm text-muted-foreground">Your Legal Guide, Powered by AI</p>
              <p className="text-balance text-muted-foreground">
                Create an account to get started
              </p>
            </div>
          </div>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="firstName">First name</Label>
                <Input
                  id="firstName"
                  name="firstName"
                  placeholder="John"
                  required
                  value={formData.firstName}
                  onChange={handleChange}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="lastName">Last name</Label>
                <Input
                  id="lastName"
                  name="lastName"
                  placeholder="Doe"
                  required
                  value={formData.lastName}
                  onChange={handleChange}
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                name="email"
                type="email"
                placeholder="m@example.com"
                required
                value={formData.email}
                onChange={handleChange}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <div className="relative">
                <Input
                  id="password"
                  name="password"
                  type={showPassword ? 'text' : 'password'}
                  required
                  value={formData.password}
                  onChange={handleChange}
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  className="absolute right-0 top-0 h-full px-3 py-2"
                  onClick={() => togglePasswordVisibility('password')}
                >
                  {showPassword ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </Button>
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="confirmPassword">Confirm Password</Label>
              <div className="relative">
                <Input
                  id="confirmPassword"
                  name="confirmPassword"
                  type={showConfirmPassword ? 'text' : 'password'}
                  required
                  value={formData.confirmPassword}
                  onChange={handleChange}
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  className="absolute right-0 top-0 h-full px-3 py-2"
                  onClick={() => togglePasswordVisibility('confirmPassword')}
                >
                  {showConfirmPassword ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </Button>
              </div>
            </div>
            {error && (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
            <Button type="submit" className="w-full" disabled={isLoading}>
              {isLoading ? 'Creating Account...' : 'Create Account'}
              {isLoading ? (
                <Loader2 className="h-4 w-4 animate-spin ml-4" />
              ) : (
                <></>
              )}
            </Button>
            {googleClientId && (
              <>
                <div className="relative my-4">
                  <div className="absolute inset-0 flex items-center">
                    <span className="w-full border-t" />
                  </div>
                  <div className="relative flex justify-center text-xs uppercase">
                    <span className="bg-background px-2 text-muted-foreground">Or sign up with</span>
                  </div>
                </div>
                <div className="flex justify-center">
                  <GoogleLogin
                    onSuccess={handleGoogleSuccess}
                    onError={() => {
                      setError('Google sign-up was cancelled or failed');
                      toast.error('Google sign-up failed');
                    }}
                    useOneTap={false}
                    theme="outline"
                    size="large"
                    text="continue_with"
                    shape="rectangular"
                  />
                </div>
              </>
            )}
            {isGoogleLoading && (
              <p className="text-sm text-muted-foreground text-center flex items-center justify-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin" /> Signing up with Google...
              </p>
            )}
          </form>
          <div className="text-center text-sm">
            Already have an account?{' '}
            <Link href="/signin" className="underline">
              Log in
            </Link>
          </div>
        </div>
      </div>
      <div className="hidden flex-1 lg:flex justify-center items-center bg-muted">
        <BannerCard />
      </div>
    </div>
  );
}

export default function SignUp() {
  return (
    <Suspense fallback={<Loading />}>
      <SignUpContent />
    </Suspense>
  );
}
