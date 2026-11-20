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
      throw new ApiError(
        errorData.detail || `Request failed with status ${response.status}`,
        response.status
      );
    }

    if (response.status === 204) {
      return {} as T;
    }

    return await response.json();
  } catch (err: unknown) {
    if (!(err instanceof ApiError && err.status === 401)) {
      console.error(`API Error on ${endpoint}:`, err);
    }
    throw err;
  }
}
