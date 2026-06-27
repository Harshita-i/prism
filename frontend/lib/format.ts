export function percent(value: number | undefined | null): string {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return "--";
  }
  if (value <= 1) {
    return `${Math.round(value * 100)}%`;
  }
  return `${Math.round(value)}%`;
}

export function shortDate(value: string | undefined | null): string {
  if (!value) return "--";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("en", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

export function titleCase(value: string | undefined | null): string {
  if (!value) return "--";
  return value
    .replace(/_/g, " ")
    .split(" ")
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

export function textOf(value: unknown, fallback = "--"): string {
  if (value === undefined || value === null || value === "") return fallback;
  if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }
  return JSON.stringify(value);
}

export function getObjectString(item: Record<string, unknown>, keys: string[], fallback = "--"): string {
  for (const key of keys) {
    const value = item[key];
    if (value !== undefined && value !== null && value !== "") {
      return textOf(value);
    }
  }
  return fallback;
}
