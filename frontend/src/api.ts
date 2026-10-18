import { fetchJson } from "./transport.mjs";
export { ApiError, waitForBackend } from "./transport.mjs";

export async function api<T>(path: string, body?: unknown): Promise<T> {
  return await fetchJson(
    "/api" + path,
    body === undefined
      ? {}
      : {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        },
    path === "/company/ask" ? 115000 : 60000,
  ) as T;
}
