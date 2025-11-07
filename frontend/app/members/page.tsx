'use client';

import { ProtectedRoute } from '@/components/protected-route';
import { AppShell } from '@/components/layout/app-shell';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Users, Plus } from 'lucide-react';

function MembersContent() {
  return (
    <AppShell breadcrumbs={[{ label: 'Board Members' }]}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h2 className="text-3xl font-bold text-gray-900">Board Members</h2>
            <p className="mt-2 text-gray-600">Manage board member profiles and committee assignments</p>
          </div>
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            Add Member
          </Button>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Board Member Directory</CardTitle>
            <CardDescription>View and manage board member information</CardDescription>
          </CardHeader>
          <CardContent className="text-center py-12">
            <Users className="h-16 w-16 mx-auto mb-4 text-gray-300" />
            <p className="text-gray-600 mb-4">Board member management module coming soon</p>
            <p className="text-sm text-gray-500">
              This will include member profiles, committee assignments, term tracking, and attendance records.
            </p>
          </CardContent>
        </Card>
      </div>
    </AppShell>
  );
}

export default function MembersPage() {
  return (
    <ProtectedRoute>
      <MembersContent />
    </ProtectedRoute>
  );
}

