'use client';

import { ProtectedRoute } from '@/components/protected-route';
import { AppShell } from '@/components/layout/app-shell';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Shield, Plus } from 'lucide-react';

function ComplianceContent() {
  return (
    <AppShell breadcrumbs={[{ label: 'Compliance' }]}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h2 className="text-3xl font-bold text-gray-900">Compliance</h2>
            <p className="mt-2 text-gray-600">Track compliance requirements and deadlines</p>
          </div>
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            Add Requirement
          </Button>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Compliance Dashboard</CardTitle>
            <CardDescription>Monitor compliance requirements and deadlines</CardDescription>
          </CardHeader>
          <CardContent className="text-center py-12">
            <Shield className="h-16 w-16 mx-auto mb-4 text-gray-300" />
            <p className="text-gray-600 mb-4">Compliance tracking module coming soon</p>
            <p className="text-sm text-gray-500">
              This will include deadline tracking, compliance alerts, and completion history.
            </p>
          </CardContent>
        </Card>
      </div>
    </AppShell>
  );
}

export default function CompliancePage() {
  return (
    <ProtectedRoute>
      <ComplianceContent />
    </ProtectedRoute>
  );
}

