/**
 * FilePreview Component
 * Displays preview/indicator for attached files in chat input
 */

import React from 'react';
import { FileAttachment } from '../types/chat';

interface FilePreviewProps {
  file: FileAttachment;
  onRemove: (fileId: string) => void;
}

export const FilePreview: React.FC<FilePreviewProps> = ({ file, onRemove }) => {
  /**
   * Get icon based on file type
   */
  const getFileIcon = (): string => {
    switch (file.type) {
      case 'document':
        return '📄';
      case 'image':
        return '🖼️';
      case 'audio':
        return '🎵';
      default:
        return '📎';
    }
  };

  /**
   * Format file size for display
   */
  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
  };

  return (
    <div className="file-preview">
      <div className="file-preview__container">
        {/* Image preview */}
        {file.type === 'image' && file.preview && (
          <div className="file-preview__image-container">
            <img
              src={file.preview}
              alt={file.name}
              className="file-preview__image"
            />
          </div>
        )}

        {/* File info */}
        <div className="file-preview__info">
          <div className="file-preview__header">
            <span className="file-preview__icon">{getFileIcon()}</span>
            <span className="file-preview__name" title={file.name}>
              {file.name}
            </span>
          </div>
          <div className="file-preview__details">
            <span className="file-preview__size">{formatFileSize(file.size)}</span>
            {file.type === 'audio' && (
              <span className="file-preview__meta">Audio message</span>
            )}
          </div>
        </div>

        {/* Remove button */}
        <button
          className="file-preview__remove-btn"
          onClick={() => onRemove(file.id)}
          title="Remove file"
          aria-label={`Remove ${file.name}`}
        >
          ✕
        </button>
      </div>
    </div>
  );
};

export default FilePreview;
