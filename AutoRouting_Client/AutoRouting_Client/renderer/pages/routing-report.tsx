import { useRouter } from "next/router";
import Footer from "./components/Footer";
import FormContainer from "./components/FormContainer";
import { useRoutingResultResults } from "../hooks/useRoutingResults";
import { useInput } from "../context/InputContext";
import ValidationResultsTable from "./components/tables/ValidationResultsTable";
import apiFetch from "../utils/fetchUtil";

export default function RoutingReport() {
  const router = useRouter();
  const { inputs } = useInput();
  const { results, isLoading, error, refetch } = useRoutingResultResults(inputs);

  const totalDevices = new Set(results.map(r => r.deviceName)).size;
  const errorDevices = new Set(
    results.filter(r => r.status === "ERROR").map(r => r.deviceName)
  ).size;
  const warningDevices = new Set(
    results.filter(r => r.status === "WARNING").map(r => r.deviceName)
  ).size;

  const handleDownload = async () => {
    const blob = new Blob([JSON.stringify({})], { type: "application/json" });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "routing_report.json";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  }
  return (
    <>
      <FormContainer>
        <div className="page-title">라우팅 결과</div>
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
        <button className="green-btn"
          onClick={handleDownload}
        >다운로드</button>
        <button
          className="close-btn"
          onClick={() => {
            const flag = confirm(
              "결과를 다시 다운로드 받을 수 없습니다. 정말로 종료하시겠습니까?"
            );
            if (!flag) return;
            window.ipc.send("shutdown", true);
          }}
        >
          종료
        </button>
      </Footer>
    </>
  );
}
