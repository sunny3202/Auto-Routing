import apiFetch from '../utils/fetchUtil';

export interface UploadResponse {
  success: boolean;
  fileId: string;
  fileName: string;
  fileSize: number;
  uploadTime: string;
}

export interface FileUploadData {
  fromToFile?: File;
  obstacleFile?: File;
  historyId: string;
}

export class FileUploadService {
  private static readonly UPLOAD_ENDPOINT = '/api/v1/routing/upload/input/';
  private static readonly SUPPORTED_FILE_TYPES = ['.json'];
  private static readonly MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

  static async uploadInputFiles(uploadData: FileUploadData, historyId: string): Promise<UploadResponse> {
    this.validateUploadData(uploadData);
    
    const formData = this.createFormData(uploadData);
    
    try {
      const response = await apiFetch(
        this.UPLOAD_ENDPOINT + historyId,
        'POST',
        formData,
        this.handleUnauthorizedAccess
      );
      
      return this.processUploadResponse(response);
    } catch (error) {
      console.error('File upload failed:', error);
      throw new Error('파일 업로드 중 오류가 발생했습니다.');
    }
  }

  private static validateUploadData(uploadData: FileUploadData): void {
    const { fromToFile, obstacleFile, historyId } = uploadData;
    
    if (!historyId) {
      throw new Error('히스토리 ID가 필요합니다.');
    }
    
    if (!fromToFile && !obstacleFile) {
      throw new Error('최소 하나의 파일이 필요합니다.');
    }
    
    if (fromToFile) {
      this.validateFile(fromToFile, 'From-To');
    }
    
    if (obstacleFile) {
      this.validateFile(obstacleFile, 'BIM');
    }
  }

  private static validateFile(file: File, fileType: string): void {
    if (file.size > this.MAX_FILE_SIZE) {
      throw new Error(`${fileType} 파일 크기가 너무 큽니다. (최대 10MB)`);
    }
    
    const fileExtension = this.getFileExtension(file.name);
    if (!this.SUPPORTED_FILE_TYPES.includes(fileExtension)) {
      throw new Error(`${fileType} 파일은 JSON 형식만 지원됩니다.`);
    }
  }

  private static getFileExtension(fileName: string): string {
    return fileName.toLowerCase().substring(fileName.lastIndexOf('.'));
  }

  private static createFormData(uploadData: FileUploadData): FormData {
    const { fromToFile, obstacleFile, historyId } = uploadData;
    const formData = new FormData();
    
    // Append history ID as metadata
    const metadata = { historyId, uploadTime: new Date().toISOString() };
    formData.append(
      'metadata',
      new Blob([JSON.stringify(metadata)], { type: 'application/json' })
    );
    
    // Append files
    if (fromToFile) {
      formData.append('fromToFile', fromToFile);
    }
    
    if (obstacleFile) {
      formData.append('obstacleFile', obstacleFile);
    }
    
    return formData;
  }

  private static handleUnauthorizedAccess = (): void => {
    console.error('Unauthorized access to upload endpoint');
    throw new Error('인증이 필요합니다.');
  };

  private static processUploadResponse(response: any): UploadResponse {
    if (!response || !response.success) {
      throw new Error('서버에서 업로드를 처리하지 못했습니다.');
    }
    
    return {
      success: response.success,
      fileId: response.fileId || '',
      fileName: response.fileName || '',
      fileSize: response.fileSize || 0,
      uploadTime: response.uploadTime || new Date().toISOString()
    };
  }
}