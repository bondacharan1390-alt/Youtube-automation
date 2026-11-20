"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";

export function AuthBoundary({
  children,
  loginContent,
}: {
  children: React.ReactNode;
  loginContent: React.ReactNode;
}) {
  const pathname = usePathname();
  const router = useRouter();
  const [isAuthorized, setIsAuthorized] = useState(false);

  useEffect(() => {
    setIsAuthorized(false);

    if (pathname === "/login") {
      setIsAuthorized(true);
      return;
    }

    if (localStorage.getItem("studio_token")) {
      setIsAuthorized(true);
      return;
    }

    router.replace("/login");
  }, [pathname, router]);

  if (pathname === "/login") {
    return loginContent;
  }

  if (!isAuthorized) {
    return (
      <div className="flex min-h-screen items-center justify-center text-sm text-slate-500 dark:text-slate-400">
        Checking your studio session...
      </div>
    );
  }

  return children;
}
