import { IonButton, IonCard, IonCardContent, IonInput, IonSelect, IonSelectOption, IonSpinner } from "@ionic/react";
import { useEffect, useMemo, useState } from "react";
import { AppShell } from "../components/AppShell";
import { api, money, shortDate } from "../services/api";
import type { Cuadratura, Deposito, Operador, ReporteData } from "../types/api";

const tipos = [
  { tipo: "cuadraturas", label: "Cuadraturas" },
  { tipo: "depositos", label: "Depositos" },
  { tipo: "operadores", label: "Operadores" }
] as const;

export default function ReportesPage() {
  const [tipo, setTipo] = useState<"cuadraturas" | "depositos" | "operadores">("cuadraturas");
  const [fechaDesde, setFechaDesde] = useState("");
  const [fechaHasta, setFechaHasta] = useState("");
  const [operador, setOperador] = useState("");
  const [data, setData] = useState<ReporteData | null>(null);
  const [loading, setLoading] = useState(false);

  const exportUrl = useMemo(
    () => `/exportar/${tipo}.xlsx?fecha_desde=${encodeURIComponent(fechaDesde)}&fecha_hasta=${encodeURIComponent(fechaHasta)}&operador=${encodeURIComponent(operador)}`,
    [tipo, fechaDesde, fechaHasta, operador]
  );

  const load = async () => {
    setLoading(true);
    try {
      setData(await api.reporte(tipo, fechaDesde, fechaHasta, operador));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, [tipo]);

  return (
    <AppShell title="Reportes">
      <div className="page-pad">
        <IonCard className="data-card">
          <IonCardContent>
            <div className="form-grid wide">
              <IonSelect label="Tipo" labelPlacement="stacked" value={tipo} onIonChange={(e) => setTipo(e.detail.value)}>
                {tipos.map((item) => <IonSelectOption key={item.tipo} value={item.tipo}>{item.label}</IonSelectOption>)}
              </IonSelect>
              <IonInput label="Fecha desde" labelPlacement="stacked" type="date" value={fechaDesde} onIonInput={(e) => setFechaDesde(String(e.detail.value ?? ""))} />
              <IonInput label="Fecha hasta" labelPlacement="stacked" type="date" value={fechaHasta} onIonInput={(e) => setFechaHasta(String(e.detail.value ?? ""))} />
              <IonSelect label="Operador" labelPlacement="stacked" value={operador} disabled={tipo === "operadores"} onIonChange={(e) => setOperador(String(e.detail.value ?? ""))}>
                <IonSelectOption value="">Todos</IonSelectOption>
                {data?.operadores.map((op) => <IonSelectOption key={op.codigo} value={op.codigo}>{op.codigo} - {op.descripcion}</IonSelectOption>)}
              </IonSelect>
            </div>
            <div className="form-actions">
              <IonButton onClick={() => void load()}>Filtrar</IonButton>
              <IonButton fill="outline" href={exportUrl}>Excel</IonButton>
              <IonButton fill="outline" href={`/reportes/${tipo}`}>Abrir version imprimible</IonButton>
            </div>
          </IonCardContent>
        </IonCard>

        <IonCard className="table-card">
          <IonCardContent>
            {loading || !data ? <IonSpinner /> : data.rows.length === 0 ? <div className="empty-state">No hay datos para el filtro seleccionado.</div> : (
              <div className="responsive-table">
                {tipo === "cuadraturas" && <CuadraturasTable rows={data.rows as Cuadratura[]} />}
                {tipo === "depositos" && <DepositosTable rows={data.rows as Deposito[]} />}
                {tipo === "operadores" && <OperadoresTable rows={data.rows as Operador[]} />}
              </div>
            )}
          </IonCardContent>
        </IonCard>
      </div>
    </AppShell>
  );
}

function CuadraturasTable({ rows }: { rows: Cuadratura[] }) {
  return (
    <table>
      <thead><tr><th>Numero</th><th>Fecha</th><th>Turno</th><th>Operador</th><th className="num">Comb.</th><th className="num">Ventas</th><th className="num">TransBank</th><th className="num">Transf.</th><th className="num">Piloto</th><th className="num">Diferencia</th></tr></thead>
      <tbody>{rows.map((item) => <tr key={item.id}><td>{item.numero}</td><td>{shortDate(item.fecha)}</td><td>{item.turno}</td><td>{item.operador_codigo}</td><td className="num">{money(item.combust_v)}</td><td className="num">{money(item.ventas_v)}</td><td className="num">{money(item.transbnk_v)}</td><td className="num">{money(item.transfer_v)}</td><td className="num">{money(item.piloto_v)}</td><td className="num">{money(item.diferencia)}</td></tr>)}</tbody>
    </table>
  );
}

function DepositosTable({ rows }: { rows: Deposito[] }) {
  return (
    <table>
      <thead><tr><th>Numero</th><th>Fecha</th><th>Turno</th><th>Operador</th><th className="num">Comb.</th><th className="num">Otros</th><th className="num">Total</th></tr></thead>
      <tbody>{rows.map((item) => <tr key={item.id}><td>{item.numero}</td><td>{shortDate(item.fecha)}</td><td>{item.turno}</td><td>{item.operador_codigo}</td><td className="num">{money(item.val_comb)}</td><td className="num">{money(item.val_otro)}</td><td className="num">{money(item.total_v)}</td></tr>)}</tbody>
    </table>
  );
}

function OperadoresTable({ rows }: { rows: Operador[] }) {
  return (
    <table>
      <thead><tr><th>Codigo</th><th>Nombre</th><th>Estado</th><th>Ingreso</th><th className="num">Tinta</th></tr></thead>
      <tbody>{rows.map((item) => <tr key={item.codigo}><td>{item.codigo}</td><td>{item.descripcion}</td><td>{item.activo ? "Activo" : "Inactivo"}</td><td>{shortDate(item.ingreso)}</td><td className="num">{item.tinta}</td></tr>)}</tbody>
    </table>
  );
}
