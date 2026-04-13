import React from "react";
import FormContainer from "./components/FormContainer";
import Footer from "./components/Footer";
import apiFetch from "../utils/fetchUtil";

import { useRouter } from "next/router";
import { useTarget } from "../context/TargetContext";
import { useInput } from "../context/InputContext";

export default function HomePage() {
  const router = useRouter();
  const { target, setTarget } = useTarget();
  const { inputs, setInputs } = useInput();

  const handleRoutingTarget = async (target: "Vacuum" | "Exhaust") => {
    setTarget(target);
    try {
      router.push("/input-page");
    } catch {
      alert("DS AutoRouting 서버와 연결이 되지 않습니다. 네트워크 상태를 확인해 주세요.")
    }

  }


  return (
    <>
      <FormContainer>
        <div className="page-title">라우팅 대상 선택</div>
        <button
          onClick={async () => {
            await handleRoutingTarget("Vacuum");
          }}
        >
          진공배관
        </button>
        <button
          onClick={async () => {
            await handleRoutingTarget("Exhaust");
          }}
        >
          배기배관
        </button>
      </FormContainer>
      <Footer>
        <button
          className="close-btn"
          onClick={() => window.ipc.send("shutdown", true)}
        >
          종료
        </button>
      </Footer>
    </>
  );
}
