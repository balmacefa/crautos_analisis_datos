import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Combines Tailwind classes with clsx and merges them correctly with tailwind-merge.
 * Useful for building reusable components with custom className props.
 */
export function cn(...inputs) {
  return twMerge(clsx(inputs));
}
