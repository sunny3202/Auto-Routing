import { createContext, ReactNode, useContext, useState } from "react";

interface TargetContextProps {
  target: "Vacuum" | "Exhaust" | undefined;
  setTarget?: (target: "Vacuum" | "Exhaust" | undefined) => void;
}

export const TargetContext = createContext<TargetContextProps>({
  target: undefined,
});

export const TargetProvider = ({ children }: { children: ReactNode }) => {
  const [target, setTarget] = useState<"Vacuum" | "Exhaust" | undefined>(
    undefined
  );

  return (
    <TargetContext.Provider value={{ target, setTarget }}>
      {children}
    </TargetContext.Provider>
  );
};

export const useTarget = () => {
  const context = useContext(TargetContext);
  if (!context) {
    throw new Error("useTarget must be used within a TargetProvider");
  }
  return context;
};
