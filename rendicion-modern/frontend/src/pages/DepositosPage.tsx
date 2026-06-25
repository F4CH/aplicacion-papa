import { IonButton, IonCard, IonCardContent, IonInput, IonSpinner } from "@ionic/react";
import { useEffect, useState } from "react";
import { useHistory } from "react-router-dom";
import { AppShell } from "../components/AppShell";
import { api, money, shortDate } from "../services/api";
import type { Deposito, Paginated } from "../types/api";

export default function DepositosPage() {
  const history = useHistory();
  const [q, setQ] = useState("");
  const [data, setData] = useState<Paginated<Deposito> | null>(null);

  const load = () => api.depositos(q).then(setData);

  useEffect(() => {
    void load();
  }, []);

  const remove = async (id?: number | null) => {
    if (!id || !confirm("Eliminar deposito?")) return;
    await api.eliminarDeposito(id);
    await load();
  };

  return (
    <AppShell title="Depositos">
      <div className="page-pad">
        <div className="toolbar-row">
          <div className="search-row">
            <IonInput fill="outline" placeholder="Numero, operador o nombre" value={q} onIonInput={(event) => setQ(String(event.detail.value ?? ""))} />
            <IonButton onClick={() => void load()}>Buscar</IonButton>
          </div>
          <IonButton onClick={() => history.push("/depositos/importar")}>Leer boleta</IonButton>
          <IonButton onClick={() => history.push("/depositos/nuevo")}>Nuevo</IonButton>
        </div>
        <IonCard className="table-card">
          <IonCardContent>
            {!data ? <IonSpinner /> : data.rows.length === 0 ? <div className="empty-state">No hay depositos.</div> : (
              <div className="responsive-table">
                <table>
                  <thead><tr><th>Numero</th><th>Fecha</th><th>Turno</th><th>Operador</th><th className="num">Comb.</th><th className="num">Otros</th><th className="num">Total</th><th></th></tr></thead>
                  <tbody>
                    {data.rows.map((item) => (
                      <tr key={item.id}>
                        <td>{item.numero}</td><td>{shortDate(item.fecha)}</td><td>{item.turno}</td><td>{item.operador_codigo}</td>
                        <td className="num">{money(item.val_comb)}</td><td className="num">{money(item.val_otro)}</td><td className="num">{money(item.total_v)}</td>
                        <td><IonButton size="small" fill="clear" onClick={() => history.push(`/depositos/editar/${item.id}`)}>Editar</IonButton><IonButton size="small" color="danger" fill="clear" onClick={() => void remove(item.id)}>Eliminar</IonButton></td>
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
