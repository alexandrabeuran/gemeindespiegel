import type { Metadata } from 'next';
import type { ReactNode } from 'react';
import './global.css';

export const metadata: Metadata = {
  title: 'Gemeindespiegel',
  description: 'Compare Swiss municipalities',
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
