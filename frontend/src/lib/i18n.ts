export type Locale = "es" | "en";

export const LOCALES: Locale[] = ["es", "en"];
export const DEFAULT_LOCALE: Locale = "es";

export function isLocale(value: string): value is Locale {
  return value === "es" || value === "en";
}

export function path(locale: Locale, route = ""): string {
  const clean = route.replace(/^\/+|\/+$/g, "");
  return clean ? `/${locale}/${clean}/` : `/${locale}/`;
}

export function switchLocalePath(currentPath: string, next: Locale): string {
  const parts = currentPath.split("/").filter(Boolean);
  if (parts.length === 0) return path(next);
  parts[0] = next;
  return `/${parts.join("/")}/`;
}
