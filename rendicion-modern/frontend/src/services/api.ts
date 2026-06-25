import type { Configuracion, Cuadratura, DashboardData, Deposito, Operador, Paginated, ReporteData, User } from "../types/api";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "";

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  const hasBody = options.body !== undefined && !(options.body instanceof FormData);
  if (hasBody && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
    credentials: "include"
  });

  if (!response.ok) {
    let message = `Error HTTP ${response.status}`;
    try {
      const payload = await response.json();
      message = payload.detail ?? message;
    } catch {
      // Mantiene el mensaje HTTP si el backend no devuelve JSON.
    }
    throw new Error(message);
  }

  return response.json() as Promise<T>;
}

export const api = {
  login: (codigo: string, password: string) =>
    request<{ user: User }>("/api/login", {
      method: "POST",
      body: JSON.stringify({ codigo, password })
    }),
  logout: () => request<{ ok: boolean }>("/api/logout", { method: "POST" }),
  me: () => request<{ user: User }>("/api/me"),
  dashboard: () => request<DashboardData>("/api/dashboard"),
  operadores: (activos = false) => request<{ rows: Operador[] }>(`/api/operadores${activos ? "?activos=true" : ""}`),
  operador: (codigo: string) => request<{ item: Operador }>(`/api/operadores/${codigo}`),
  guardarOperador: (payload: Operador, originalCodigo?: string) =>
    request<{ item: Operador }>(originalCodigo ? `/api/operadores/${originalCodigo}` : "/api/operadores", {
      method: originalCodigo ? "PUT" : "POST",
      body: JSON.stringify(payload)
    }),
  desactivarOperador: (codigo: string) => request<{ ok: boolean }>(`/api/operadores/${codigo}`, { method: "DELETE" }),
  usuarios: () => request<{ rows: User[] }>("/api/usuarios"),
  usuario: (id: string) => request<{ item: User }>(`/api/usuarios/${id}`),
  guardarUsuario: (payload: User & { password?: string }, id?: number) =>
    request<{ item: User }>(id ? `/api/usuarios/${id}` : "/api/usuarios", {
      method: id ? "PUT" : "POST",
      body: JSON.stringify(payload)
    }),
  desactivarUsuario: (id: number) => request<{ ok: boolean }>(`/api/usuarios/${id}`, { method: "DELETE" }),
  configuracion: () => request<{ item: Configuracion }>("/api/configuracion"),
  guardarConfiguracion: (payload: Configuracion) =>
    request<{ item: Configuracion }>("/api/configuracion", {
      method: "PUT",
      body: JSON.stringify(payload)
    }),
  cuadraturas: (q = "", page = 1) =>
    request<Paginated<Cuadratura>>(`/api/cuadraturas?page=${page}&q=${encodeURIComponent(q)}`),
  cuadraturaNueva: () => request<{ item: Cuadratura; operadores: Operador[] }>("/api/cuadraturas/nuevo"),
  cuadratura: (id: string) => request<{ item: Cuadratura; operadores: Operador[] }>(`/api/cuadraturas/${id}`),
  guardarCuadratura: (payload: Cuadratura) =>
    request<{ item: Cuadratura }>(payload.id ? `/api/cuadraturas/${payload.id}` : "/api/cuadraturas", {
      method: payload.id ? "PUT" : "POST",
      body: JSON.stringify(payload)
    }),
  eliminarCuadratura: (id: number) => request<{ ok: boolean }>(`/api/cuadraturas/${id}`, { method: "DELETE" }),
  importarCuadratura: (file: File) => {
    const body = new FormData();
    body.append("imagen", file);
    return request<{ item: Cuadratura; operadores: Operador[]; ocr_text: string; ocr_warning: string }>("/api/cuadraturas/importar", {
      method: "POST",
      body
    });
  },
  depositos: (q = "", page = 1) =>
    request<Paginated<Deposito>>(`/api/depositos?page=${page}&q=${encodeURIComponent(q)}`),
  depositoNuevo: () => request<{ item: Deposito; operadores: Operador[] }>("/api/depositos/nuevo"),
  deposito: (id: string) => request<{ item: Deposito; operadores: Operador[] }>(`/api/depositos/${id}`),
  guardarDeposito: (payload: Deposito) =>
    request<{ item: Deposito }>(payload.id ? `/api/depositos/${payload.id}` : "/api/depositos", {
      method: payload.id ? "PUT" : "POST",
      body: JSON.stringify(payload)
    }),
  eliminarDeposito: (id: number) => request<{ ok: boolean }>(`/api/depositos/${id}`, { method: "DELETE" }),
  importarDeposito: (file: File) => {
    const body = new FormData();
    body.append("imagen", file);
    return request<{ item: Deposito; operadores: Operador[]; ocr_text: string; ocr_warning: string }>("/api/depositos/importar", {
      method: "POST",
      body
    });
  },
  reporte: (tipo: string, fechaDesde = "", fechaHasta = "", operador = "") =>
    request<ReporteData>(`/api/reportes/${tipo}?fecha_desde=${encodeURIComponent(fechaDesde)}&fecha_hasta=${encodeURIComponent(fechaHasta)}&operador=${encodeURIComponent(operador)}`)
};

export function money(value: number | null | undefined): string {
  return `$${Number(value ?? 0).toLocaleString("es-CL")}`;
}

export function shortDate(value: string | null | undefined): string {
  if (!value) return "-";
  return value.split("-").reverse().join("-");
}
