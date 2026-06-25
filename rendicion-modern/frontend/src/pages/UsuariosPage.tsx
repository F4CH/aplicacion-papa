import { IonButton, IonCard, IonCardContent, IonSpinner } from "@ionic/react";
import { useEffect, useState } from "react";
import { useHistory } from "react-router-dom";
import { AppShell } from "../components/AppShell";
import { api } from "../services/api";
import type { User } from "../types/api";

export default function UsuariosPage() {
  const history = useHistory();
  const [rows, setRows] = useState<User[] | null>(null);

  const load = () => api.usuarios().then((data) => setRows(data.rows));

  useEffect(() => {
    void load();
  }, []);

  const deactivate = async (id: number) => {
    if (!confirm("Desactivar usuario?")) return;
    await api.desactivarUsuario(id);
    await load();
  };

  return (
    <AppShell title="Usuarios">
      <div className="page-pad">
        <div className="toolbar-row">
          <IonButton onClick={() => history.push("/usuarios/nuevo")}>Nuevo usuario</IonButton>
        </div>
        <IonCard className="table-card"><IonCardContent>
          {!rows ? <IonSpinner /> : rows.length === 0 ? <div className="empty-state">No hay usuarios.</div> : (
            <div className="responsive-table"><table><thead><tr><th>Usuario</th><th>Nombre</th><th>Rol</th><th>Seguridad</th><th>Estado</th><th></th></tr></thead><tbody>
              {rows.map((item) => <tr key={item.id}><td>{item.codigo}</td><td>{item.nombre}</td><td>{item.rol}</td><td>{item.nivel_seguridad}</td><td>{item.activo ? "Activo" : "Inactivo"}</td><td><IonButton size="small" fill="clear" onClick={() => history.push(`/usuarios/editar/${item.id}`)}>Editar</IonButton><IonButton size="small" color="danger" fill="clear" onClick={() => void deactivate(item.id)}>Desactivar</IonButton></td></tr>)}
            </tbody></table></div>
          )}
        </IonCardContent></IonCard>
      </div>
    </AppShell>
  );
}
