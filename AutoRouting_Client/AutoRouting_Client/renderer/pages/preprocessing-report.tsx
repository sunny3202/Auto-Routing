import { useRouter } from "next/router";
import Footer from "./components/Footer";
import FormContainer from "./components/FormContainer";
import ValidationResultsTable from "./components/tables/ValidationResultsTable";
import { useInput } from "../context/InputContext";
import { usePreprocessingResults } from "../hooks/usePreprocessingResults";
import apiFetch from "../utils/fetchUtil";

export default function PreprocessingReport() {
  const router = useRouter();
  const { inputs } = useInput();
  const { results, isLoading, error, refetch } = usePreprocessingResults(inputs);

  const totalDevices = new Set(results.map(r => r.deviceName)).size;
  const errorDevices = new Set(
    results.filter(r => r.status === "ERROR").map(r => r.deviceName)
  ).size;
  const warningDevices = new Set(
    results.filter(r => r.status === "WARNING").map(r => r.deviceName)
  ).size;

  const handleNext = async () => {
    router.push("/routing-progress-page");

  };

  const handleBack = () => {
    const shouldGoBack = confirm(
      "전처리 결과는 저장되지 않습니다. 정말로 뒤로 가시겠습니까?"
    );
    if (shouldGoBack) {
      router.push("/rule-collection-page");
    }
  };

  return (
    <>
      <FormContainer>
        <div className="page-title">전처리 결과</div>
        <div className="summary">
          <p>
            총 {totalDevices}개 장비 중, 에러수: {errorDevices} 경고수: {warningDevices}
          </p>
        </div>
        <ValidationResultsTable
          results={results}
          isLoading={isLoading}
          maxHeight="440px"
        />
      </FormContainer>
      <Footer>
        <button
          onClick={handleNext}>
          다음
        </button>
        <button
          className="back-btn"
          onClick={() => {
            handleBack();
          }}
        >
          뒤로가기
        </button>
      </Footer>
    </>
  );
}
