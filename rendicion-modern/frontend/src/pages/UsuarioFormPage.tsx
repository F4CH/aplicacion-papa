import { IonButton, IonCard, IonCardContent, IonCheckbox, IonInput, IonSelect, IonSelectOption, IonSpinner } from "@ionic/react";
import { useEffect, useState } from "react";
import { useHistory, useParams } from "react-router-dom";
import { AppShell } from "../components/AppShell";
import { api } from "../services/api";
import type { Role, User } from "../types/api";

type EditableUser = User & { password?: string };

const blank: EditableUser = {
  id: 0,
  codigo: "",
  nombre: "",
  rol: "consulta",
  nivel_seguridad: 3,
  menu: "",
  activo: true,
  password: ""
};

const roles: Role[] = ["consulta", "operador", "supervisor", "admin"];

export default function UsuarioFormPage() {
  const { id } = useParams<{ id?: string }>();
  const history = useHistory();
  const [item, setItem] = useState<EditableUser | null>(id ? null : blank);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!id) return;
    void api.usuario(id).then((data) => setItem({ ...data.item, password: "" }));
  }, [id]);

  const set = (field: keyof EditableUser, value: string | number | boolean) => setItem((current) => current ? { ...current, [field]: value } : current);

  const save = async () => {
    if (!item) return;
    setError("");
    try {
      await api.guardarUsuario(item, id ? item.id : undefined);
      history.push("/usuarios");
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "No se pudo guardar.");
    }
  };

  return (
    <AppShell title={id ? "Editar usuario" : "Nuevo usuario"}>
      <div className="page-pad">
        <IonCard className="data-card">
          <IonCardContent>
            {!item ? <IonSpinner /> : (
              <>
                <div className="form-grid">
                  <IonInput label="Codigo" labelPlacement="stacked" value={item.codigo} onIonInput={(e) => set("codigo", String(e.detail.value ?? ""))} />
                  <IonInput label="Nombre" labelPlacement="stacked" value={item.nombre} onIonInput={(e) => set("nombre", String(e.detail.value ?? ""))} />
                  <IonSelect label="Rol" labelPlacement="stacked" value={item.rol} onIonChange={(e) => set("rol", String(e.detail.value))}>
                    {roles.map((role) => <IonSelectOption key={role} value={role}>{role}</IonSelectOption>)}
                  </IonSelect>
                  <IonInput label="Seguridad" labelPlacement="stacked" type="number" min={1} max={9} value={item.nivel_seguridad} onIonInput={(e) => set("nivel_seguridad", Number(e.detail.value ?? 3))} />
                  <IonInput label="Menu" labelPlacement="stacked" value={item.menu} onIonInput={(e) => set("menu", String(e.detail.value ?? ""))} />
                  <IonInput label="Password" labelPlacement="stacked" type="password" placeholder={id ? "Dejar vacio para mantener" : "Minimo 8 caracteres"} value={item.password ?? ""} onIonInput={(e) => set("password", String(e.detail.value ?? ""))} />
                  <IonCheckbox checked={item.activo} onIonChange={(e) => set("activo", e.detail.checked)}>Activo</IonCheckbox>
                </div>
                {error && <p className="ion-text-danger">{error}</p>}
                <div className="form-actions">
                  <IonButton onClick={() => void save()}>Guardar</IonButton>
                  <IonButton fill="outline" onClick={() => history.push("/usuarios")}>Cancelar</IonButton>
                </div>
              </>
            )}
          </IonCardContent>
        </IonCard>
      </div>
    </AppShell>
  );
}
