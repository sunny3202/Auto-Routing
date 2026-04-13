import React from 'react';
import { useRouter } from "next/router";
import Footer from "./components/Footer";
import FormContainer from "./components/FormContainer";
import { useInput } from "../context/InputContext";
import { useFileUpload } from "../hooks/useFileUpload";
import { FileHandler } from "../utils/FileHandler";
import styles from "./styles/input-page.module.css";

const INPUT_FIELD_IDS = {
  FROM_TO_PATH: 'from-to-path-field',
  FROM_TO_FILE: 'from-to-file',
  OBSTACLE_PATH: 'obstacle-path-field',
  OBSTACLE_FILE: 'obstacle-file'
} as const;

const CONFIRMATION_MESSAGES = {
  BACK_NAVIGATION: '입력하신 정보는 저장되지 않습니다. 정말로 뒤로 가시겠습니까?',
  REQUIRED_FILES: 'From-To 정보와 BIM 정보는 필수 입력 사항입니다.'
} as const;

export default function InputPage() {
  const router = useRouter();
  const { inputs, setInputs } = useInput();
  const {
    fromToData,
    obstacleData,
    isUploading,
    error,
    handleFromToFileSelect,
    handleObstacleFileSelect,
    uploadFiles,
    clearError,
    hasRequiredFiles
  } = useFileUpload();
  const [filenames, setFilenames] = React.useState<string>()

  const onFromToFileChange = async (event: React.ChangeEvent<HTMLInputElement>): Promise<void> => {
    const file = event.target.files?.[0];
    if (file) {
      await handleFromToFileSelect(file);
    }


    let name = ""
    let i = 0
    while (i < event.target.files.length) {
      if (i < event.target.files.length - 1) { name = name + event.target.files?.[i].name + ", "; }
      else { name = name + event.target.files?.[i].name }
      i++;
    }
    setFilenames(name)
  };

  const onObstacleFileChange = async (event: React.ChangeEvent<HTMLInputElement>): Promise<void> => {
    const file = event.target.files?.[0];
    if (file) {
      await handleObstacleFileSelect(file);
    }
  };

  const onNextClick = async (): Promise<void> => {
    router.push("/input-validation-progress-page");
  };

  const onBackClick = (): void => {
    const shouldNavigateBack = confirm(CONFIRMATION_MESSAGES.BACK_NAVIGATION);
    if (shouldNavigateBack) {
      router.push("/home");
    }
  };

  const handleFromToButtonClick = (): void => {
    FileHandler.triggerFileInput(INPUT_FIELD_IDS.FROM_TO_FILE);
  };

  const handleObstacleButtonClick = (): void => {
    FileHandler.triggerFileInput(INPUT_FIELD_IDS.OBSTACLE_FILE);
  };

  return (
    <>
      <FormContainer>
        <div className="page-title">라우팅 기본정보 입력</div>

        {error && (
          <div className="error-banner">
            <span>{error}</span>
            <button onClick={clearError} className="error-close-btn">
              ×
            </button>
          </div>
        )}

        <table className={styles.InputTable}>
          <tbody>
            <tr>
              <td style={{ width: "85%" }}>
                <input
                  className="text-field"
                  id={INPUT_FIELD_IDS.FROM_TO_PATH}
                  type="text"
                  placeholder="From-To 정보를 입력해 주세요"
                  value={filenames === "" ? null : filenames}
                  disabled
                />
              </td>
              <td>
                <input
                  id={INPUT_FIELD_IDS.FROM_TO_FILE}
                  type="file"
                  style={{ display: "none" }}
                  onChange={onFromToFileChange}
                  multiple
                />
                <button
                  className="green-btn"
                  onClick={handleFromToButtonClick}
                  disabled={isUploading}
                >
                  열기
                </button>
              </td>
            </tr>
            <tr>
              <td>
                <input
                  className="text-field"
                  id={INPUT_FIELD_IDS.OBSTACLE_PATH}
                  type="text"
                  placeholder="BIM 정보를 입력해 주세요"
                  disabled
                />
              </td>
              <td>
                <input
                  id={INPUT_FIELD_IDS.OBSTACLE_FILE}
                  type="file"
                  accept=".json"
                  style={{ display: "none" }}
                  onChange={onObstacleFileChange}
                />
                <button
                  className="green-btn"
                  onClick={handleObstacleButtonClick}
                  disabled={isUploading}
                >
                  열기
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </FormContainer>

      <Footer>
        { }
        { }
        <button
          onClick={onNextClick}
        >
          다음
        </button>
        <button
          className="back-btn"
          onClick={onBackClick}
          disabled={isUploading}
        >
          뒤로가기
        </button>
      </Footer>
    </>
  );
}
