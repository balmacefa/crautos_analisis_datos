import React from 'react';
import { cn } from '@/lib/utils';
import { useTheme } from '@/context/ThemeContext';
import { ChevronDown } from 'lucide-react';

const Select = React.forwardRef(({ className, children, ...props }, ref) => {
  const { theme } = useTheme();
  
  return (
    <div className="relative group">
      <select
        className={cn(
          "flex h-12 w-full appearance-none rounded-xl border px-4 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 disabled:cursor-not-allowed disabled:opacity-50 transition-all",
          theme === 'dark' 
            ? "bg-white/5 border-white/10 text-white [&>option]:bg-zinc-900" 
            : "bg-slate-50 border-slate-200 text-slate-900 [&>option]:bg-white",
          className
        )}
        ref={ref}
        {...props}
      >
        {children}
      </select>
      <ChevronDown className="absolute right-4 top-1/2 -translate-y-1/2 text-white/30 group-hover:text-cyan-400 transition-colors pointer-events-none" size={16} />
    </div>
  );
});
Select.displayName = "Select";

export { Select };
