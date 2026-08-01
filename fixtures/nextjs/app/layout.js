import "./styles.css";

export const metadata = {
  title: "Deploy Skills Next.js Fixture",
  description: "A production deployment validation fixture",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
