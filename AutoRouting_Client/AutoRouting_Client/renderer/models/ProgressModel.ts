export interface Progress {
  id: string;
  percentage: number;
}

export interface ProgressApiResponse {
  progress: number;
}

export class ProgressModel {
  private progress: Progress | null = null;
  private listeners: Array<(progress: Progress | null) => void> = [];

  getProgress(): Progress | null {
    return this.progress;
  }

  setProgress(progress: Progress): void {
    this.progress = progress;
    this.notifyListeners();
  }

  clearProgress(): void {
    this.progress = null;
    this.notifyListeners();
  }

  subscribe(listener: (progress: Progress | null) => void): () => void {
    this.listeners.push(listener);
    return () => {
      this.listeners = this.listeners.filter(l => l !== listener);
    };
  }

  private notifyListeners(): void {
    this.listeners.forEach(listener => listener(this.progress));
  }
}

export const progressModel = new ProgressModel();