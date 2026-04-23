import React from 'react';
import { cn } from '@/lib/utils';

const Badge = ({ children, className = "", variant = "cyan" }) => {
  const variants = {
    cyan: "bg-cyan-500/20 text-cyan-400 border-cyan-500/30",
    purple: "bg-purple-500/20 text-purple-400 border-purple-500/30",
    amber: "bg-amber-500/20 text-amber-400 border-amber-500/30",
    emerald: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
    rose: "bg-rose-500/20 text-rose-400 border-rose-500/30",
  };

  return (
    <span className={cn(
      "px-2 py-0.5 text-[10px] font-bold tracking-wider uppercase rounded-full border",
      variants[variant],
      className
    )}>
      {children}
    </span>
  );
};

export { Badge };
