'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Progress } from '@/components/ui/progress';
import { 
  FileText, 
  Users, 
  TrendingUp, 
  AlertTriangle, 
  CheckCircle, 
  Clock,
  BarChart3,
  Settings,
  Eye,
  Edit,
  Trash2
} from 'lucide-react';
import { useAuth } from '@/app/authProvider';
import { toast } from 'sonner';

interface DocumentStats {
  total_sessions: number;
  completed_sessions: number;
  failed_sessions: number;
  completion_rate: number;
  total_documents: number;
  total_downloads: number;
  average_generation_time: number;
  document_type_breakdown: Record<string, number>;
}

interface SystemHealth {
  status: string;
  error_rate: number;
  recent_errors: number;
  critical_errors: number;
  storage_usage: number;
  active_sessions: number;
  last_updated: string;
}

interface DocumentTemplate {
  id: string;
  name: string;
  document_type: string;
  description: string;
  required_fields_count: number;
  optional_fields_count: number;
  is_active: boolean;
  version: string;
  created_at: string;
  updated_at: string;
}

export default function DocumentManagementPage() {
  const { axiosInstance } = useAuth();
  const [stats, setStats] = useState<DocumentStats | null>(null);
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [templates, setTemplates] = useState<DocumentTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      
      // Fetch stats
      const statsResponse = await axiosInstance.get('/api/chat/documents/analytics/stats');
      setStats(statsResponse.data);
      
      // Fetch health
      const healthResponse = await axiosInstance.get('/api/chat/documents/analytics/health');
      setHealth(healthResponse.data);
      
      // Fetch templates
      const templatesResponse = await axiosInstance.get('/api/chat/documents/templates');
      setTemplates(templatesResponse.data);
      
    } catch (error) {
      console.error('Failed to fetch data:', error);
      toast.error('Failed to load admin data');
    } finally {
      setLoading(false);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatTime = (seconds: number) => {
    if (seconds < 60) return `${seconds.toFixed(1)}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds.toFixed(1)}s`;
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <Card key={i} className="animate-pulse">
              <CardContent className="p-6">
                <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                <div className="h-8 bg-gray-200 rounded w-1/2"></div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Document Management</h1>
          <p className="text-gray-600">Monitor and manage document generation system</p>
        </div>
        <Button onClick={fetchData} variant="outline">
          <BarChart3 className="h-4 w-4 mr-2" />
          Refresh Data
        </Button>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="templates">Templates</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
          <TabsTrigger value="health">System Health</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          {/* Key Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center">
                  <FileText className="h-8 w-8 text-blue-600" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Total Sessions</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {stats?.total_sessions || 0}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center">
                  <CheckCircle className="h-8 w-8 text-green-600" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Completion Rate</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {stats?.completion_rate?.toFixed(1) || 0}%
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center">
                  <TrendingUp className="h-8 w-8 text-purple-600" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Total Documents</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {stats?.total_documents || 0}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center">
                  <Clock className="h-8 w-8 text-orange-600" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Avg Generation Time</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {formatTime(stats?.average_generation_time || 0)}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Document Type Breakdown */}
          <Card>
            <CardHeader>
              <CardTitle>Document Type Usage</CardTitle>
              <CardDescription>Most popular document types</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {stats?.document_type_breakdown && Object.entries(stats.document_type_breakdown).map(([type, count]) => (
                  <div key={type} className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-700">
                      {type.replace('_', ' ').toUpperCase()}
                    </span>
                    <div className="flex items-center space-x-2">
                      <div className="w-32 bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-600 h-2 rounded-full"
                          style={{ 
                            width: `${(count / Math.max(...Object.values(stats.document_type_breakdown))) * 100}%` 
                          }}
                        ></div>
                      </div>
                      <span className="text-sm text-gray-500 w-8">{count}</span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Templates Tab */}
        <TabsContent value="templates" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Document Templates</CardTitle>
              <CardDescription>Manage document templates and their configurations</CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Fields</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Version</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {templates.map((template) => (
                    <TableRow key={template.id}>
                      <TableCell className="font-medium">{template.name}</TableCell>
                      <TableCell>
                        <Badge variant="outline">
                          {template.document_type.replace('_', ' ').toUpperCase()}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="text-sm text-gray-600">
                          {template.required_fields_count} required, {template.optional_fields_count} optional
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant={template.is_active ? "default" : "secondary"}>
                          {template.is_active ? "Active" : "Inactive"}
                        </Badge>
                      </TableCell>
                      <TableCell>{template.version}</TableCell>
                      <TableCell>
                        <div className="flex space-x-2">
                          <Button size="sm" variant="outline">
                            <Eye className="h-4 w-4" />
                          </Button>
                          <Button size="sm" variant="outline">
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button size="sm" variant="outline">
                            <Settings className="h-4 w-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Analytics Tab */}
        <TabsContent value="analytics" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Generation Statistics</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between">
                  <span>Completed Sessions</span>
                  <span className="font-medium">{stats?.completed_sessions || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span>Failed Sessions</span>
                  <span className="font-medium text-red-600">{stats?.failed_sessions || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span>Total Downloads</span>
                  <span className="font-medium">{stats?.total_downloads || 0}</span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Performance Metrics</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <div className="flex justify-between mb-2">
                    <span>Success Rate</span>
                    <span>{stats?.completion_rate?.toFixed(1) || 0}%</span>
                  </div>
                  <Progress value={stats?.completion_rate || 0} className="h-2" />
                </div>
                <div>
                  <div className="flex justify-between mb-2">
                    <span>Average Generation Time</span>
                    <span>{formatTime(stats?.average_generation_time || 0)}</span>
                  </div>
                  <div className="text-sm text-gray-500">
                    Target: &lt; 30 seconds
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* System Health Tab */}
        <TabsContent value="health" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>System Status</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center space-x-2">
                  {health?.status === 'healthy' ? (
                    <CheckCircle className="h-6 w-6 text-green-600" />
                  ) : (
                    <AlertTriangle className="h-6 w-6 text-yellow-600" />
                  )}
                  <span className="text-lg font-medium capitalize">
                    {health?.status || 'Unknown'}
                  </span>
                </div>
                <div className="mt-4 space-y-2">
                  <div className="flex justify-between">
                    <span>Error Rate</span>
                    <span className="font-medium">{health?.error_rate?.toFixed(2) || 0}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Recent Errors</span>
                    <span className="font-medium">{health?.recent_errors || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Critical Errors</span>
                    <span className="font-medium text-red-600">{health?.critical_errors || 0}</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Storage Usage</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span>Total Size</span>
                    <span className="font-medium">{formatFileSize(health?.storage_usage || 0)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Active Sessions</span>
                    <span className="font-medium">{health?.active_sessions || 0}</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Last Updated</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-sm text-gray-600">
                  {health?.last_updated ? new Date(health.last_updated).toLocaleString() : 'Never'}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
