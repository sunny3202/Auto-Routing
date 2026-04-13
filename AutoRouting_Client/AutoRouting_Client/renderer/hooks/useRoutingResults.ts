import { useState, useEffect, useCallback } from 'react';
import { ValidationResult } from '../pages/components/tables/ValidationResultsTable';
import apiFetch from '../utils/fetchUtil';
import testset from '../../resources/test_assets/vaccum_test_2/result_report.json';


const ERROR_MESSAGES = {
  FETCH_FAILED: '전처리 결과를 가져오는 중 오류가 발생했습니다.',
  UNAUTHORIZED: '인증이 필요합니다.'
} as const;

const EMPTY_RESULTS: ValidationResult[] = [];

interface useRoutingResultsReturn {
  results: ValidationResult[];
  isLoading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

export const useRoutingResultResults = (inputs: any): useRoutingResultsReturn => {
  const [results, setResults] = useState<ValidationResult[]>(EMPTY_RESULTS);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const hasValidInputs = useCallback((): boolean => {
    return Boolean(inputs && Object.keys(inputs).length > 0);
  }, [inputs]);

  const handleUnauthorizedAccess = useCallback((): void => {
    console.error('Unauthorized access to RoutingResult endpoint');
    setError(ERROR_MESSAGES.UNAUTHORIZED);
  }, []);

  const processRoutingResultResponse = useCallback((apiResponse: unknown): void => {
    try {
      if (!Array.isArray(apiResponse)) {
        throw new Error('Invalid API response format');
      }
      const transformedResults: ValidationResult[] = apiResponse.map((element: any) => ({
        id: element.id,
        status: element.state,
        deviceName: element.equip,
        content: element.description,
        details: element.details || ""
      }));
      setResults(transformedResults);
      setError(null);
    } catch (transformError) {
      console.error('Failed to transform RoutingResult response:', transformError);
      setError(ERROR_MESSAGES.FETCH_FAILED);
      setResults(createMockRoutingResultResults());
    }
  }, []);

  const handleApiError = useCallback((apiError: unknown): void => {
    console.error('RoutingResult API error:', apiError);
    setError(ERROR_MESSAGES.FETCH_FAILED);
    setResults(createMockRoutingResultResults());
  }, []);

  const fetchRoutingResultResults = useCallback(async (): Promise<void> => {
    if (!hasValidInputs()) {
      setResults(createMockRoutingResultResults());
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const apiResponse = await apiFetch(
        `/api/v1/routing/report/result/${inputs.history_id}`,
        'GET',
        undefined,
        handleUnauthorizedAccess
      );

      console.log('RoutingResult API response:', apiResponse);
      processRoutingResultResponse(apiResponse);

    } catch (fetchError) {
      handleApiError(fetchError);
    } finally {
      setIsLoading(false);
    }
  }, [inputs, hasValidInputs, handleUnauthorizedAccess, processRoutingResultResponse, handleApiError]);

  const refetch = useCallback(async (): Promise<void> => {
    await fetchRoutingResultResults();
  }, [fetchRoutingResultResults]);

  useEffect(() => {
    fetchRoutingResultResults();
  }, [fetchRoutingResultResults]);

  return {
    results,
    isLoading,
    error,
    refetch
  };
};

const createMockRoutingResultResults = (): ValidationResult[] => {
  const validationResult = testset.map(item => { return { id: "0", status: item.state, deviceName: item.equip, content: item.description, details: "" } }) as ValidationResult[];
  return validationResult;
}