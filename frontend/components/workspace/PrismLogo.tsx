export function PrismLogo({ className = "h-6 w-6" }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 48 48" fill="none" aria-hidden="true">
      <path
        d="M23.5 6.5 41 37.5H6L23.5 6.5Z"
        fill="url(#prism-main)"
        stroke="currentColor"
        strokeWidth="2.5"
        strokeLinejoin="round"
      />
      <path d="M23.5 6.5v31M23.5 37.5 6 37.5M23.5 37.5 41 37.5" stroke="white" strokeOpacity="0.72" strokeWidth="2" />
      <path d="M24 20 41 37.5M24 20 6 37.5" stroke="white" strokeOpacity="0.42" strokeWidth="2" />
      <defs>
        <linearGradient id="prism-main" x1="8" y1="8" x2="40" y2="39" gradientUnits="userSpaceOnUse">
          <stop stopColor="#A7F3D0" />
          <stop offset="0.5" stopColor="#22D3EE" />
          <stop offset="1" stopColor="#6366F1" />
        </linearGradient>
      </defs>
    </svg>
  );
}
