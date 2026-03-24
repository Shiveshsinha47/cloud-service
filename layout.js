export const metadata = {
  title: "Cloud Drive",
  description: "Full Stack Cloud Drive"
};

export default function RootLayout({ children }) {
  return (
    <html>
      <body style={{ fontFamily: "Arial", padding: "40px" }}>
        {children}
      </body>
    </html>
  );
}