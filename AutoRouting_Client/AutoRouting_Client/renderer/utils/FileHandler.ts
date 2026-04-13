export interface FileReadResult {
  content: any;
  fileName: string;
  fileSize: number;
}

export class FileHandler {
  private static readonly JSON_MIME_TYPE = 'application/json';
  private static readonly ENCODING_UTF8 = 'UTF-8';

  static async readJsonFile(file: File): Promise<FileReadResult> {
    this.validateJsonFile(file);
    
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      
      reader.onload = (event) => {
        try {
          const content = this.parseJsonContent(event.target?.result as string);
          resolve({
            content,
            fileName: file.name,
            fileSize: file.size
          });
        } catch (error) {
          reject(new Error(`JSON 파싱 오류: ${error.message}`));
        }
      };
      
      reader.onerror = () => {
        reject(new Error('파일 읽기 중 오류가 발생했습니다.'));
      };
      
      reader.readAsText(file, this.ENCODING_UTF8);
    });
  }

  private static validateJsonFile(file: File): void {
    if (!file) {
      throw new Error('파일이 선택되지 않았습니다.');
    }
    
    if (!file.name.toLowerCase().endsWith('.json')) {
      throw new Error('JSON 파일만 지원됩니다.');
    }
  }

  private static parseJsonContent(content: string): any {
    if (!content.trim()) {
      throw new Error('파일이 비어있습니다.');
    }
    
    try {
      return JSON.parse(content);
    } catch (error) {
      throw new Error('유효하지 않은 JSON 형식입니다.');
    }
  }

  static updateFileDisplayField(fieldId: string, fileName: string): void {
    const field = document.getElementById(fieldId) as HTMLInputElement;
    if (field) {
      field.value = fileName;
    }
  }

  static triggerFileInput(fileInputId: string): void {
    const fileInput = document.getElementById(fileInputId) as HTMLInputElement;
    if (fileInput) {
      fileInput.click();
    }
  }
}