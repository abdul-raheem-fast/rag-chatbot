"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/lib/store";

export default function Home() {
  const router = useRouter();
  const { isAuthenticated, loadFromStorage } = useAuthStore();

  useEffect(() => {
    loadFromStorage();
  }, [loadFromStorage]);

  useEffect(() => {
    if (isAuthenticated) {
      router.push("/chat");
    } else {
      router.push("/login");
    }
  }, [isAuthenticated, router]);

  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="animate-pulse text-gray-400">Loading...</div>
    </div>
  );
}
