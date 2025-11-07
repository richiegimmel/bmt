'use client';

import { ProtectedRoute } from '@/components/protected-route';
import { AppShell } from '@/components/layout/app-shell';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { FileCheck, Plus } from 'lucide-react';

function ResolutionsContent() {
  return (
    <AppShell breadcrumbs={[{ label: 'Resolutions' }]}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h2 className="text-3xl font-bold text-gray-900">Resolutions</h2>
            <p className="mt-2 text-gray-600">Track board resolutions and action items</p>
          </div>
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            New Resolution
          </Button>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Resolution Registry</CardTitle>
            <CardDescription>View and manage board resolutions</CardDescription>
          </CardHeader>
          <CardContent className="text-center py-12">
            <FileCheck className="h-16 w-16 mx-auto mb-4 text-gray-300" />
            <p className="text-gray-600 mb-4">Resolution management module coming soon</p>
            <p className="text-sm text-gray-500">
              This will include resolution tracking, voting records, and action item management.
            </p>
          </CardContent>
        </Card>
      </div>
    </AppShell>
  );
}

export default function ResolutionsPage() {
  return (
    <ProtectedRoute>
      <ResolutionsContent />
    </ProtectedRoute>
  );
}

