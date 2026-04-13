import { useEffect } from "react";
import styles from "../styles/ParameterCard.module.css";
import { Parameter } from "../../context/RuleSetsContext";

interface ParameterCardProps {
  title: string;
  parameters: Parameter[];
}

export default function ParameterCard(props: ParameterCardProps) {
  const onNumberChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const id = event.target.id;
    const rule = props.parameters.find((rule) => rule.name === id);

    if (rule.inputType === "int") {
      if (!/^-?\d+$/.test(event.target.value)) {
        alert("정수만 입력할 수 있습니다.");
        event.target.value = "";
        return;
      }
    }

    if (rule.inputType !== "number") {
      if (rule.min instanceof Array) {
        if (id.includes("_x")) {
          const x = parseFloat(event.target.value);
          if (x < rule.min[0]) {
            alert(`X 좌표가 최소값(${rule.min[0]})보다 작습니다.`);
            event.target.value = rule.min[0].toString();
          }
        }
        if (id.includes("_y")) {
          const y = parseFloat(event.target.value);
          if (y < rule.min[1]) {
            alert(`Y 좌표가 최소값(${rule.min[1]})보다 작습니다.`);
            event.target.value = rule.min[1].toString();
          }
        }
        if (id.includes("_z")) {
          const z = parseFloat(event.target.value);
          if (z < rule.min[2]) {
            alert(`Z 좌표가 최소값(${rule.min[2]})보다 작습니다.`);
            event.target.value = rule.min[2].toString();
          }
        }
      }

      if (rule.max instanceof Array) {
        if (id.includes("_x")) {
          const x = parseFloat(event.target.value);
          if (x > rule.max[0]) {
            alert(`X 좌표가 최대값(${rule.max[0]})보다 큽니다.`);
            event.target.value = rule.max[0].toString();
          }
        }
        if (id.includes("_y")) {
          const y = parseFloat(event.target.value);
          if (y > rule.max[1]) {
            alert(`Y 좌표가 최대값(${rule.max[1]})보다 큽니다.`);
            event.target.value = rule.max[1].toString();
          }
        }
        if (id.includes("_z")) {
          const z = parseFloat(event.target.value);
          if (z > rule.max[2]) {
            alert(`Z 좌표가 최대값(${rule.max[2]})보다 큽니다.`);
            event.target.value = rule.max[2].toString();
          }
        }
      }
    } else {
      const value = parseFloat(event.target.value);
      if (rule.min instanceof Array) {
        alert("최소값 설정 오류입니다. 관리자에게 문의하세요.");
        return;
      }

      if (rule.max instanceof Array) {
        alert("최대값 설정 오류입니다. 관리자에게 문의하세요.");
        return;
      }

      if (rule.min !== undefined && value < rule.min) {
        alert(`입력값이 최소값(${rule.min})보다 작습니다.`);
        event.target.value = rule.min.toString();
      }
      if (rule.max !== undefined && value > rule.max) {
        alert(`입력값이 최대값(${rule.max})보다 큽니다.`);
        event.target.value = rule.max.toString();
      }
    }
  };

  useEffect(() => {
    for (const rule of props.parameters) {
      if (rule.disabled) {
        const input = document.getElementById(rule.name) as HTMLInputElement;
        if (input) {
          input.disabled = true;
        }
      }
    }
  }, []);

  return (
    <div className={styles.Card}>
      <div className={styles.CardTitle}>{props.title}</div>
      <div className={styles.CardContent}>
        <table>
          <tbody>
            {Array.isArray(props.parameters) &&
              props.parameters.map((rule, index) => (
                <tr key={index}>
                  <td className={styles.TdPropertyName}>{rule.label}</td>
                  <td className={styles.TdParameterInput}>
                    {rule.inputType === "file" ? (
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", width: "100%" }}>
                        <input
                          id={rule.name}
                          type="file"
                          accept=".py"
                          onChange={(e) => {
                            const file = e.target.files?.[0];
                            if (file) {
                              document.getElementById(
                                `span_${rule.name}`
                              )!.innerText = file.name;
                            }
                          }}
                        />
                        <span
                          id={`span_${rule.name}`}
                          style={{ flex: 1, textAlign: "left", overflow: "hidden", whiteSpace: "nowrap", textOverflow: "ellipsis" }}
                        >
                          { }
                        </span>
                        <button
                          id={`btn_${rule.name}`}
                          onClick={() => {
                            const input = document.getElementById(
                              rule.name
                            ) as HTMLInputElement;
                            input.click();
                          }}
                        >
                          선택
                        </button>
                      </div>
                    ) : rule.inputType === "text" ? (
                      <input
                        id={rule.name}
                        type="text"
                        defaultValue={rule.defaultValue as string}
                      />
                    ) : rule.inputType === "number" ? (
                      <input
                        id={rule.name}
                        type="number"
                        defaultValue={rule.defaultValue as number}
                        onChange={onNumberChange}
                      />
                    ) : rule.inputType === "checkbox" ? (
                      <input
                        id={rule.name}
                        type="checkbox"
                        defaultChecked={rule.defaultValue as boolean}
                      />
                    ) : rule.inputType === "coordinate" ? (
                      <>
                        <span>X:</span>
                        <input
                          id={`${rule.name}_x`}
                          className={styles.NumberInput}
                          type="number"
                          placeholder="1000000"
                        />
                        <span>Y:</span>
                        <input
                          id={`${rule.name}_y`}
                          className={styles.NumberInput}
                          type="number"
                          placeholder="1000000"
                        />
                        <span>Z:</span>
                        <input
                          id={`${rule.name}_z`}
                          className={styles.NumberInput}
                          type="number"
                          placeholder="1000000"
                        />
                      </>
                    ) : rule.inputType === "int" ? (
                      <input
                        id={rule.name}
                        type="number"
                        defaultValue={rule.defaultValue as number}
                        onChange={onNumberChange}
                      />
                    ) : null}
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
