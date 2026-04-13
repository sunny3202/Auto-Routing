import { useState, useEffect } from 'react';
import { ValidationResult } from '../pages/components/tables/ValidationResultsTable';
import apiFetch from '../utils/fetchUtil';
import testset from '../../resources/test_assets/vaccum_test_2/input_validation_report.json';

interface UseValidationResultsReturn {
  results: ValidationResult[];
  isLoading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

export const useValidationResults = (inputs: any): UseValidationResultsReturn => {
  const [results, setResults] = useState<ValidationResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchValidationResults = async () => {
    if (!inputs || Object.keys(inputs).length === 0) {
      setResults([]);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {

      const res = testset;

      const validationResult = res.map(element => {
        console.log("Validation element:", element);
        return {
          id: "0",
          status: element.state,
          deviceName: element.equip,
          content: element.description,
          details: ""
        } as ValidationResult;
      });

      if (validationResult) {
        setResults(validationResult);
      } else {
        setResults([]);
      }
    } catch (err) {
      console.error('Validation API error:', err);
      setError('검증 결과를 가져오는 중 오류가 발생했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  const refetch = async () => {
    await fetchValidationResults();
  };

  useEffect(() => {
    fetchValidationResults();
  }, [inputs]);

  return { results, isLoading, error, refetch };
};
