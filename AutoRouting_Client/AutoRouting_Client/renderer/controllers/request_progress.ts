import apiFetch from '../utils/fetchUtil';
import { ProgressModel, Progress, ProgressApiResponse } from '../models/ProgressModel';

export class ProgressController {
  private model: ProgressModel;
  private pollingInterval: NodeJS.Timeout | null = null;
  private readonly POLLING_INTERVAL_MS = 2000; // Poll every 2 seconds
  private isPolling = false;

  constructor(model: ProgressModel) {
    this.model = model;
  }

  async fetchProgress(requestId: string, type: string): Promise<Progress | null> {
    try {
      const response: ProgressApiResponse = await apiFetch(
        `/api/v1/routing/progress/${type}/${requestId}`,
        "GET",
        undefined,
        () => {
          console.error('Unauthorized access to progress endpoint');
          this.handleError('인증이 필요합니다.');
        }
      );

      console.log("Progress API Response:", response.progress);

      if (response.progress) {
        console.log("percentage:", response.progress);
        const progress = { id: '', percentage: response.progress } as Progress;
        this.model.setProgress(progress);
        return progress;
      } else {
        throw new Error('Invalid API response');
      }
    } catch (error) {
      console.error('Failed to fetch progress:', error);
      this.handleError('진행 상태를 가져오는 중 오류가 발생했습니다.');
      return null;
    }
  }

  startPolling(requestId: string, type: string): void {
    if (this.isPolling) {
      console.warn('Polling is already active');
      return;
    }

    this.isPolling = true;
    console.log(`Starting progress polling for request: ${requestId}`);

    this.fetchProgress(requestId, type);

    this.pollingInterval = setInterval(async () => {
      const progress = await this.fetchProgress(requestId, type);

    }, this.POLLING_INTERVAL_MS);
  }

  stopPolling(): void {
    if (this.pollingInterval) {
      clearInterval(this.pollingInterval);
      this.pollingInterval = null;
    }
    this.isPolling = false;
    console.log('Progress polling stopped');
  }

  async cancelRouting(requestId: string): Promise<boolean> {
    try {
      const response = await apiFetch(
        `/api/v1/routing/process/stop/${requestId}`,
        "POST",
        undefined,
        () => {
          console.error('Unauthorized access to cancel endpoint');
          this.handleError('인증이 필요합니다.');
        }
      );

      if (response.success) {
        this.stopPolling();
        this.model.clearProgress();
        return true;
      }
      return false;
    } catch (error) {
      console.error('Failed to cancel routing:', error);
      this.handleError('라우팅 취소 중 오류가 발생했습니다.');
      return false;
    }
  }

  resetProgress(): void {
    this.stopPolling();
    this.model.clearProgress();
  }

  private handleError(message: string): void {
    const errorProgress: Progress = {
      id: '',
      percentage: 0,
    };
    this.model.setProgress(errorProgress);
  }

  generateMockProgress(step: number = 1): Progress {
    const steps = [
      '데이터 검증 중',
      '라우팅 규칙 수집 중',
      '경로 분석 중',
      '최적화 수행 중',
      '결과 생성 중'
    ];

    const percentage = Math.min(100, (step / steps.length) * 100);

    return {
      id: 'mock-request-123',
      percentage: Math.round(percentage),
    };
  }
}