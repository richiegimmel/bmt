'use client';

import { ProtectedRoute } from '@/components/protected-route';
import { AppShell } from '@/components/layout/app-shell';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Calendar, Plus } from 'lucide-react';

function MeetingsContent() {
  return (
    <AppShell breadcrumbs={[{ label: 'Meetings' }]}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h2 className="text-3xl font-bold text-gray-900">Meetings</h2>
            <p className="mt-2 text-gray-600">Manage board and committee meetings</p>
          </div>
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            Schedule Meeting
          </Button>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Meeting Management</CardTitle>
            <CardDescription>Schedule, manage, and track board meetings</CardDescription>
          </CardHeader>
          <CardContent className="text-center py-12">
            <Calendar className="h-16 w-16 mx-auto mb-4 text-gray-300" />
            <p className="text-gray-600 mb-4">Meeting management module coming soon</p>
            <p className="text-sm text-gray-500">
              This will include meeting scheduling, agenda building, minutes tracking, and more.
            </p>
          </CardContent>
        </Card>
      </div>
    </AppShell>
  );
}

export default function MeetingsPage() {
  return (
    <ProtectedRoute>
      <MeetingsContent />
    </ProtectedRoute>
  );
}

