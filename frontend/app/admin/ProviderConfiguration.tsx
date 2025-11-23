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
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Separator } from '@/components/ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { 
  Loader2, 
  CheckCircle, 
  AlertCircle, 
  Plus, 
  Edit, 
  Trash2, 
  TestTube,
  Settings,
  Eye,
  EyeOff
} from 'lucide-react';
import { toast } from 'sonner';

interface ProviderConfig {
  id: string;
  name: string;
  provider_type: string;
  enabled: boolean;
  api_key?: string;
  base_url?: string;
  model: string;
  embedding_model: string;
  temperature: number;
  max_tokens?: number;
  dimensions?: number;
  custom_config: Record<string, any>;
  status: string;
  last_tested?: string;
  error_message?: string;
}

interface ProviderConfigFormData {
  name: string;
  provider_type: string;
  enabled: boolean;
  api_key: string;
  base_url: string;
  model: string;
  embedding_model: string;
  temperature: number;
  max_tokens: number;
  dimensions: number;
  custom_config: Record<string, any>;
}

const PROVIDER_TYPES = [
  { value: 'openai', label: 'OpenAI', description: 'GPT models and embeddings' },
  { value: 'gemini', label: 'Google Gemini', description: 'Gemini models and embeddings' },
  { value: 'anthropic', label: 'Anthropic Claude', description: 'Claude models with FastEmbed' },
  { value: 'groq', label: 'Groq', description: 'Fast inference with FastEmbed' },
  { value: 'ollama', label: 'Ollama', description: 'Local models and embeddings' },
  { value: 'mistral', label: 'Mistral AI', description: 'Mistral models and embeddings' },
  { value: 'azure-openai', label: 'Azure OpenAI', description: 'Azure-hosted OpenAI models' },
  { value: 't-systems', label: 'T-Systems LLM Hub', description: 'Custom T-Systems models' },
  { value: 'fastembed', label: 'FastEmbed', description: 'Local sentence transformers' },
];

const MODEL_OPTIONS = {
  openai: {
    llm: ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-3.5-turbo'],
    embedding: ['text-embedding-3-small', 'text-embedding-3-large', 'text-embedding-ada-002']
  },
  gemini: {
    llm: ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-1.0-pro'],
    embedding: ['text-embedding-004', 'text-embedding-002']
  },
  anthropic: {
    llm: ['claude-3-opus-20240229', 'claude-3-sonnet-20240229', 'claude-3-haiku-20240307'],
    embedding: ['fastembed-all-MiniLM-L6-v2']
  },
  groq: {
    llm: ['llama3-8b-8192', 'llama3-70b-8192', 'mixtral-8x7b-32768'],
    embedding: ['fastembed-all-MiniLM-L6-v2']
  },
  ollama: {
    llm: ['llama2', 'llama3', 'mistral', 'codellama'],
    embedding: ['nomic-embed-text', 'all-minilm']
  },
  mistral: {
    llm: ['mistral-small', 'mistral-medium', 'mistral-large'],
    embedding: ['mistral-embed']
  },
  'azure-openai': {
    llm: ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo'],
    embedding: ['text-embedding-3-small', 'text-embedding-3-large']
  },
  't-systems': {
    llm: ['gpt-3.5-turbo', 'gpt-4'],
    embedding: ['text-embedding-3-large', 'text-embedding-3-small']
  },
  fastembed: {
    llm: ['llama2', 'llama3'],
    embedding: ['sentence-transformers/all-MiniLM-L6-v2', 'sentence-transformers/paraphrase-multilingual-mpnet-base-v2']
  }
};

export default function ProviderConfiguration() {
  const { axiosInstance } = useAuth();
  const [providers, setProviders] = useState<ProviderConfig[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedProvider, setSelectedProvider] = useState<ProviderConfig | null>(null);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [testing, setTesting] = useState<string | null>(null);
  const [showApiKey, setShowApiKey] = useState<Record<string, boolean>>({});

  const [formData, setFormData] = useState<ProviderConfigFormData>({
    name: '',
    provider_type: 'openai',
    enabled: false,
    api_key: '',
    base_url: '',
    model: '',
    embedding_model: '',
    temperature: 0.7,
    max_tokens: 1000,
    dimensions: 1536,
    custom_config: {}
  });

  useEffect(() => {
    fetchProviders();
  }, []);

  const fetchProviders = async () => {
    setLoading(true);
    try {
      const response = await axiosInstance.get('/api/admin/providers/configs');
      setProviders(response.data);
    } catch (error: any) {
      toast.error(`Failed to fetch providers: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateProvider = () => {
    setFormData({
      name: '',
      provider_type: 'openai',
      enabled: false,
      api_key: '',
      base_url: '',
      model: '',
      embedding_model: '',
      temperature: 0.7,
      max_tokens: 1000,
      dimensions: 1536,
      custom_config: {}
    });
    setIsEditing(false);
    setSelectedProvider(null);
    setIsDialogOpen(true);
  };

  const handleEditProvider = (provider: ProviderConfig) => {
    setFormData({
      name: provider.name,
      provider_type: provider.provider_type,
      enabled: provider.enabled,
      api_key: provider.api_key || '',
      base_url: provider.base_url || '',
      model: provider.model,
      embedding_model: provider.embedding_model,
      temperature: provider.temperature,
      max_tokens: provider.max_tokens || 1000,
      dimensions: provider.dimensions || 1536,
      custom_config: provider.custom_config || {}
    });
    setIsEditing(true);
    setSelectedProvider(provider);
    setIsDialogOpen(true);
  };

  const handleSaveProvider = async () => {
    try {
      if (isEditing && selectedProvider) {
        await axiosInstance.put(`/api/admin/providers/configs/${selectedProvider.id}`, formData);
        toast.success('Provider updated successfully');
      } else {
        await axiosInstance.post('/api/admin/providers/configs', formData);
        toast.success('Provider created successfully');
      }
      setIsDialogOpen(false);
      fetchProviders();
    } catch (error: any) {
      toast.error(`Failed to save provider: ${error.response?.data?.detail || error.message}`);
    }
  };

  const handleDeleteProvider = async (providerId: string) => {
    if (!confirm('Are you sure you want to delete this provider?')) return;
    
    try {
      await axiosInstance.delete(`/api/admin/providers/configs/${providerId}`);
      toast.success('Provider deleted successfully');
      fetchProviders();
    } catch (error: any) {
      toast.error(`Failed to delete provider: ${error.response?.data?.detail || error.message}`);
    }
  };

  const handleTestProvider = async (provider: ProviderConfig) => {
    setTesting(provider.id);
    try {
      const response = await axiosInstance.post(`/api/admin/providers/configs/${provider.id}/test`);
      if (response.data.success) {
        toast.success('Provider test successful');
      } else {
        toast.error(`Provider test failed: ${response.data.message}`);
      }
      fetchProviders();
    } catch (error: any) {
      toast.error(`Provider test failed: ${error.response?.data?.detail || error.message}`);
    } finally {
      setTesting(null);
    }
  };

  const handleToggleProvider = async (providerId: string, enabled: boolean) => {
    try {
      await axiosInstance.post(`/api/admin/providers/configs/${providerId}/enable`, null, {
        params: { enabled }
      });
      toast.success(`Provider ${enabled ? 'enabled' : 'disabled'} successfully`);
      fetchProviders();
    } catch (error: any) {
      toast.error(`Failed to toggle provider: ${error.response?.data?.detail || error.message}`);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-500';
      case 'inactive': return 'bg-gray-500';
      case 'error': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active': return <CheckCircle className="h-4 w-4" />;
      case 'error': return <AlertCircle className="h-4 w-4" />;
      default: return <AlertCircle className="h-4 w-4" />;
    }
  };

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Provider Configuration</CardTitle>
          <CardDescription>Manage AI provider configurations</CardDescription>
        </CardHeader>
        <CardContent className="flex items-center justify-center py-8">
          <Loader2 className="h-6 w-6 animate-spin" />
          <span className="ml-2">Loading providers...</span>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold">Provider Configuration</h2>
          <p className="text-muted-foreground">Manage AI provider configurations and settings</p>
        </div>
        <Button onClick={handleCreateProvider}>
          <Plus className="h-4 w-4 mr-2" />
          Add Provider
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {providers.map((provider) => (
          <Card key={provider.id} className="relative">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg">{provider.name}</CardTitle>
                <div className="flex items-center space-x-2">
                  <Badge className={getStatusColor(provider.status)}>
                    {getStatusIcon(provider.status)}
                    <span className="ml-1 capitalize">{provider.status}</span>
                  </Badge>
                  <Switch
                    checked={provider.enabled}
                    onCheckedChange={(enabled) => handleToggleProvider(provider.id, enabled)}
                  />
                </div>
              </div>
              <CardDescription>
                {PROVIDER_TYPES.find(p => p.value === provider.provider_type)?.description}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="text-sm space-y-1">
                <p><strong>Model:</strong> {provider.model}</p>
                <p><strong>Embedding:</strong> {provider.embedding_model}</p>
                <p><strong>Temperature:</strong> {provider.temperature}</p>
                {provider.last_tested && (
                  <p><strong>Last Tested:</strong> {new Date(provider.last_tested).toLocaleString()}</p>
                )}
                {provider.error_message && (
                  <p className="text-red-500"><strong>Error:</strong> {provider.error_message}</p>
                )}
              </div>
              
              <Separator />
              
              <div className="flex space-x-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleEditProvider(provider)}
                >
                  <Edit className="h-4 w-4 mr-1" />
                  Edit
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleTestProvider(provider)}
                  disabled={testing === provider.id}
                >
                  {testing === provider.id ? (
                    <Loader2 className="h-4 w-4 mr-1 animate-spin" />
                  ) : (
                    <TestTube className="h-4 w-4 mr-1" />
                  )}
                  Test
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleDeleteProvider(provider.id)}
                  className="text-red-500 hover:text-red-700"
                >
                  <Trash2 className="h-4 w-4 mr-1" />
                  Delete
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {providers.length === 0 && (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-8">
            <Settings className="h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">No Providers Configured</h3>
            <p className="text-muted-foreground text-center mb-4">
              Get started by adding your first AI provider configuration.
            </p>
            <Button onClick={handleCreateProvider}>
              <Plus className="h-4 w-4 mr-2" />
              Add Provider
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Provider Configuration Dialog */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {isEditing ? 'Edit Provider' : 'Add New Provider'}
            </DialogTitle>
            <DialogDescription>
              Configure your AI provider settings and credentials.
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="name">Provider Name</Label>
                <Input
                  id="name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="e.g., My OpenAI Provider"
                />
              </div>
              <div>
                <Label htmlFor="provider_type">Provider Type</Label>
                <Select
                  value={formData.provider_type}
                  onValueChange={(value) => setFormData({ ...formData, provider_type: value })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {PROVIDER_TYPES.map((type) => (
                      <SelectItem key={type.value} value={type.value}>
                        <div>
                          <div className="font-medium">{type.label}</div>
                          <div className="text-sm text-muted-foreground">{type.description}</div>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="api_key">API Key</Label>
                <div className="relative">
                  <Input
                    id="api_key"
                    type={showApiKey[formData.provider_type] ? 'text' : 'password'}
                    value={formData.api_key}
                    onChange={(e) => setFormData({ ...formData, api_key: e.target.value })}
                    placeholder="Enter your API key"
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="absolute right-0 top-0 h-full px-3"
                    onClick={() => setShowApiKey({ ...showApiKey, [formData.provider_type]: !showApiKey[formData.provider_type] })}
                  >
                    {showApiKey[formData.provider_type] ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </Button>
                </div>
              </div>
              <div>
                <Label htmlFor="base_url">Base URL (Optional)</Label>
                <Input
                  id="base_url"
                  value={formData.base_url}
                  onChange={(e) => setFormData({ ...formData, base_url: e.target.value })}
                  placeholder="https://api.openai.com/v1"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="model">LLM Model</Label>
                <Select
                  value={formData.model}
                  onValueChange={(value) => setFormData({ ...formData, model: value })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select model" />
                  </SelectTrigger>
                  <SelectContent>
                    {MODEL_OPTIONS[formData.provider_type as keyof typeof MODEL_OPTIONS]?.llm.map((model) => (
                      <SelectItem key={model} value={model}>
                        {model}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label htmlFor="embedding_model">Embedding Model</Label>
                <Select
                  value={formData.embedding_model}
                  onValueChange={(value) => setFormData({ ...formData, embedding_model: value })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select embedding model" />
                  </SelectTrigger>
                  <SelectContent>
                    {MODEL_OPTIONS[formData.provider_type as keyof typeof MODEL_OPTIONS]?.embedding.map((model) => (
                      <SelectItem key={model} value={model}>
                        {model}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div>
                <Label htmlFor="temperature">Temperature</Label>
                <Input
                  id="temperature"
                  type="number"
                  min="0"
                  max="2"
                  step="0.1"
                  value={formData.temperature}
                  onChange={(e) => setFormData({ ...formData, temperature: parseFloat(e.target.value) })}
                />
              </div>
              <div>
                <Label htmlFor="max_tokens">Max Tokens</Label>
                <Input
                  id="max_tokens"
                  type="number"
                  min="1"
                  value={formData.max_tokens}
                  onChange={(e) => setFormData({ ...formData, max_tokens: parseInt(e.target.value) })}
                />
              </div>
              <div>
                <Label htmlFor="dimensions">Dimensions</Label>
                <Input
                  id="dimensions"
                  type="number"
                  min="1"
                  value={formData.dimensions}
                  onChange={(e) => setFormData({ ...formData, dimensions: parseInt(e.target.value) })}
                />
              </div>
            </div>

            <div className="flex items-center space-x-2">
              <Switch
                id="enabled"
                checked={formData.enabled}
                onCheckedChange={(enabled) => setFormData({ ...formData, enabled })}
              />
              <Label htmlFor="enabled">Enable this provider</Label>
            </div>
          </div>

          <div className="flex justify-end space-x-2 pt-4">
            <Button variant="outline" onClick={() => setIsDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleSaveProvider}>
              {isEditing ? 'Update Provider' : 'Create Provider'}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
