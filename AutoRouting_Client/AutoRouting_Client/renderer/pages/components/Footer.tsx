import styles from "../styles/Footer.module.css";

interface FooterProps {
  children?: React.ReactNode;
}

export default function Footer({ children }: FooterProps) {
  return <footer className={styles.Footer}>{children}</footer>;
}
