import { IonButton, IonCard, IonCardContent, IonInput, IonSpinner } from "@ionic/react";
import { useEffect, useState } from "react";
import { useHistory } from "react-router-dom";
import { AppShell } from "../components/AppShell";
import { api, money, shortDate } from "../services/api";
import type { Cuadratura, Paginated } from "../types/api";

export default function CuadraturasPage() {
  const history = useHistory();
  const [q, setQ] = useState("");
  const [data, setData] = useState<Paginated<Cuadratura> | null>(null);

  const load = () => api.cuadraturas(q).then(setData);

  useEffect(() => {
    void load();
  }, []);

  const remove = async (id?: number | null) => {
    if (!id || !confirm("Eliminar cuadratura?")) return;
    await api.eliminarCuadratura(id);
    await load();
  };

  return (
    <AppShell title="Cuadraturas">
      <div className="page-pad">
        <div className="toolbar-row">
          <div className="search-row">
            <IonInput fill="outline" placeholder="Numero, operador o nombre" value={q} onIonInput={(event) => setQ(String(event.detail.value ?? ""))} />
            <IonButton onClick={() => void load()}>Buscar</IonButton>
          </div>
          <IonButton onClick={() => history.push("/cuadraturas/importar")}>Leer cuadratura</IonButton>
          <IonButton onClick={() => history.push("/cuadraturas/nuevo")}>Nueva</IonButton>
        </div>
        <IonCard className="table-card">
          <IonCardContent>
            {!data ? <IonSpinner /> : data.rows.length === 0 ? <div className="empty-state">No hay cuadraturas.</div> : (
              <div className="responsive-table">
                <table>
                  <thead><tr><th>Numero</th><th>Fecha</th><th>Turno</th><th>Operador</th><th className="num">Ventas</th><th className="num">Diferencia</th><th></th></tr></thead>
                  <tbody>
                    {data.rows.map((item) => (
                      <tr key={item.id}>
                        <td>{item.numero}</td><td>{shortDate(item.fecha)}</td><td>{item.turno}</td><td>{item.operador_codigo}</td>
                        <td className="num">{money(item.ventas_v)}</td><td className="num">{money(item.diferencia)}</td>
                        <td><IonButton size="small" fill="clear" onClick={() => history.push(`/cuadraturas/editar/${item.id}`)}>Editar</IonButton><IonButton size="small" color="danger" fill="clear" onClick={() => void remove(item.id)}>Eliminar</IonButton></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </IonCardContent>
        </IonCard>
      </div>
    </AppShell>
  );
}
