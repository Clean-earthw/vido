"use client";

import { ChevronDown } from "lucide-react";
import { useState } from "react";

interface StyleSelectorProps {
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
}

const styles = [
  { value: "cinematic", label: "🎬 Cinematic" },
  { value: "anime", label: "🎨 Anime" },
  { value: "cyberpunk", label: "💜 Cyberpunk" },
  { value: "watercolor", label: "🎨 Watercolor" },
  { value: "fantasy", label: "🧙 Fantasy" },
  { value: "noir", label: "🖤 Noir" },
];

export function StyleSelector({ value, onChange, disabled }: StyleSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);
  const selected = styles.find(s => s.value === value);

  return (
    <div className="relative">
      <label className="block text-gray-700 text-sm font-medium mb-2">
        Style
      </label>
      <button
        type="button"
        onClick={() => !disabled && setIsOpen(!isOpen)}
        disabled={disabled}
        className="w-full bg-white text-gray-800 rounded-xl px-4 py-2.5 border-2 border-gray-300 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition flex items-center justify-between disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <span>{selected?.label || "Select style"}</span>
        <ChevronDown className={`w-4 h-4 transition-transform ${isOpen ? "rotate-180" : ""}`} />
      </button>

      {isOpen && !disabled && (
        <div className="absolute top-full left-0 right-0 mt-1 bg-white border-2 border-gray-300 rounded-xl shadow-lg z-10 overflow-hidden">
          {styles.map((style) => (
            <button
              key={style.value}
              type="button"
              onClick={() => {
                onChange(style.value);
                setIsOpen(false);
              }}
              className={`w-full px-4 py-2.5 text-left hover:bg-gray-50 transition ${
                value === style.value ? "bg-blue-50 text-blue-600" : "text-gray-800"
              }`}
            >
              {style.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}