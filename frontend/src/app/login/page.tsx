"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { Youtube, ShieldCheck, Key, ArrowRight } from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { useTranslation } from "@/lib/i18n";
import { useStudioStore } from "@/lib/store";
import { fetchApi } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const { t } = useTranslation();
  const setAuth = useStudioStore((state) => state.setAuth);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isRegister, setIsRegister] = useState(false);
  const [fullName, setFullName] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleDevLogin = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await fetchApi<any>("/auth/dev-token", { method: "POST" });
      setAuth(res.access_token, res.user);
      router.push("/");
    } catch (err: any) {
      setError(err.message || "Dev login failed");
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    const endpoint = isRegister ? "/auth/register" : "/auth/login";
    const body = isRegister
      ? { email, password, full_name: fullName }
      : { email, password };

    try {
      const res = await fetchApi<any>(endpoint, {
        method: "POST",
        body: JSON.stringify(body),
      });
      setAuth(res.access_token, res.user);
      router.push("/");
    } catch (err: any) {
      setError(err.message || "Authentication failed");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto py-12 px-4 space-y-6">
      {/* Brand Header */}
      <div className="text-center space-y-2">
        <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-red-600 to-rose-500 text-white flex items-center justify-center mx-auto shadow-lg shadow-red-500/20">
          <Youtube className="w-7 h-7" />
        </div>
        <h1 className="text-2xl font-extrabold tracking-tight text-slate-900 dark:text-white">
          {isRegister ? "Create Studio Account" : t.auth.signInTitle}
        </h1>
        <p className="text-xs text-slate-500 dark:text-slate-400">
          {t.auth.signInSubtitle}
        </p>
      </div>

      <Card className="p-6 space-y-5">
        {error && (
          <div className="p-3 text-xs bg-rose-50 text-rose-600 dark:bg-rose-950/40 dark:text-rose-400 border border-rose-200 dark:border-rose-900 rounded-lg">
            {error}
          </div>
        )}

        {/* 1-Click Dev Creator Login Button */}
        <div className="p-4 rounded-xl bg-gradient-to-r from-red-50 to-purple-50 dark:from-red-950/30 dark:to-purple-950/30 border border-red-200/60 dark:border-red-900/40 text-center space-y-2">
          <p className="text-xs font-semibold text-slate-900 dark:text-slate-200">
            {t.auth.devLoginButton}
          </p>
          <p className="text-[11px] text-slate-500 dark:text-slate-400">
            {t.auth.devLoginHint}
          </p>
          <Button
            type="button"
            variant="secondary"
            size="sm"
            onClick={handleDevLogin}
            isLoading={isLoading}
            className="w-full text-xs font-semibold"
          >
            <ShieldCheck className="w-3.5 h-3.5 mr-1.5 text-emerald-500" />
            <span>Launch with Demo Creator</span>
          </Button>
        </div>

        <div className="relative flex py-1 items-center">
          <div className="flex-grow border-t border-slate-200 dark:border-studio-800" />
          <span className="flex-shrink mx-3 text-[10px] uppercase font-bold text-slate-400">
            Or credentials
          </span>
          <div className="flex-grow border-t border-slate-200 dark:border-studio-800" />
        </div>

        {/* Traditional Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {isRegister && (
            <Input
              label="Full Name"
              type="text"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              placeholder="e.g. Ramesh Varma"
              required
            />
          )}

          <Input
            label={t.auth.email}
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="creator@youtube-studio.ai"
            required
          />

          <Input
            label={t.auth.password}
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••••••"
            required
          />

          <Button
            type="submit"
            isLoading={isLoading}
            className="w-full text-sm font-semibold"
          >
            <span>{isRegister ? "Register Account" : t.auth.signInButton}</span>
            <ArrowRight className="w-4 h-4 ml-1.5" />
          </Button>
        </form>

        <div className="text-center pt-2">
          <button
            type="button"
            onClick={() => setIsRegister(!isRegister)}
            className="text-xs text-red-600 dark:text-red-400 hover:underline"
          >
            {isRegister
              ? "Already have an account? Sign in"
              : "Need a new account? Register here"}
          </button>
        </div>
      </Card>
    </div>
  );
}
