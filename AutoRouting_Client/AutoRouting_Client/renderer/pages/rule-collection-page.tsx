import styles from "./styles/rule-collection-page.module.css";
import { useRouter } from "next/router";
import Footer from "./components/Footer";
import FormContainer from "./components/FormContainer";
import { Rule, useRuleSets } from "../context/RuleSetsContext";
import { useEffect, useState } from "react";
import apiFetch from "../utils/fetchUtil";
import { useInput } from "../context/InputContext";

export default function RuleCollectionPage() {
  const router = useRouter();
  const { ruleSets, setRuleSets } = useRuleSets();

  const [selected, setSelected] = useState<string>("");
  const [rules, setRules] = useState<Rule[]>([]);
  const { inputs } = useInput()

  const onRuleSetClick = (e: React.MouseEvent<HTMLDivElement>) => {
    const target = e.currentTarget as HTMLDivElement;
    setSelected(target.innerText);
  };


  const onNextClick = async (): Promise<void> => {

    router.push("/preprocessing-progress-page");

  };

  useEffect(() => {
    const selectedRuleSet = ruleSets.find(
      (ruleSet) => ruleSet.name === selected
    );
    if (selectedRuleSet) {
      setRules(selectedRuleSet.rules);
    }
  }, [selected]);

  return (
    <>
      <FormContainer>
        <div className="page-title">규칙 선택</div>
        <div
          style={{
            display: "flex",
            flexDirection: "row",
            width: "100%",
            height: "calc(100% - 40px)",
          }}
        >
          <div className={styles.RuleSetsContainer}>
            <div className={styles.ContainerTitle}>규칙 리스트</div>
            {ruleSets.map((ruleSet, index) => (
              <div
                className={
                  selected === ruleSet.name
                    ? `${styles.RuleSetLabel} ${styles.RuleSetLabelSelected}`
                    : styles.RuleSetLabel
                }
                key={index}
                onClick={onRuleSetClick}
              >
                {ruleSet.name}
              </div>
            ))}
          </div>
          <div
            className={styles.RuleSetsContainer}
            style={{
              margin: "0 10px 0 10px",
              width: "250px",
            }}
          >
            <div className={styles.ContainerTitle}>상세 내역</div>
            <table
              style={{
                fontSize: "10px",
                width: "230px",
                margin: "0 5px 0 5px",
              }}
            >
              <thead>
                <tr>
                  <th style={{ width: "30px" }}>번호</th>
                  <th>규칙</th>
                </tr>
              </thead>
              <tbody>
                {rules.map((rule, index) => (
                  <tr key={index}>
                    <td>{index + 1}</td>
                    <td style={{ textAlign: "left" }}>{rule.description}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              width: "80px",
              height: "100%",
            }}
          >
            <button
              onClick={() =>
                router.push(
                  `/rule-editor/${ruleSets.find((ruleSet) => ruleSet.name === selected)?.id ||
                  ""
                  }`
                )
              }
              disabled={selected === ""}
            >
              규칙편집
            </button>
            <button disabled>삭제</button>
            <button onClick={() => router.push("/rule-editor/0")} disabled>
              추가
            </button>
          </div>
        </div>
      </FormContainer>
      <Footer>
        <button
          onClick={() => onNextClick()}
          disabled={selected === ""}
        >
          다음
        </button>
        <button
          className="back-btn"
          onClick={() => {
            router.push("/input-validation-report");
          }}
        >
          뒤로가기
        </button>
      </Footer>
    </>
  );
}
