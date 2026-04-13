import styles from "../styles/FormContainer.module.css";

interface FormContainerProps {
  children?: React.ReactNode;
}

export default function FormContainer({ children }: FormContainerProps) {
  return <main className={styles.FormContainer}>{children}</main>;
}
