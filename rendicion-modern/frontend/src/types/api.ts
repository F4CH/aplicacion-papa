export type Role = "consulta" | "operador" | "supervisor" | "admin";

export interface User {
  id: number;
  codigo: string;
  nombre: string;
  rol: Role;
  nivel_seguridad: number;
  menu: string;
  activo: boolean;
}

export interface Stat {
  label: string;
  value: number;
  kind: "number" | "money";
}

export interface Paginated<T> {
  rows: T[];
  page: number;
  per_page: number;
  total: number;
  total_pages: number;
}

export interface Operador {
  codigo: string;
  descripcion: string;
  activo: boolean;
  ingreso: string | null;
  tinta: number;
}

export interface Cuadratura {
  id?: number | null;
  numero: number;
  fecha: string;
  turno: number;
  operador_codigo: string;
  operador_nombre: string;
  combust_v: number;
  otros_v: number;
  deposito_v: number;
  ventas_v: number;
  transbnk_v: number;
  transfer_v: number;
  piloto_v: number;
  diferencia: number;
  recuperar_depositos?: boolean;
}

export interface Deposito {
  id?: number | null;
  numero: number;
  fecha: string;
  turno: number;
  operador_codigo: string;
  operador_nombre: string;
  por_20k: number;
  por_10k: number;
  por_05k: number;
  por_02k: number;
  por_01k: number;
  por_05c: number;
  por_01c: number;
  por_50u: number;
  por_10u: number;
  aceite_c: number;
  promo_c: number;
  aceite_v: number;
  promo_v: number;
  val_comb: number;
  val_otro: number;
  total_v: number;
}

export interface Configuracion {
  id: number;
  empresa: string;
  rut: string;
  local: string;
  email: string;
  membrete: string;
}

export interface ReporteData {
  tipo: "cuadraturas" | "depositos" | "operadores";
  rows: Array<Cuadratura | Deposito | Operador>;
  operadores: Operador[];
  fecha_desde: string;
  fecha_hasta: string;
  operador: string;
}

export interface DashboardData {
  stats: Stat[];
  ultima_cuadratura: string | null;
  ultimo_deposito: string | null;
  recent_cuadraturas: Cuadratura[];
  recent_depositos: Deposito[];
}
