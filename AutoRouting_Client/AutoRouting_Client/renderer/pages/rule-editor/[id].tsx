import React, { useEffect } from "react";
import { useRouter } from "next/router";
import styles from "../styles/rule-editor.module.css";
import FormContainer from "../components/FormContainer";
import Footer from "../components/Footer";
import ParameterCard from "../components/ParameterCard";
import { useTarget } from "../../context/TargetContext";
import RuleCard from "../components/RuleCard";
import {
  Parameter,
  ParameterSet,
  Rule,
  useRuleSets,
} from "../../context/RuleSetsContext";

export default function RuleEditor() {
  const router = useRouter();
  const { id } = router.query;

  const ruleSetsNameRef = React.useRef<HTMLInputElement>(null);

  const { target, setTarget } = useTarget();
  const { ruleSets, setRuleSets } = useRuleSets();

  const [rules, setRules] = React.useState<Rule[]>(
    ruleSets.find((ruleSet) => ruleSet.id === id)?.rules || []
  );
  const [parameterSets, setParameterSets] = React.useState<ParameterSet[]>([]);

  useEffect(() => {
    if (ruleSets.find((ruleSet) => ruleSet.id === id)) {
      ruleSetsNameRef.current!.value = ruleSets.find(
        (ruleSet) => ruleSet.id === id
      )?.name;
      ruleSetsNameRef.current!.disabled = true;
    }

    setRules(ruleSets.find((ruleSet) => ruleSet.id === id)?.rules || []);
    setParameterSets(
      ruleSets.find((ruleSet) => ruleSet.id === id)?.parameterSets || []
    );
  }, [id, ruleSets]);

  return (
    <>
      <FormContainer>
        <table>
          <tbody>
            <tr>
              <td className={styles.TdLabel}>규칙명: </td>
              <td className={styles.TdLabelInput}>
                <input
                  style={{ width: "calc(430px - 20px)" }}
                  type="text"
                  placeholder="규칙명을 입력하세요."
                  ref={ruleSetsNameRef}
                />
              </td>
            </tr>
          </tbody>
        </table>
        <div className={styles.ValidationMsg}>*메시지 입니다.</div>
        <section className={styles.RuleContainer}>
          <div className={styles.CardTitle}>규칙 관리</div>
          <RuleCard rules={rules} />
        </section>
        <section className={styles.CardContainer}>
          {parameterSets.map((parameterSet) => {
            return (
              <ParameterCard
                key={parameterSet.label}
                title={parameterSet.label}
                parameters={parameterSet.parameters}
              />
            );

          })}
        </section>
      </FormContainer>
      <Footer>
        <button
          onClick={() => {
            const flag = confirm("규칙이 저장되었습니다.");
            if (!flag) return;
            router.push("/rule-collection-page");
          }}
          disabled
        >
          저장
        </button>
        <button
          onClick={() => {
            const flag = confirm(
              "편집된 규칙은 저장되지 않습니다. 정말로 취소하시겠습니까?"
            );
            if (!flag) return;
            router.push("/rule-collection-page");
          }}
        >
          취소
        </button>
      </Footer>
    </>
  );
}
