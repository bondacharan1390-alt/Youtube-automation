import React from "react";
import { cn } from "@/lib/utils";

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
}

export const Input: React.FC<InputProps> = ({
  label,
  error,
  helperText,
  className,
  id,
  ...props
}) => {
  const inputId = id || (label ? label.toLowerCase().replace(/\s+/g, "-") : undefined);

  return (
    <div className="w-full space-y-1.5">
      {label && (
        <label
          htmlFor={inputId}
          className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider"
        >
          {label}
        </label>
      )}
      <input
        id={inputId}
        className={cn(
          "w-full px-3.5 py-2 text-sm rounded-lg bg-slate-50 dark:bg-studio-950/70 border border-slate-300 dark:border-studio-700 text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent transition-colors",
          error && "border-rose-500 focus:ring-rose-500",
          className
        )}
        {...props}
      />
      {error && <p className="text-xs text-rose-500 mt-1">{error}</p>}
      {helperText && !error && (
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">{helperText}</p>
      )}
    </div>
  );
};
