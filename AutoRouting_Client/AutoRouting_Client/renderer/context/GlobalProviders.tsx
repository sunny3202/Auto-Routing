import { ReactNode } from "react";
import { TargetProvider } from "./TargetContext";
import { InputProvider } from "./InputContext";
import { RuleSetsProvider } from "./RuleSetsContext";

export const GlobalProviders = ({ children }: { children: ReactNode }) => {
  return (
    <TargetProvider>
      <InputProvider>
        <RuleSetsProvider>{children}</RuleSetsProvider>
      </InputProvider>
    </TargetProvider>
  );
};
