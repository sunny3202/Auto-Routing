import React, { useEffect, useState } from "react";
import { useRouter } from "next/router";
import Footer from "./components/Footer";
import FormContainer from "./components/FormContainer";
import { useRoutingProgress } from "../hooks/useRoutingProgress";
import styles from "./styles/routing-progress-page.module.css";
import { useInput } from "../context/InputContext";

export default function InputValidationProcessPage() {
  const router = useRouter();
  const [dotCount, setDotCount] = useState(0);
  const {
    progress,
    isLoading,
    error,
    startProgress,
    stopProgress,
    cancelRouting,
  } = useRoutingProgress();
  const { inputs } = useInput();

  useEffect(() => {
    const interval = setInterval(() => {
      setDotCount((prev) => (prev + 1) % 4);
    }, 500);
    return () => clearInterval(interval);
  }, []);

  const handleBackClick = async () => {
    const flag = confirm(
      "전처리가 중단되며 결과는 저장되지 않습니다. 정말로 뒤로 가시겠습니까?"
    );
    if (!flag) return;

    await cancelRouting(inputs.history_id);
    router.push("/rule-collection-page");
  };

  const getProgressPercentage = (): number => {
    return 100;
  };

  const getProgressValue = (): number => {
    return getProgressPercentage() / 100;
  };

  const isCompleted = progress?.percentage >= 100;

  return (
    <>
      <FormContainer>
        <div className="page-title">
          {isCompleted
            ? "처리 완료!"
            : `처리 중${".".repeat(dotCount)}`}
        </div>

        <span style={{ fontWeight: "bold" }}>{getProgressPercentage()}%</span>
        <progress
          className={styles.Progress}
          value={getProgressValue().toString()}
          max="1"
        />

        {error && (
          <div className={styles.errorMessage}>
            <p>{error}</p>
            <button
              onClick={() => startProgress(inputs.history_id, "preprocessing")}
              className={styles.retryBtn}
            >
              다시 시도
            </button>
          </div>
        )}
      </FormContainer>

      <Footer>
        { }
        <button onClick={() => router.push("/preprocessing-report")}>
          결과 보기
        </button>

        <button className="back-btn" onClick={handleBackClick}>
          뒤로가기
        </button>
      </Footer>
    </>
  );
}
