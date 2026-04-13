import { useState, useEffect, useCallback, useRef } from 'react';
import { Progress, progressModel } from '../models/ProgressModel';
import { ProgressController } from '../controllers/request_progress';
import { UseProgressTracking } from '../types/UseProgressTracking';


export const useRoutingProgress = (): UseProgressTracking => {
  const [progress, setProgress] = useState<Progress | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const controllerRef = useRef<ProgressController | null>(null);

  useEffect(() => {
    if (!controllerRef.current) {
      controllerRef.current = new ProgressController(progressModel);
    }
  }, []);

  useEffect(() => {
    const unsubscribe = progressModel.subscribe((newProgress) => {
      setProgress(newProgress);
      setIsLoading(false);

    });

    return unsubscribe;
  }, []);

  const startProgress = useCallback(
    (
      requestId: string,
      type: "result" | "preprocessing" | "validate" = "result"
    ) => {
      if (!controllerRef.current) return;

      setIsLoading(true);
      setError(null);
      controllerRef.current.startPolling(requestId, type);
    },
    []
  );

  const stopProgress = useCallback(() => {
    if (!controllerRef.current) return;

    controllerRef.current.stopPolling();
    setIsLoading(false);
    setProgress(null)
  }, []);

  const cancelRouting = useCallback(async (requestId: string): Promise<boolean> => {
    if (!controllerRef.current) return false;

    setIsLoading(true);
    const success = await controllerRef.current.cancelRouting(requestId);
    setIsLoading(false);
    return success;
  }, []);

  return {
    progress,
    isLoading,
    error,
    startProgress,
    stopProgress,
    cancelRouting
  };
};