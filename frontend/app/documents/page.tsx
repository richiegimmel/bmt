"use client";

import { useState, useEffect, useCallback } from "react";
import { useAuth } from "@/contexts/auth-context";
import { ProtectedRoute } from "@/components/protected-route";
import { AppShell } from "@/components/layout/app-shell";
import { documentsAPI } from "@/lib/api/documents";
import { useDropzone } from "react-dropzone";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import type { Document, DocumentStats } from "@/types/document";
import {
  Upload,
  FileText,
  Download,
  Trash2,
  Search,
  FileIcon,
  Loader2,
  RefreshCw,
} from "lucide-react";

function DocumentsContent() {
  const { getToken } = useAuth();
  const token = getToken();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [stats, setStats] = useState<DocumentStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [processing, setProcessing] = useState<Record<number, boolean>>({});
  const [searchQuery, setSearchQuery] = useState("");
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  // Load documents
  const loadDocuments = useCallback(async () => {
    if (!token) return;

    try {
      setLoading(true);
      const response = await documentsAPI.list(
        {
          search: searchQuery || undefined,
          page,
          page_size: 20,
        },
        token
      );
      setDocuments(response.documents);
      setTotalPages(response.total_pages);
    } catch (error) {
      toast.error("Failed to load documents");
      console.error(error);
    } finally {
      setLoading(false);
    }
  }, [token, searchQuery, page]);

  // Load stats
  const loadStats = useCallback(async () => {
    if (!token) return;

    try {
      const statsData = await documentsAPI.getStats(token);
      setStats(statsData);
    } catch (error) {
      console.error("Failed to load stats:", error);
    }
  }, [token]);

  useEffect(() => {
    loadDocuments();
    loadStats();
  }, [loadDocuments, loadStats]);

  // File upload handler
  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      if (!token) return;

      setUploading(true);

      for (const file of acceptedFiles) {
        try {
          toast.info(`Uploading ${file.name}...`);
          const document = await documentsAPI.upload(file, "/", token);
          toast.success(`Uploaded ${file.name}`);

          // Auto-process the document
          setProcessing((prev) => ({ ...prev, [document.id]: true }));
          try {
            await documentsAPI.process(document.id, {}, token);
            toast.success(`Processed ${file.name}`);
          } catch (error) {
            toast.error(`Failed to process ${file.name}`);
          } finally {
            setProcessing((prev) => ({ ...prev, [document.id]: false }));
          }
        } catch (error: any) {
          toast.error(error.message || `Failed to upload ${file.name}`);
        }
      }

      setUploading(false);
      loadDocuments();
      loadStats();
    },
    [token, loadDocuments, loadStats]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/pdf": [".pdf"],
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
      "application/msword": [".doc"],
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
      "application/vnd.ms-excel": [".xls"],
    },
    maxSize: 50 * 1024 * 1024, // 50MB
    disabled: uploading,
  });

  // Delete document
  const handleDelete = async (id: number, filename: string) => {
    if (!token) return;

    if (!confirm(`Delete ${filename}?`)) return;

    try {
      await documentsAPI.delete(id, token);
      toast.success("Document deleted");
      loadDocuments();
      loadStats();
    } catch (error) {
      toast.error("Failed to delete document");
    }
  };

  // Process document
  const handleProcess = async (id: number, filename: string) => {
    if (!token) return;

    setProcessing((prev) => ({ ...prev, [id]: true }));
    try {
      await documentsAPI.process(id, {}, token);
      toast.success(`Processed ${filename}`);
      loadDocuments();
    } catch (error: any) {
      toast.error(error.message || "Failed to process document");
    } finally {
      setProcessing((prev) => ({ ...prev, [id]: false }));
    }
  };

  // Download document
  const handleDownload = (id: number, filename: string) => {
    if (!token) return;

    const url = documentsAPI.getDownloadUrl(id);
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", filename);
    link.style.display = "none";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Format file size
  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  // Format date
  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  return (
    <AppShell breadcrumbs={[{ label: 'Documents' }]}>
      <div className="container mx-auto px-4 max-w-7xl py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Documents</h1>
          <p className="text-gray-600">Upload and manage your documents</p>
        </div>

        {/* Stats */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-gray-600">
                  Total Documents
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats.total_documents}</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-gray-600">
                  Total Size
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {formatFileSize(stats.total_size_bytes)}
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-gray-600">
                  Processed
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats.processed_count}</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-gray-600">
                  Pending
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats.unprocessed_count}</div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Upload Area */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Upload Documents</CardTitle>
            <CardDescription>
              Drag and drop files or click to browse (PDF, Word, Excel - Max 50MB)
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div
              {...getRootProps()}
              className={`border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-colors ${
                isDragActive
                  ? "border-blue-500 bg-blue-50"
                  : "border-gray-300 hover:border-gray-400"
              } ${uploading ? "opacity-50 cursor-not-allowed" : ""}`}
            >
              <input {...getInputProps()} />
              <Upload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
              {uploading ? (
                <p className="text-gray-600">Uploading...</p>
              ) : isDragActive ? (
                <p className="text-blue-600">Drop files here...</p>
              ) : (
                <>
                  <p className="text-gray-600 mb-2">
                    Drag and drop files here, or click to select
                  </p>
                  <p className="text-sm text-gray-500">
                    Supported: PDF, DOCX, XLSX (up to 50MB each)
                  </p>
                </>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Search */}
        <div className="mb-6 flex gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input
              type="text"
              placeholder="Search documents..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
          <Button onClick={() => loadDocuments()} variant="outline">
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>

        {/* Documents List */}
        <Card>
          <CardHeader>
            <CardTitle>My Documents</CardTitle>
            <CardDescription>
              {documents.length} document{documents.length !== 1 ? "s" : ""}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex justify-center py-12">
                <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
              </div>
            ) : documents.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                <FileIcon className="mx-auto h-12 w-12 mb-4 text-gray-300" />
                <p>No documents found</p>
                <p className="text-sm">Upload your first document to get started</p>
              </div>
            ) : (
              <div className="space-y-4">
                {documents.map((doc) => (
                  <div
                    key={doc.id}
                    className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50"
                  >
                    <div className="flex items-center gap-4 flex-1">
                      <FileText className="h-8 w-8 text-blue-500" />
                      <div className="flex-1">
                        <h3 className="font-medium text-gray-900">
                          {doc.original_filename}
                        </h3>
                        <div className="flex gap-4 text-sm text-gray-500 mt-1">
                          <span>{doc.file_type}</span>
                          <span>{formatFileSize(doc.file_size)}</span>
                          <span>{formatDate(doc.created_at)}</span>
                          {doc.is_processed && doc.chunk_count && (
                            <span className="text-green-600">
                              {doc.chunk_count} chunks
                            </span>
                          )}
                          {!doc.is_processed && (
                            <span className="text-amber-600">Not processed</span>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      {!doc.is_processed && (
                        <Button
                          onClick={() => handleProcess(doc.id, doc.original_filename)}
                          disabled={processing[doc.id]}
                          size="sm"
                          variant="outline"
                        >
                          {processing[doc.id] ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : (
                            <>
                              <RefreshCw className="h-4 w-4 mr-2" />
                              Process
                            </>
                          )}
                        </Button>
                      )}
                      <Button
                        onClick={() => handleDownload(doc.id, doc.original_filename)}
                        size="sm"
                        variant="outline"
                      >
                        <Download className="h-4 w-4" />
                      </Button>
                      <Button
                        onClick={() => handleDelete(doc.id, doc.original_filename)}
                        size="sm"
                        variant="outline"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex justify-center gap-2 mt-6">
                <Button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                  variant="outline"
                  size="sm"
                >
                  Previous
                </Button>
                <span className="flex items-center px-4 text-sm text-gray-600">
                  Page {page} of {totalPages}
                </span>
                <Button
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                  variant="outline"
                  size="sm"
                >
                  Next
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </AppShell>
  );
}

export default function DocumentsPage() {
  return (
    <ProtectedRoute>
      <DocumentsContent />
    </ProtectedRoute>
  );
}
