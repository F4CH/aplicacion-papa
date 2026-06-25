import { IonButton, IonCard, IonCardContent, IonCheckbox, IonInput, IonSpinner } from "@ionic/react";
import { useEffect, useState } from "react";
import { useHistory, useParams } from "react-router-dom";
import { AppShell } from "../components/AppShell";
import { api } from "../services/api";
import type { Operador } from "../types/api";

const blank: Operador = {
  codigo: "",
  descripcion: "",
  activo: true,
  ingreso: "",
  tinta: 0
};

export default function OperadorFormPage() {
  const { codigo } = useParams<{ codigo?: string }>();
  const history = useHistory();
  const [item, setItem] = useState<Operador | null>(codigo ? null : blank);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!codigo) return;
    void api.operador(codigo).then((data) => setItem(data.item));
  }, [codigo]);

  const set = (field: keyof Operador, value: string | number | boolean | null) => setItem((current) => current ? { ...current, [field]: value } : current);

  const save = async () => {
    if (!item) return;
    setError("");
    try {
      await api.guardarOperador(item, codigo);
      history.push("/operadores");
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "No se pudo guardar.");
    }
  };

  return (
    <AppShell title={codigo ? "Editar operador" : "Nuevo operador"}>
      <div className="page-pad">
        <IonCard className="data-card">
          <IonCardContent>
            {!item ? <IonSpinner /> : (
              <>
                <div className="form-grid">
                  <IonInput label="Codigo" labelPlacement="stacked" maxlength={5} value={item.codigo} onIonInput={(e) => set("codigo", String(e.detail.value ?? ""))} />
                  <IonInput label="Nombre" labelPlacement="stacked" value={item.descripcion} onIonInput={(e) => set("descripcion", String(e.detail.value ?? ""))} />
                  <IonInput label="Ingreso" labelPlacement="stacked" type="date" value={item.ingreso ?? ""} onIonInput={(e) => set("ingreso", String(e.detail.value ?? ""))} />
                  <IonInput label="Tinta" labelPlacement="stacked" type="number" value={item.tinta} onIonInput={(e) => set("tinta", Number(e.detail.value ?? 0))} />
                  <IonCheckbox checked={item.activo} onIonChange={(e) => set("activo", e.detail.checked)}>Activo</IonCheckbox>
                </div>
                {error && <p className="ion-text-danger">{error}</p>}
                <div className="form-actions">
                  <IonButton onClick={() => void save()}>Guardar</IonButton>
                  <IonButton fill="outline" onClick={() => history.push("/operadores")}>Cancelar</IonButton>
                </div>
              </>
            )}
          </IonCardContent>
        </IonCard>
      </div>
    </AppShell>
  );
}
