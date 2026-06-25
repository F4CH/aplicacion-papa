import { IonButton, IonCard, IonCardContent, IonCardHeader, IonCardTitle, IonSpinner } from "@ionic/react";
import { useEffect, useState } from "react";
import { useHistory } from "react-router-dom";
import { AppShell } from "../components/AppShell";
import { api, money, shortDate } from "../services/api";
import type { DashboardData } from "../types/api";

export default function DashboardPage() {
  const history = useHistory();
  const [data, setData] = useState<DashboardData | null>(null);

  useEffect(() => {
    void api.dashboard().then(setData);
  }, []);

  return (
    <AppShell title="Panel">
      <div className="page-pad">
        {!data ? <IonSpinner /> : (
          <>
            <section className="grid-cards">
              {data.stats.map((stat) => (
                <IonCard className="data-card" key={stat.label}>
                  <IonCardHeader><IonCardTitle>{stat.label}</IonCardTitle></IonCardHeader>
                  <IonCardContent><div className="stat-value">{stat.kind === "money" ? money(stat.value) : stat.value.toLocaleString("es-CL")}</div></IonCardContent>
                </IonCard>
              ))}
            </section>
            <section className="quick-actions">
              <IonButton onClick={() => history.push("/cuadraturas")}>Ver cuadraturas</IonButton>
              <IonButton onClick={() => history.push("/cuadraturas/importar")}>Leer cuadratura</IonButton>
              <IonButton onClick={() => history.push("/depositos")}>Ver depositos</IonButton>
              <IonButton onClick={() => history.push("/depositos/importar")}>Leer boleta</IonButton>
              <IonButton fill="outline" onClick={() => history.push("/reportes")}>Reportes</IonButton>
            </section>
            <section className="two-column">
              <Recent title="Cuadraturas recientes" rows={data.recent_cuadraturas.map((item) => [String(item.numero), shortDate(item.fecha), item.operador_codigo, money(item.ventas_v)])} />
              <Recent title="Depositos recientes" rows={data.recent_depositos.map((item) => [String(item.numero), shortDate(item.fecha), item.operador_codigo, money(item.total_v)])} />
            </section>
          </>
        )}
      </div>
    </AppShell>
  );
}

function Recent({ title, rows }: { title: string; rows: string[][] }) {
  return (
    <IonCard className="table-card">
      <IonCardHeader><IonCardTitle>{title}</IonCardTitle></IonCardHeader>
      <IonCardContent>
        {rows.length === 0 ? <div className="empty-state">Sin registros recientes.</div> : (
          <div className="responsive-table">
            <table><tbody>{rows.map((row) => <tr key={row.join("-")}>{row.map((cell) => <td key={cell}>{cell}</td>)}</tr>)}</tbody></table>
          </div>
        )}
      </IonCardContent>
    </IonCard>
  );
}
