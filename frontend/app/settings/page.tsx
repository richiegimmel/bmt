'use client';

import { ProtectedRoute } from '@/components/protected-route';
import { AppShell } from '@/components/layout/app-shell';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Settings as SettingsIcon } from 'lucide-react';

function SettingsContent() {
  return (
    <AppShell breadcrumbs={[{ label: 'Settings' }]}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-gray-900">Settings</h2>
          <p className="mt-2 text-gray-600">Manage your account and system preferences</p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Account Settings</CardTitle>
            <CardDescription>Update your profile and preferences</CardDescription>
          </CardHeader>
          <CardContent className="text-center py-12">
            <SettingsIcon className="h-16 w-16 mx-auto mb-4 text-gray-300" />
            <p className="text-gray-600 mb-4">Settings module coming soon</p>
            <p className="text-sm text-gray-500">
              This will include account preferences, notification settings, and system configuration.
            </p>
          </CardContent>
        </Card>
      </div>
    </AppShell>
  );
}

export default function SettingsPage() {
  return (
    <ProtectedRoute>
      <SettingsContent />
    </ProtectedRoute>
  );
}

