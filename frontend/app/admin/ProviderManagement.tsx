'use client';
import React, { useEffect, useState } from 'react';
import { useAuth } from '@/app/authProvider';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Loader2, CheckCircle, AlertCircle } from 'lucide-react';
import { toast } from 'sonner';

interface Provider {
  name: string;
  model: string;
  embedding_model: string;
  active: boolean;
}

interface ProvidersResponse {
  providers: Record<string, Provider>;
  current_provider: string;
}

export default function ProviderManagement() {
  const { axiosInstance } = useAuth();
  const [providers, setProviders] = useState<Record<string, Provider>>({});
  const [currentProvider, setCurrentProvider] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);
  const [switching, setSwitching] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchProviders();
  }, []);

  const fetchProviders = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axiosInstance.get('/api/admin/providers');
      setProviders(response.data.providers);
      setCurrentProvider(response.data.current_provider);
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Failed to fetch providers');
      toast.error('Failed to fetch providers');
    } finally {
      setLoading(false);
    }
  };

  const switchProvider = async (providerName: string) => {
    setSwitching(providerName);
    try {
      const response = await axiosInstance.post(`/api/admin/providers/${providerName}/switch`);
      setCurrentProvider(providerName);
      toast.success(response.data.message);
      // Refresh providers to update active status
      await fetchProviders();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to switch provider');
    } finally {
      setSwitching(null);
    }
  };

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>AI Provider Management</CardTitle>
          <CardDescription>Manage AI model providers and switch between them</CardDescription>
        </CardHeader>
        <CardContent className="flex items-center justify-center py-8">
          <Loader2 className="h-6 w-6 animate-spin" />
          <span className="ml-2">Loading providers...</span>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>AI Provider Management</CardTitle>
          <CardDescription>Manage AI model providers and switch between them</CardDescription>
        </CardHeader>
        <CardContent className="flex items-center justify-center py-8">
          <AlertCircle className="h-6 w-6 text-red-500" />
          <span className="ml-2 text-red-500">{error}</span>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>AI Provider Management</CardTitle>
        <CardDescription>
          Manage AI model providers and switch between them. Currently using: <strong>{currentProvider}</strong>
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {Object.entries(providers).map(([key, provider]) => (
          <div key={key} className="border rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div>
                  <h3 className="font-semibold text-lg">{provider.name}</h3>
                  <p className="text-sm text-muted-foreground">
                    Model: {provider.model} | Embedding: {provider.embedding_model}
                  </p>
                </div>
                {provider.active && (
                  <Badge variant="default" className="bg-green-500">
                    <CheckCircle className="h-3 w-3 mr-1" />
                    Active
                  </Badge>
                )}
              </div>
              <Button
                onClick={() => switchProvider(key)}
                disabled={provider.active || switching === key}
                variant={provider.active ? "secondary" : "default"}
              >
                {switching === key ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Switching...
                  </>
                ) : provider.active ? (
                  'Current Provider'
                ) : (
                  'Switch to this Provider'
                )}
              </Button>
            </div>
          </div>
        ))}
        
        <Separator />
        
        <div className="text-sm text-muted-foreground">
          <p><strong>Note:</strong> Switching providers will affect all new chat sessions. Existing conversations will continue to use their original provider.</p>
        </div>
      </CardContent>
    </Card>
  );
}
