const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number
  ) {
    super(message);
    this.name = "ApiError";
  }
}

function extractErrorMessage(detail: unknown, status: number): string {
  if (typeof detail === "string") {
    return detail;
  }
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === "string") return item;
        if (item && typeof item === "object") {
          const loc = Array.isArray((item as any).loc)
            ? (item as any).loc.filter((p: any) => p !== "body").join(".")
            : "";
          const msg = (item as any).msg || (item as any).message || JSON.stringify(item);
          return loc ? `${loc}: ${msg}` : msg;
        }
        return String(item);
      })
      .join("; ");
  }
  if (detail && typeof detail === "object") {
    return (detail as any).msg || (detail as any).message || JSON.stringify(detail);
  }
  return `Request failed with status ${status}`;
}

export async function fetchApi<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = typeof window !== "undefined" ? localStorage.getItem("studio_token") : null;
  
  const headers = new Headers(options.headers || {});
  headers.set("Content-Type", "application/json");
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const url = `${API_BASE_URL}${endpoint.startsWith("/") ? endpoint : `/${endpoint}`}`;

  try {
    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: response.statusText }));
      if (response.status === 401 && typeof window !== "undefined") {
        const token = localStorage.getItem("studio_token");
        if (token) {
          localStorage.removeItem("studio_token");
          if (window.location.pathname !== "/login") {
            window.location.replace("/login");
          }
        }
      }
      const message = extractErrorMessage(errorData.detail, response.status);
      throw new ApiError(message, response.status);
    }

    if (response.status === 204) {
      return {} as T;
    }

    return await response.json();
  } catch (err: unknown) {
    if (!(err instanceof ApiError && err.status < 500)) {
      console.error(`API Error on ${endpoint}:`, err);
    } else {
      console.warn(`API Warning on ${endpoint} (${(err as ApiError).status}):`, (err as ApiError).message);
    }
    throw err;
  }
}
