'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/auth-context';
import { useRouter } from 'next/navigation';
import { getTemplates, generateDocument, generateAndDownload } from '@/lib/api/document-generation';
import type { TemplateInfo, GenerateDocumentRequest } from '@/types/document-generation';
import ProtectedRoute from '@/components/protected-route';
import { toast } from 'sonner';

export default function GeneratePage() {
  return (
    <ProtectedRoute>
      <GeneratePageContent />
    </ProtectedRoute>
  );
}

function GeneratePageContent() {
  const { user } = useAuth();
  const router = useRouter();
  const [templates, setTemplates] = useState<TemplateInfo[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<TemplateInfo | null>(null);
  const [formData, setFormData] = useState<Record<string, any>>({});
  const [format, setFormat] = useState<'docx' | 'pdf'>('docx');
  const [title, setTitle] = useState('');
  const [saveToLibrary, setSaveToLibrary] = useState(true);
  const [loading, setLoading] = useState(false);
  const [loadingTemplates, setLoadingTemplates] = useState(true);

  useEffect(() => {
    loadTemplates();
  }, []);

  const loadTemplates = async () => {
    try {
      setLoadingTemplates(true);
      const data = await getTemplates();
      setTemplates(data.templates);
    } catch (error: any) {
      toast.error('Failed to load templates');
      console.error('Error loading templates:', error);
    } finally {
      setLoadingTemplates(false);
    }
  };

  const handleTemplateSelect = (template: TemplateInfo) => {
    setSelectedTemplate(template);
    setFormData({});
    setTitle(`${template.name} - ${new Date().toLocaleDateString()}`);
  };

  const handleFieldChange = (fieldName: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      [fieldName]: value
    }));
  };

  const handleArrayFieldChange = (fieldName: string, index: number, value: string) => {
    const currentArray = (formData[fieldName] as string[]) || [];
    const newArray = [...currentArray];
    newArray[index] = value;
    handleFieldChange(fieldName, newArray);
  };

  const addArrayItem = (fieldName: string) => {
    const currentArray = (formData[fieldName] as string[]) || [];
    handleFieldChange(fieldName, [...currentArray, '']);
  };

  const removeArrayItem = (fieldName: string, index: number) => {
    const currentArray = (formData[fieldName] as string[]) || [];
    handleFieldChange(fieldName, currentArray.filter((_, i) => i !== index));
  };

  const handleGenerate = async (download: boolean = false) => {
    if (!selectedTemplate) return;

    // Validate required fields
    for (const field of selectedTemplate.required_fields) {
      const value = formData[field];
      if (!value || (Array.isArray(value) && value.length === 0)) {
        toast.error(`Missing required field: ${field}`);
        return;
      }
    }

    if (!title.trim()) {
      toast.error('Please enter a document title');
      return;
    }

    const request: GenerateDocumentRequest = {
      template_type: selectedTemplate.template_type,
      data: formData,
      format,
      title: title.trim(),
      save_to_documents: saveToLibrary && !download
    };

    try {
      setLoading(true);

      if (download) {
        // Direct download
        const blob = await generateAndDownload(request);
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${title.replace(/[^a-z0-9]/gi, '_')}.${format}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        toast.success('Document downloaded successfully');
      } else {
        // Generate and optionally save
        const response = await generateDocument(request);
        toast.success(
          saveToLibrary
            ? 'Document generated and saved to library'
            : 'Document generated successfully'
        );

        if (saveToLibrary && response.document_id) {
          // Optionally redirect to documents page
          // router.push('/documents');
        }
      }

      // Reset form
      setFormData({});
      setSelectedTemplate(null);
      setTitle('');
    } catch (error: any) {
      toast.error(error.message || 'Failed to generate document');
      console.error('Error generating document:', error);
    } finally {
      setLoading(false);
    }
  };

  const renderField = (fieldName: string, fieldInfo: { type: string; description: string }) => {
    const isRequired = selectedTemplate?.required_fields.includes(fieldName);

    if (fieldInfo.type === 'array') {
      const arrayValue = (formData[fieldName] as string[]) || [];

      return (
        <div key={fieldName} className="space-y-2">
          <label className="block text-sm font-medium">
            {fieldName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
            {isRequired && <span className="text-red-500 ml-1">*</span>}
          </label>
          <p className="text-xs text-gray-500">{fieldInfo.description}</p>
          {arrayValue.map((item, index) => (
            <div key={index} className="flex gap-2">
              <input
                type="text"
                value={item}
                onChange={(e) => handleArrayFieldChange(fieldName, index, e.target.value)}
                className="flex-1 rounded-md border border-gray-300 px-3 py-2 text-sm"
                placeholder={`Item ${index + 1}`}
              />
              <button
                type="button"
                onClick={() => removeArrayItem(fieldName, index)}
                className="px-3 py-2 text-sm text-red-600 hover:text-red-700"
              >
                Remove
              </button>
            </div>
          ))}
          <button
            type="button"
            onClick={() => addArrayItem(fieldName)}
            className="px-4 py-2 text-sm text-blue-600 hover:text-blue-700"
          >
            + Add Item
          </button>
        </div>
      );
    }

    return (
      <div key={fieldName}>
        <label className="block text-sm font-medium mb-1">
          {fieldName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
          {isRequired && <span className="text-red-500 ml-1">*</span>}
        </label>
        <p className="text-xs text-gray-500 mb-2">{fieldInfo.description}</p>
        <input
          type="text"
          value={formData[fieldName] || ''}
          onChange={(e) => handleFieldChange(fieldName, e.target.value)}
          className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
          placeholder={fieldInfo.description}
        />
      </div>
    );
  };

  if (loadingTemplates) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-4xl mx-auto">
          <p>Loading templates...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Generate Document</h1>
          <p className="mt-2 text-gray-600">
            Create legal documents from templates
          </p>
        </div>

        {!selectedTemplate ? (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">Select a Template</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {templates.map((template) => (
                <button
                  key={template.template_type}
                  onClick={() => handleTemplateSelect(template)}
                  className="p-6 border-2 border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-colors text-left"
                >
                  <h3 className="font-semibold text-lg mb-2">{template.name}</h3>
                  <p className="text-sm text-gray-600">
                    {template.required_fields.length} required fields
                  </p>
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold">{selectedTemplate.name}</h2>
                <button
                  onClick={() => setSelectedTemplate(null)}
                  className="text-sm text-gray-600 hover:text-gray-900"
                >
                  Change Template
                </button>
              </div>

              <div className="space-y-6">
                {/* Document Title */}
                <div>
                  <label className="block text-sm font-medium mb-1">
                    Document Title <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    className="w-full rounded-md border border-gray-300 px-3 py-2"
                    placeholder="Enter document title"
                  />
                </div>

                {/* Format Selection */}
                <div>
                  <label className="block text-sm font-medium mb-1">Output Format</label>
                  <div className="flex gap-4">
                    <label className="flex items-center">
                      <input
                        type="radio"
                        value="docx"
                        checked={format === 'docx'}
                        onChange={(e) => setFormat(e.target.value as 'docx' | 'pdf')}
                        className="mr-2"
                      />
                      Word (.docx)
                    </label>
                    <label className="flex items-center">
                      <input
                        type="radio"
                        value="pdf"
                        checked={format === 'pdf'}
                        onChange={(e) => setFormat(e.target.value as 'docx' | 'pdf')}
                        className="mr-2"
                      />
                      PDF (.pdf)
                    </label>
                  </div>
                </div>

                {/* Template Fields */}
                <div className="border-t pt-6">
                  <h3 className="font-semibold mb-4">Document Fields</h3>
                  <div className="space-y-4">
                    {Object.entries(selectedTemplate.fields).map(([fieldName, fieldInfo]) =>
                      renderField(fieldName, fieldInfo)
                    )}
                  </div>
                </div>

                {/* Save Option */}
                <div className="border-t pt-6">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={saveToLibrary}
                      onChange={(e) => setSaveToLibrary(e.target.checked)}
                      className="mr-2"
                    />
                    Save to document library
                  </label>
                </div>

                {/* Action Buttons */}
                <div className="flex gap-4">
                  <button
                    onClick={() => handleGenerate(false)}
                    disabled={loading}
                    className="flex-1 bg-blue-600 text-white px-6 py-3 rounded-md hover:bg-blue-700 disabled:opacity-50"
                  >
                    {loading ? 'Generating...' : 'Generate Document'}
                  </button>
                  <button
                    onClick={() => handleGenerate(true)}
                    disabled={loading}
                    className="flex-1 bg-green-600 text-white px-6 py-3 rounded-md hover:bg-green-700 disabled:opacity-50"
                  >
                    {loading ? 'Generating...' : 'Generate & Download'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
