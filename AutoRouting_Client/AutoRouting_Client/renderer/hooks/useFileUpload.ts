import { useState, useCallback } from 'react';
import { FileUploadService, UploadResponse } from '../services/FileUploadService';
import { FileHandler, FileReadResult } from '../utils/FileHandler';

interface UseFileUploadReturn {
  fromToData: any;
  obstacleData: any;
  isUploading: boolean;
  error: string | null;
  handleFromToFileSelect: (file: File) => Promise<void>;
  handleObstacleFileSelect: (file: File) => Promise<void>;
  uploadFiles: (historyId: string) => Promise<UploadResponse | null>;
  clearError: () => void;
  hasRequiredFiles: () => boolean;
}

export const useFileUpload = (): UseFileUploadReturn => {
  const [fromToData, setFromToData] = useState<any>({});
  const [obstacleData, setObstacleData] = useState<any>({});
  const [fromToFile, setFromToFile] = useState<File | null>(null);
  const [obstacleFile, setObstacleFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const clearError = useCallback((): void => {
    setError(null);
  }, []);

  const handleFileRead = useCallback((
    result: FileReadResult,
    setData: (data: any) => void,
    setFile: (file: File | null) => void,
    file: File
  ): void => {
    setData(result.content);
    setFile(file);
    setError(null);
  }, []);

  const handleFromToFileSelect = useCallback(async (file: File): Promise<void> => {
    try {
      const result = await FileHandler.readJsonFile(file);
      handleFileRead(result, setFromToData, setFromToFile, file);
    } catch (fileError) {
      console.error('From-To file read error:', fileError);
      setError(`From-To 파일 오류: ${fileError.message}`);
    }
  }, [handleFileRead]);

  const handleObstacleFileSelect = useCallback(async (file: File): Promise<void> => {
    try {
      const result = await FileHandler.readJsonFile(file);
      handleFileRead(result, setObstacleData, setObstacleFile, file);
      FileHandler.updateFileDisplayField('obstacle-path-field', file.name);
    } catch (fileError) {
      console.error('Obstacle file read error:', fileError);
      setError(`BIM 파일 오류: ${fileError.message}`);
    }
  }, [handleFileRead]);

  const uploadFiles = useCallback(async (historyId: string): Promise<UploadResponse | null> => {
    if (!hasRequiredFiles()) {
      setError('From-To 정보와 BIM 정보는 필수 입력 사항입니다.');
      return null;
    }

    setIsUploading(true);
    setError(null);

    try {
      const uploadData = {
        fromToFile: fromToFile || undefined,
        obstacleFile: obstacleFile || undefined,
        historyId
      };

      const response = await FileUploadService.uploadInputFiles(uploadData, historyId);
      console.log('Upload successful:', response);
      return response;
    } catch (uploadError) {
      console.error('Upload error:', uploadError);
      setError(uploadError.message);
      return null;
    } finally {
      setIsUploading(false);
    }
  }, [fromToFile, obstacleFile]);

  const hasRequiredFiles = useCallback((): boolean => {
    return Object.keys(fromToData).length > 0 && Object.keys(obstacleData).length > 0;
  }, [fromToData, obstacleData]);

  return {
    fromToData,
    obstacleData,
    isUploading,
    error,
    handleFromToFileSelect,
    handleObstacleFileSelect,
    uploadFiles,
    clearError,
    hasRequiredFiles
  };
};