import type { Metadata } from "next";
import "@/styles/globals.css";
import { Sidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";
import { MobileNav } from "@/components/layout/MobileNav";
import { CreateProjectModal } from "@/components/projects/CreateProjectModal";
import { AuthBoundary } from "@/components/auth/AuthBoundary";

export const metadata: Metadata = {
  title: "AI YouTube Studio Suite",
  description: "Autonomous bilingual AI video creation platform for YouTube Longs and Shorts",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-slate-50 dark:bg-studio-950 text-slate-900 dark:text-slate-100 min-h-screen antialiased flex flex-col md:flex-row">
        <AuthBoundary
          loginContent={
            <main className="flex-1 p-4 md:p-6 lg:p-8 max-w-7xl mx-auto w-full">
              {children}
            </main>
          }
        >
          <>
            {/* Desktop / Tablet Sidebar */}
            <Sidebar />

            {/* Main Content Area */}
            <div className="flex-1 flex flex-col min-w-0 min-h-screen pb-16 md:pb-0">
              <Header />
              <main className="flex-1 p-4 md:p-6 lg:p-8 max-w-7xl mx-auto w-full">
                {children}
              </main>
            </div>

            {/* Mobile Navigation Drawer & Bottom Bar */}
            <MobileNav />

            {/* Global Create Project Modal */}
            <CreateProjectModal />
          </>
        </AuthBoundary>
      </body>
    </html>
  );
}
