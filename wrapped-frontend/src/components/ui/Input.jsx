import React from 'react';
import { cn } from '@/lib/utils';
import { useTheme } from '@/context/ThemeContext';

const Input = React.forwardRef(({ className, type, ...props }, ref) => {
  const { theme } = useTheme();
  
  return (
    <input
      type={type}
      className={cn(
        "flex h-12 w-full rounded-xl border px-4 py-2 text-sm ring-offset-white file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-gray-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50",
        theme === 'dark' 
          ? "bg-white/5 border-white/10 text-white" 
          : "bg-slate-50 border-slate-200 text-slate-900",
        className
      )}
      ref={ref}
      {...props}
    />
  );
});
Input.displayName = "Input";

export { Input };
