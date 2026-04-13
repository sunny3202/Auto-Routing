import { Rule } from "../../context/RuleSetsContext";
import styles from "../styles/RuleCard.module.css";

interface RuleCardProps {
  rules: Rule[];
}

export default function RuleCard(props: RuleCardProps) {
  return (
    <>
      <div className={styles.RuleContent}>
        <table>
          <thead>
            <tr>
              <th>번호</th>
              <th>규칙</th>
              <th>검증도구</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {Array.isArray(props.rules) && props.rules.length === 0 && (
              <tr>
                <td colSpan={4} style={{ width: "440px" }}>
                  규칙이 없습니다.
                </td>
              </tr>
            )}
            {Array.isArray(props.rules) &&
              props.rules.map((rule, index) => (
                <tr key={index}>
                  <td className={styles.TdNumberField}>{index + 1}</td>
                  <td className={styles.TdRule}>{rule.description}</td>
                  <td className={styles.TdButtonField}>
                    <button disabled={rule.isAutoUpdated}>선택</button>
                  </td>
                  <td className={styles.TdDeleteField}>
                    <button disabled={rule.isAutoUpdated}>X</button>
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>
      <div className={styles.RuleFooter}>
        <button disabled>추가</button>
      </div>
    </>
  );
}
