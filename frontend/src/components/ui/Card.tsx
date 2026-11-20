import React from "react";
import { cn } from "@/lib/utils";

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  hoverable?: boolean;
}

export const Card: React.FC<CardProps> = ({
  children,
  className,
  hoverable = false,
  ...props
}) => {
  return (
    <div
      className={cn(
        "bg-white dark:bg-studio-900 border border-slate-200 dark:border-studio-800/80 rounded-xl p-5 shadow-sm transition-all",
        hoverable && "hover:border-slate-300 dark:hover:border-studio-700 hover:shadow-md",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
};
