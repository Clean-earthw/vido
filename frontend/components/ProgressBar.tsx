"use client";

import { motion } from "framer-motion";

interface ProgressBarProps {
  progress: number;
}

export function ProgressBar({ progress }: ProgressBarProps) {
  const clampedProgress = Math.min(Math.max(progress, 0), 100);

  return (
    <div className="w-full">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium text-gray-700">
          {clampedProgress < 100 ? "Generating..." : "Complete!"}
        </span>
        <span className="text-sm font-medium text-gray-700">
          {Math.round(clampedProgress)}%
        </span>
      </div>
      <div className="w-full h-3 bg-gray-200 rounded-full overflow-hidden">
        <motion.div
          className="h-full bg-gradient-to-r from-blue-600 to-purple-600 rounded-full"
          initial={{ width: "0%" }}
          animate={{ width: `${clampedProgress}%` }}
          transition={{ duration: 0.5, ease: "easeInOut" }}
        />
      </div>
    </div>
  );
}