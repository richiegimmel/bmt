'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/auth-context';
import { ProtectedRoute } from '@/components/protected-route';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { AppShell } from '@/components/layout/app-shell';
import { dashboardAPI, type DashboardData } from '@/lib/api/dashboard';
import {
  Calendar,
  CheckSquare,
  FileText,
  Shield,
  TrendingUp,
  Clock,
  AlertCircle,
  Plus,
} from 'lucide-react';
import { useRouter } from 'next/navigation';

function DashboardContent() {
  const { user, getToken } = useAuth();
  const router = useRouter();
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      const token = getToken();
      if (!token) return;
      
      const data = await dashboardAPI.getDashboardData(token);
      setDashboardData(data);
    } catch (error) {
      console.error('Failed to load dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'TBD';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      draft: 'text-gray-600 bg-gray-100',
      scheduled: 'text-blue-600 bg-blue-100',
      completed: 'text-green-600 bg-green-100',
      pending: 'text-amber-600 bg-amber-100',
      overdue: 'text-red-600 bg-red-100',
    };
    return colors[status.toLowerCase()] || 'text-gray-600 bg-gray-100';
  };

  const getPriorityColor = (priority: string | null) => {
    if (!priority) return 'text-gray-600';
    const colors: Record<string, string> = {
      high: 'text-red-600',
      medium: 'text-amber-600',
      low: 'text-green-600',
    };
    return colors[priority.toLowerCase()] || 'text-gray-600';
  };

  return (
    <AppShell breadcrumbs={[{ label: 'Dashboard' }]}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h2 className="text-3xl font-bold text-gray-900">Dashboard</h2>
            <p className="mt-2 text-gray-600">
              Welcome back, {user?.full_name || user?.username}!
            </p>
          </div>
          <div className="flex gap-2">
            <Button onClick={() => router.push('/meetings/new')}>
              <Plus className="h-4 w-4 mr-2" />
              New Meeting
            </Button>
            <Button variant="outline" onClick={() => router.push('/documents')}>
              <Plus className="h-4 w-4 mr-2" />
              Upload Document
            </Button>
          </div>
        </div>

        {loading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          </div>
        ) : dashboardData ? (
          <>
            {/* Key Metrics */}
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4 mb-8">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Upcoming Meetings</CardTitle>
                  <Calendar className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{dashboardData.metrics.upcoming_meetings_count}</div>
                  <p className="text-xs text-muted-foreground">Next 30 days</p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Action Items</CardTitle>
                  <CheckSquare className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{dashboardData.metrics.pending_action_items_count}</div>
                  <p className="text-xs text-muted-foreground">Pending completion</p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Documents</CardTitle>
                  <FileText className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{dashboardData.metrics.documents_pending_review}</div>
                  <p className="text-xs text-muted-foreground">Needing review</p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Compliance</CardTitle>
                  <Shield className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{dashboardData.metrics.compliance_alerts_count}</div>
                  <p className="text-xs text-muted-foreground">Alerts active</p>
                </CardContent>
              </Card>
            </div>

            <div className="grid gap-6 md:grid-cols-2">
              {/* Upcoming Meetings */}
              <Card>
                <CardHeader>
                  <CardTitle>Upcoming Meetings</CardTitle>
                  <CardDescription>Next scheduled board meetings</CardDescription>
                </CardHeader>
                <CardContent>
                  {dashboardData.upcoming_meetings.length > 0 ? (
                    <div className="space-y-4">
                      {dashboardData.upcoming_meetings.map((meeting) => (
                        <div
                          key={meeting.id}
                          className="flex items-start gap-3 p-3 rounded-lg border hover:bg-gray-50 cursor-pointer transition"
                          onClick={() => router.push(`/meetings/${meeting.id}`)}
                        >
                          <Calendar className="h-5 w-5 text-blue-600 mt-0.5" />
                          <div className="flex-1 min-w-0">
                            <p className="font-medium text-gray-900 truncate">{meeting.title}</p>
                            <div className="flex items-center gap-2 mt-1">
                              <Clock className="h-3 w-3 text-gray-400" />
                              <span className="text-sm text-gray-600">
                                {formatDate(meeting.meeting_date)} {meeting.meeting_time && `at ${meeting.meeting_time}`}
                              </span>
                            </div>
                          </div>
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(meeting.status)}`}>
                            {meeting.status}
                          </span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-8 text-gray-500">
                      <Calendar className="h-12 w-12 mx-auto mb-2 text-gray-300" />
                      <p>No upcoming meetings</p>
                      <Button className="mt-4" onClick={() => router.push('/meetings/new')}>
                        Schedule Meeting
                      </Button>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Pending Action Items */}
              <Card>
                <CardHeader>
                  <CardTitle>Action Items</CardTitle>
                  <CardDescription>Tasks requiring attention</CardDescription>
                </CardHeader>
                <CardContent>
                  {dashboardData.pending_action_items.length > 0 ? (
                    <div className="space-y-4">
                      {dashboardData.pending_action_items.map((item) => (
                        <div
                          key={item.id}
                          className="flex items-start gap-3 p-3 rounded-lg border hover:bg-gray-50 cursor-pointer transition"
                          onClick={() => router.push(`/resolutions?action_item=${item.id}`)}
                        >
                          <CheckSquare className={`h-5 w-5 mt-0.5 ${getPriorityColor(item.priority)}`} />
                          <div className="flex-1 min-w-0">
                            <p className="font-medium text-gray-900 truncate">{item.title}</p>
                            <div className="flex items-center gap-2 mt-1">
                              {item.due_date && (
                                <>
                                  <Clock className="h-3 w-3 text-gray-400" />
                                  <span className="text-sm text-gray-600">
                                    Due {formatDate(item.due_date)}
                                  </span>
                                </>
                              )}
                              {item.assigned_to && (
                                <span className="text-sm text-gray-600">• {item.assigned_to}</span>
                              )}
                            </div>
                          </div>
                          {item.priority && (
                            <span className={`text-xs font-medium ${getPriorityColor(item.priority)}`}>
                              {item.priority}
                            </span>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-8 text-gray-500">
                      <CheckSquare className="h-12 w-12 mx-auto mb-2 text-gray-300" />
                      <p>No pending action items</p>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Recent Activity */}
              <Card>
                <CardHeader>
                  <CardTitle>Recent Activity</CardTitle>
                  <CardDescription>Latest updates and changes</CardDescription>
                </CardHeader>
                <CardContent>
                  {dashboardData.recent_activities.length > 0 ? (
                    <div className="space-y-4">
                      {dashboardData.recent_activities.slice(0, 5).map((activity) => (
                        <div
                          key={`${activity.type}-${activity.id}`}
                          className="flex items-start gap-3 p-2 rounded hover:bg-gray-50 cursor-pointer transition"
                          onClick={() => router.push(activity.url)}
                        >
                          <div className="h-8 w-8 rounded-full bg-blue-100 flex items-center justify-center">
                            <FileText className="h-4 w-4 text-blue-600" />
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="font-medium text-gray-900 text-sm truncate">{activity.title}</p>
                            <p className="text-xs text-gray-600">{activity.description}</p>
                            <p className="text-xs text-gray-400 mt-1">
                              {formatDate(activity.created_at)}
                            </p>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-8 text-gray-500">
                      <TrendingUp className="h-12 w-12 mx-auto mb-2 text-gray-300" />
                      <p>No recent activity</p>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Compliance Alerts */}
              <Card>
                <CardHeader>
                  <CardTitle>Compliance Alerts</CardTitle>
                  <CardDescription>Items requiring attention</CardDescription>
                </CardHeader>
                <CardContent>
                  {dashboardData.compliance_alerts.length > 0 ? (
                    <div className="space-y-4">
                      {dashboardData.compliance_alerts.map((alert) => (
                        <div
                          key={alert.id}
                          className="flex items-start gap-3 p-3 rounded-lg border hover:bg-gray-50 cursor-pointer transition"
                          onClick={() => router.push('/compliance')}
                        >
                          <AlertCircle className={`h-5 w-5 mt-0.5 ${
                            alert.days_until_due < 7 ? 'text-red-600' : 
                            alert.days_until_due < 14 ? 'text-amber-600' : 
                            'text-blue-600'
                          }`} />
                          <div className="flex-1 min-w-0">
                            <p className="font-medium text-gray-900 truncate">{alert.title}</p>
                            <div className="flex items-center gap-2 mt-1">
                              <Clock className="h-3 w-3 text-gray-400" />
                              <span className="text-sm text-gray-600">
                                Due {formatDate(alert.due_date)} ({alert.days_until_due} days)
                              </span>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-8 text-gray-500">
                      <Shield className="h-12 w-12 mx-auto mb-2 text-gray-300" />
                      <p>All compliance items up to date</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </>
        ) : null}
      </div>
    </AppShell>
  );
}

export default function DashboardPage() {
  return (
    <ProtectedRoute>
      <DashboardContent />
    </ProtectedRoute>
  );
}
