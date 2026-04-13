import { Progress } from "../models/ProgressModel";

export interface UseProgressTracking {
  progress: Progress | null;
  isLoading: boolean;
  error: string | null;
  startProgress: (requestId: string, type: "result" | "preprocessing" | "validate") => void;
  stopProgress: () => void;
  cancelRouting: (requestId: string) => Promise<boolean>;
}