import { useRouter } from "next/router";
import Footer from "./components/Footer";
import FormContainer from "./components/FormContainer";
import ValidationResultsTable from "./components/tables/ValidationResultsTable";
import { useInput } from "../context/InputContext";
import { useValidationResults } from "../hooks/useValidationResults";

export default function InputValidationReport() {
  const router = useRouter();
  const { inputs } = useInput();
  const { results, isLoading, error, refetch } = useValidationResults(inputs);

  const totalDevices = new Set(results.map((r) => r.deviceName)).size;
  const errorDevices = new Set(
    results.filter((r) => r.status === "ERROR").map((r) => r.deviceName)
  ).size;
  const warningDevices = new Set(results.filter((r) => r.status === "WARNING").map((r) => r.deviceName)).size;

  const handleNext = () => {
    if (results.some((result) => result.status === "ERROR")) {
      const shouldProceed = confirm(
        "에러 발생 장비를 제외한 나머지 장비에 대한 규칙설정을 진행하시겠습니까?"
      );
      if (!shouldProceed) return;
    }
    router.push("/rule-collection-page");
  };

  const handleBack = () => {
    const shouldGoBack = confirm(
      "검증 결과는 저장되지 않습니다. 정말로 뒤로 가시겠습니까?"
    );
    if (shouldGoBack) {
      router.push("/input-page");
    }
  };

  return (
    <>
      <FormContainer>
        <div className="page-header">
          <div className="page-title">라우팅 기본정보 검증 결과</div>
          {error && (
            <div className="error-banner">
              <p>{error}</p>
              <button onClick={refetch} className="retry-btn">
                다시 시도
              </button>
            </div>
          )}
          <div className="summary">
            <p>
              총 {totalDevices}개 장비 중, 에러수: {errorDevices} 경고수: {warningDevices}
            </p>
          </div>
        </div>

        <ValidationResultsTable
          results={results}
          isLoading={isLoading}
          maxHeight="440px"
        />
      </FormContainer>

      <Footer>
        <button onClick={handleNext} disabled={isLoading}>
          다음
        </button>
        <button className="back-btn" onClick={handleBack}>
          뒤로가기
        </button>
      </Footer>
    </>
  );
}
