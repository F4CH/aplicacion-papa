import { IonButton, IonCard, IonCardContent, IonSpinner } from "@ionic/react";
import { useEffect, useState } from "react";
import { useHistory } from "react-router-dom";
import { AppShell } from "../components/AppShell";
import { api, shortDate } from "../services/api";
import type { Operador } from "../types/api";

export default function OperadoresPage() {
  const history = useHistory();
  const [rows, setRows] = useState<Operador[] | null>(null);

  const load = () => api.operadores().then((data) => setRows(data.rows));

  useEffect(() => {
    void load();
  }, []);

  const deactivate = async (codigo: string) => {
    if (!confirm("Desactivar operador?")) return;
    await api.desactivarOperador(codigo);
    await load();
  };

  return (
    <AppShell title="Operadores">
      <div className="page-pad">
        <div className="toolbar-row">
          <IonButton onClick={() => history.push("/operadores/nuevo")}>Nuevo operador</IonButton>
        </div>
        <IonCard className="table-card"><IonCardContent>
          {!rows ? <IonSpinner /> : rows.length === 0 ? <div className="empty-state">No hay operadores.</div> : (
            <div className="responsive-table"><table><thead><tr><th>Codigo</th><th>Nombre</th><th>Estado</th><th>Ingreso</th><th className="num">Tinta</th><th></th></tr></thead><tbody>
              {rows.map((item) => <tr key={item.codigo}><td>{item.codigo}</td><td>{item.descripcion}</td><td>{item.activo ? "Activo" : "Inactivo"}</td><td>{shortDate(item.ingreso)}</td><td className="num">{item.tinta}</td><td><IonButton size="small" fill="clear" onClick={() => history.push(`/operadores/editar/${item.codigo}`)}>Editar</IonButton><IonButton size="small" color="danger" fill="clear" onClick={() => void deactivate(item.codigo)}>Desactivar</IonButton></td></tr>)}
            </tbody></table></div>
          )}
        </IonCardContent></IonCard>
      </div>
    </AppShell>
  );
}
