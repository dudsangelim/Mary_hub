"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";

import { clearTokens, getAccessToken } from "@/lib/auth";

export function useAuth(requireAuth = false) {
  const router = useRouter();
  const pathname = usePathname();
  const [isReady, setIsReady] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    const token = getAccessToken();
    const authenticated = Boolean(token);
    setIsAuthenticated(authenticated);
    setIsReady(true);
    if (requireAuth && !authenticated && pathname !== "/") {
      router.replace("/");
    }
  }, [pathname, requireAuth, router]);

  return {
    isReady,
    isAuthenticated,
    logout() {
      clearTokens();
      router.replace("/");
    }
  };
}
