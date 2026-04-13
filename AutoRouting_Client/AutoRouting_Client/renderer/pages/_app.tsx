import RootLayout from "../layout";
import "./styles/globals.css";

export default function App({
  Component,
  pageProps,
}: {
  Component: any;
  pageProps: any;
}) {
  return (
    <RootLayout>
      <Component {...pageProps} />
    </RootLayout>
  );
}
