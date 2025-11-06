export interface Document {
  id: number;
  filename: string;
  original_filename: string;
  file_path: string;
  file_type: string;
  file_size: number;
  mime_type: string;
  extracted_text: string | null;
  summary: string | null;
  folder: string;
  owner_id: number;
  created_at: string;
  updated_at: string | null;
  is_processed: boolean;
  chunk_count: number | null;
}

export interface DocumentListResponse {
  documents: Document[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface DocumentStats {
  total_documents: number;
  total_size_bytes: number;
  by_file_type: Record<string, number>;
  by_folder: Record<string, number>;
  processed_count: number;
  unprocessed_count: number;
}

export interface DocumentProcessRequest {
  generate_embeddings?: boolean;
  chunk_size?: number;
  chunk_overlap?: number;
}

export interface DocumentProcessResponse {
  document_id: number;
  status: string;
  extracted_text_length: number;
  chunk_count: number;
  embeddings_generated: boolean;
  processing_time_seconds: number;
  message: string;
}

export interface DocumentUploadParams {
  file: File;
  folder?: string;
}

export interface DocumentListParams {
  folder?: string;
  file_type?: string;
  search?: string;
  page?: number;
  page_size?: number;
}
