"use client";

import React from 'react';
import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';

const Card = ({ 
  children, 
  className, 
  delay = 0, 
  hover = true,
  variant = 'glass' 
}) => {
  const variants = {
    glass: 'bg-white/5 backdrop-blur-xl border border-white/10',
    dark: 'bg-black/40 backdrop-blur-2xl border border-white/5',
    white: 'bg-white shadow-xl shadow-slate-200 border border-slate-100 text-slate-900',
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.6, delay }}
      whileHover={hover ? { y: -5, transition: { duration: 0.2 } } : {}}
      className={cn(
        'relative overflow-hidden rounded-[2.5rem] p-6 transition-all duration-300',
        variants[variant],
        className
      )}
    >
      {children}
    </motion.div>
  );
};

export { Card };
