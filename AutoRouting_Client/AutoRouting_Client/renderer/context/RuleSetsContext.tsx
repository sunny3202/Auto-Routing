import { createContext, ReactNode, useContext, useState } from "react";

export interface Rule {
  description: string;
  isAutoUpdated: boolean;
}

export interface Parameter {
  label: string;
  name: string;
  inputType: "file" | "text" | "number" | "int" | "checkbox" | "coordinate";
  defaultValue?: string | number | boolean | Array<number>;
  min?: number | Array<number>;
  max?: number | Array<number>;
  disabled?: boolean;
}

export interface ParameterSet {
  label: string;
  type:
  | "routingParameters"
  | "resultParameters"
  | "customParametersForVacuum"
  | "preprocessingScripts"
  | "routingScripts"
  | "postprocessingScripts";
  target?: "Vacuum";
  parameters: Parameter[];
}

interface RuleSetProps {
  name: string;
  id: string;
  rules: Rule[];
  parameterSets: ParameterSet[];
}

interface RuleSetsContextProps {
  ruleSets: RuleSetProps[];
  setRuleSets?: (ruleSets: RuleSetProps[]) => void;
}

const V_routingParameters: Parameter[] = [
  {
    label: "경로 간 간섭 허용",
    name: "is_interference_allowed",
    inputType: "checkbox",
    defaultValue: false
  },
  {
    label: "탐색 정밀도 (mm)",
    name: "accuracy",
    inputType: "number",
    defaultValue: 100,
    min: 50,
  },
  {
    label: "최소 직관 길이 (mm)",
    name: "min_straight_distance",
    inputType: "number",
    defaultValue: 150,
    min: 0,
  },
  {
    label: "꺽임 최소화 강도",
    name: "bending_optimization_weight",
    inputType: "number",
    min: 0,
    max: 1,
    defaultValue: 1,
  },
];

const V_resultParameters: Parameter[] = [
  {
    label: "BIM 속성 정보 매핑",
    name: "use_bim_attribute_mapping",
    inputType: "checkbox",
    defaultValue: true,
  },
  {
    label: "라우팅 실패 결과 출력",
    name: "is_failed_result_included",
    inputType: "checkbox",
    defaultValue: false,
  },
];

const V_customParametersForVacuum: Parameter[] = [
  {
    label: "꺽임 집중 위치",
    name: "greedy_turn",
    inputType: "checkbox",
    defaultValue: true,
    disabled: true,
  },
  {
    label: "꺽임 횟수 제한",
    name: "turn_count_limit",
    inputType: "int",
    defaultValue: 6,
    min: 0,
  },
];

const V_preprocessingScripts: Parameter[] = [
  { label: "전처리 설정", name: "pre_processing", inputType: "file" },
  {
    label: "시작 위치 전처리 설정",
    name: "process_start_point",
    inputType: "file",
  },
  {
    label: "종료 위치 전처리 설정",
    name: "process_end_point",
    inputType: "file",
  },
  { label: "확보공간 설정", name: "voxel_area", inputType: "file" },
];

const V_routingScripts: Parameter[] = [
  { label: "우선순위 설정", name: "sort_pocs", inputType: "file" },
  { label: "꺽임 각도 설정", name: "turn_angles", inputType: "file" },
];

const V_postprocessingScripts: Parameter[] = [
  { label: "후처리 설정", name: "post_processing", inputType: "file" },
];

const E_routingParameters: Parameter[] = [
  {
    label: "경로 간 간섭 허용",
    name: "is_interference_allowed",
    inputType: "checkbox",
    defaultValue: false
  },
  {
    label: "탐색 정밀도 (mm)",
    name: "accuracy",
    inputType: "number",
    defaultValue: 200,
    min: 50,
  },
  {
    label: "최소 직관 길이 (mm)",
    name: "min_straight_distance",
    inputType: "number",
    defaultValue: 0,
    min: 0,
  },
  {
    label: "꺽임 최소화 강도",
    name: "bending_optimization_weight",
    inputType: "number",
    min: 0,
    max: 1,
    defaultValue: 0,
  },
];

const E_resultParameters: Parameter[] = [
  {
    label: "BIM 속성 정보 매핑",
    name: "use_bim_attribute_mapping",
    inputType: "checkbox",
    defaultValue: true,
    disabled: true,
  },
  {
    label: "라우팅 실패 결과 출력",
    name: "is_failed_result_included",
    inputType: "checkbox",
    defaultValue: false,
  },
];

const E_preprocessingScripts: Parameter[] = [
  {
    label: "시작 위치 전처리 설정",
    name: "process_start_point",
    inputType: "file",
  },
  {
    label: "종료 위치 전처리 설정",
    name: "process_end_point",
    inputType: "file",
  },
  { label: "확보공간 설정", name: "voxel_area", inputType: "file" },
  { label: "장애물 전처리 설정", name: "restricted_area_setting", inputType: "file" }
];

const E_routingScripts: Parameter[] = [
  { label: "우선순위 설정", name: "sort_pocs", inputType: "file" },
  { label: "POC 매칭 기준 설정", name: "match_pocs", inputType: "file" },
];

const E_postprocessingScripts: Parameter[] = [
  { label: "후처리 설정", name: "post_processing", inputType: "file" },
];

export const RuleSetsContext = createContext<RuleSetsContextProps>({
  ruleSets: [],
});

export const RuleSetsProvider = ({ children }: { children: ReactNode }) => {
  const [ruleSets, setRuleSets] = useState<RuleSetProps[]>([
    {
      name: "진공배관 라우팅",
      id: "0",
      rules: [
        {
          description: "최단거리 라우팅",
          isAutoUpdated: true,
        },
        {
          description: "경로 간 간섭 해소",
          isAutoUpdated: true,
        },
        {
          description: "꺽임 최대 3회까지 허용",
          isAutoUpdated: true,
        },
        {
          description: "Heating Jacket 사이즈 140mm 반영",
          isAutoUpdated: true,
        },
        {
          description: "Super Bellows Size는 FSF에 위치한 PUMP POC 와 동일",
          isAutoUpdated: true,
        },
        {
          description: "단관과 단관 사이 Flage 반영",
          isAutoUpdated: true,
        },
        {
          description: "1,700mm 직관 상단에 위치한 Mid Foreline 연결 시 Flage 반영",
          isAutoUpdated: true,
        },
        {
          description: "CSF Mid Foreline 으로부터 2,135mm + 2,135mm 구간 직관 설계계",
          isAutoUpdated: true,
        },
        {
          description: "꺽임은 1,700mm 구간에서 허용",
          isAutoUpdated: true,
        },
        {
          description: "꺽임 각도 45도 -> 30도 -> 60도 적용",
          isAutoUpdated: true,
        },
        {
          description: "배관 상단 Reducer 반영",
          isAutoUpdated: true,
        },
        {
          description: "Reducer 상단 Flange 사용 및 Dual Bellows 연결",
          isAutoUpdated: true,
        },
        {
          description: "Bellows 상단에 Flange + 150mm 직관 연결 후 설비 연결",
          isAutoUpdated: true,
        },
        {
          description: "Size 별 Reducer 반영",
          isAutoUpdated: true,
        },
      ],
      parameterSets: [
        {
          label: "라우팅 파라미터",
          type: "routingParameters",
          parameters: V_routingParameters,
        },
        {
          label: "결과 파라미터",
          type: "resultParameters",
          parameters: V_resultParameters,
        },
        {
          label: "(진공배관) 커스텀 파라미터",
          type: "customParametersForVacuum",
          target: "Vacuum",
          parameters: V_customParametersForVacuum,
        },
        {
          label: "전처리 스크립트",
          type: "preprocessingScripts",
          parameters: V_preprocessingScripts,
        },
        {
          label: "라우팅 스크립트",
          type: "routingScripts",
          parameters: V_routingScripts,
        },
        {
          label: "후처리 스크립트",
          type: "postprocessingScripts",
          parameters: V_postprocessingScripts,
        },
      ],
    },
    {
      name: "배기배관 라우팅",
      id: "1",
      rules: [
        {
          description: "최단거리 라우팅",
          isAutoUpdated: true,
        },
        {
          description: "경로 간 간섭 해소",
          isAutoUpdated: true,
        },
        {
          description: "입상 배기는 천장 판넬에서 150mm 이상 입상",
          isAutoUpdated: true,
        },
        {
          description: "FFU 상부 700mm 공간 확보",
          isAutoUpdated: true,
        },
        {
          description: "XY 평면상 직선거리 15m 내 위치에 타공",
          isAutoUpdated: true,
        },
        {
          description: "동일 성상 덕트에 타공",
          isAutoUpdated: true,
        },
        {
          description: "타공 간 거리 기준 적용: 100A = 300mm, 150A = 400mm, 200A = 450mm",
          isAutoUpdated: true,
        },
        {
          description: "(타공조건 1) 타공 간 직선 간격은 최소 2,000mm 이상. 외벽에서 최소 50mm 이격",
          isAutoUpdated: true,
        },
        {
          description: "(타공조건 2) 타공조건 1 충종 불가 시, 지그재그 설치. 300mm 이상 이격",
          isAutoUpdated: true,
        },
        {
          description: "(타공조건 3) 타공조건 2 만족 불가 시 100mm 이격",
          isAutoUpdated: true,
        },
        {
          description: "(하부배기) 면 사용 우선순위: 윗면 -> 가까운 옆면 -> 반대 면",
          isAutoUpdated: true,
        },
        {
          description: "(상부배기) 면 사용 우선순위: 가까운 옆면 -> 윗면 -> 반대 면",
          isAutoUpdated: true,
        },
        {
          description: "FAB 중앙부와 가까운 설비부터 타공",
          isAutoUpdated: true,
        },
        {
          description: "DUCT Flange 위 타공 금지. Flange 양 변에서 50mm 이격",
          isAutoUpdated: true,
        },
        {
          description: "하부 배기 연결 시 역구배 금지",
          isAutoUpdated: true,
        },
      ],
      parameterSets: [
        {
          label: "라우팅 파라미터",
          type: "routingParameters",
          parameters: E_routingParameters,
        },
        {
          label: "결과 파라미터",
          type: "resultParameters",
          parameters: E_resultParameters,
        },
        {
          label: "전처리 스크립트",
          type: "preprocessingScripts",
          parameters: E_preprocessingScripts,
        },
        {
          label: "라우팅 스크립트",
          type: "routingScripts",
          parameters: E_routingScripts,
        },
        {
          label: "후처리 스크립트",
          type: "postprocessingScripts",
          parameters: E_postprocessingScripts,
        },
      ],
    }
  ]);

  return (
    <RuleSetsContext.Provider value={{ ruleSets, setRuleSets }}>
      {children}
    </RuleSetsContext.Provider>
  );
};

export const useRuleSets = () => {
  const context = useContext(RuleSetsContext);
  if (!context) {
    throw new Error("useRuleSets must be used within a RuleSetsProvider");
  }
  return context;
};
