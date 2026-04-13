import { createContext, ReactNode, useContext, useState } from "react";

interface Inputs {
  history_id: string;
  fromTo: {};
  obstacles: {};
}

interface InputContextProps {
  inputs: Inputs;
  setInputs?: (inputs: Inputs) => void;
}

export const InputContext = createContext<InputContextProps>({
  inputs: { history_id: '', fromTo: {}, obstacles: {} },
});

export const InputProvider = ({ children }: { children: ReactNode }) => {
  const [inputs, setInputs] = useState<Inputs>({
    history_id: '',
    fromTo: {},
    obstacles: {},
  });

  return (
    <InputContext.Provider value={{ inputs, setInputs }}>
      {children}
    </InputContext.Provider>
  );
};

export const useInput = () => {
  const context = useContext(InputContext);
  if (!context) {
    throw new Error("useInput must be used within a InputProvider");
  }
  return context;
};
