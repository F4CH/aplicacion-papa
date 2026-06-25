import { IonButton, IonCard, IonCardContent, IonInput, IonSpinner, IonTextarea } from "@ionic/react";
import { useEffect, useState } from "react";
import { AppShell } from "../components/AppShell";
import { api } from "../services/api";
import type { Configuracion } from "../types/api";

export default function ConfiguracionPage() {
  const [item, setItem] = useState<Configuracion | null>(null);
  const [message, setMessage] = useState("");

  useEffect(() => {
    void api.configuracion().then((data) => setItem(data.item));
  }, []);

  const set = (field: keyof Configuracion, value: string) => setItem((current) => current ? { ...current, [field]: value } : current);

  const save = async () => {
    if (!item) return;
    const data = await api.guardarConfiguracion(item);
    setItem(data.item);
    setMessage("Configuracion guardada.");
  };

  return (
    <AppShell title="Configuracion">
      <div className="page-pad">
        <IonCard className="data-card"><IonCardContent>
          {!item ? <IonSpinner /> : (
            <>
              <div className="form-grid">
                <IonInput label="Empresa" labelPlacement="stacked" value={item.empresa} onIonInput={(e) => set("empresa", String(e.detail.value ?? ""))} />
                <IonInput label="RUT" labelPlacement="stacked" value={item.rut} onIonInput={(e) => set("rut", String(e.detail.value ?? ""))} />
                <IonInput label="Local" labelPlacement="stacked" value={item.local} onIonInput={(e) => set("local", String(e.detail.value ?? ""))} />
                <IonInput label="E-mail" labelPlacement="stacked" type="email" value={item.email} onIonInput={(e) => set("email", String(e.detail.value ?? ""))} />
              </div>
              <IonTextarea label="Membrete" labelPlacement="stacked" value={item.membrete} onIonInput={(e) => set("membrete", String(e.detail.value ?? ""))} autoGrow />
              {message && <p className="muted">{message}</p>}
              <div className="form-actions"><IonButton onClick={() => void save()}>Guardar</IonButton></div>
            </>
          )}
        </IonCardContent></IonCard>
      </div>
    </AppShell>
  );
}
