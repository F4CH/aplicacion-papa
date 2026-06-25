import { IonButton, IonCard, IonCardContent, IonCheckbox, IonInput, IonSelect, IonSelectOption, IonSpinner, IonTextarea } from "@ionic/react";
import { useEffect, useState } from "react";
import { useHistory, useLocation, useParams } from "react-router-dom";
import { AppShell } from "../components/AppShell";
import { api, money } from "../services/api";
import type { Cuadratura, Operador } from "../types/api";

export default function CuadraturaFormPage() {
  const { id } = useParams<{ id?: string }>();
  const history = useHistory();
  const location = useLocation<{ item?: Cuadratura; operadores?: Operador[]; ocr_warning?: string; ocr_text?: string }>();
  const [item, setItem] = useState<Cuadratura | null>(location.state?.item ?? null);
  const [operadores, setOperadores] = useState<Operador[]>(location.state?.operadores ?? []);
  const [ocrWarning] = useState(location.state?.ocr_warning ?? "");
  const [ocrText] = useState(location.state?.ocr_text ?? "");
  const [error, setError] = useState("");

  useEffect(() => {
    if (item) return;
    const loader = id ? api.cuadratura(id) : api.cuadraturaNueva();
    void loader.then((data) => {
      setItem(data.item);
      setOperadores(data.operadores);
    }).catch((exc) => setError(exc instanceof Error ? exc.message : "No se pudo cargar la cuadratura."));
  }, [id, item]);

  const set = (field: keyof Cuadratura, value: string | number | boolean) => setItem((current) => current ? { ...current, [field]: value } : current);

  const save = async () => {
    if (!item) return;
    setError("");
    try {
      await api.guardarCuadratura(item);
      history.push("/cuadraturas");
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "No se pudo guardar.");
    }
  };

  return (
    <AppShell title={id ? "Editar cuadratura" : "Nueva cuadratura"}>
      <div className="page-pad">
        <IonCard className="data-card"><IonCardContent>
          {!item ? (
            error ? <p className="ion-text-danger">{error}</p> : <IonSpinner />
          ) : (
            <>
              {ocrWarning && <p className="ion-text-warning">{ocrWarning}</p>}
              <div className="form-grid wide">
                <IonInput label="Numero" labelPlacement="stacked" type="number" value={item.numero} onIonInput={(e) => set("numero", Number(e.detail.value ?? 0))} />
                <IonInput label="Fecha" labelPlacement="stacked" type="date" value={item.fecha} onIonInput={(e) => set("fecha", String(e.detail.value ?? ""))} />
                <IonInput label="Turno" labelPlacement="stacked" type="number" value={item.turno} onIonInput={(e) => set("turno", Number(e.detail.value ?? 1))} />
                <IonSelect label="Operador" labelPlacement="stacked" value={item.operador_codigo} onIonChange={(e) => set("operador_codigo", String(e.detail.value))}>
                  {operadores.map((op) => <IonSelectOption key={op.codigo} value={op.codigo}>{op.codigo} - {op.descripcion}</IonSelectOption>)}
                </IonSelect>
                {(["combust_v", "otros_v", "deposito_v", "ventas_v", "transbnk_v", "transfer_v", "piloto_v"] as const).map((field) => (
                  <IonInput key={field} label={field} labelPlacement="stacked" type="number" value={item[field]} onIonInput={(e) => set(field, Number(e.detail.value ?? 0))} />
                ))}
                <IonCheckbox checked={Boolean(item.recuperar_depositos)} onIonChange={(e) => set("recuperar_depositos", e.detail.checked)}>Recuperar depositos del turno</IonCheckbox>
              </div>
              <p className="muted">Diferencia actual: <strong>{money(item.diferencia)}</strong></p>
              {ocrText && <IonTextarea label="Texto detectado por OCR" labelPlacement="stacked" value={ocrText} readonly autoGrow />}
              {error && <p className="ion-text-danger">{error}</p>}
              <div className="form-actions"><IonButton onClick={() => void save()}>Guardar</IonButton><IonButton fill="outline" onClick={() => history.push("/cuadraturas")}>Cancelar</IonButton></div>
            </>
          )}
        </IonCardContent></IonCard>
      </div>
    </AppShell>
  );
}
