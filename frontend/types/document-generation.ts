/**
 * Types for document generation feature
 */

export interface TemplateField {
  type: string;
  description: string;
}

export interface TemplateInfo {
  template_type: string;
  name: string;
  required_fields: string[];
  optional_fields: string[];
  fields: Record<string, TemplateField>;
}

export interface GenerateDocumentRequest {
  template_type: string;
  data: Record<string, any>;
  format: 'docx' | 'pdf';
  title: string;
  save_to_documents: boolean;
}

export interface GenerateDocumentResponse {
  document_id?: number;
  filename: string;
  format: string;
  size: number;
  download_url: string;
}
