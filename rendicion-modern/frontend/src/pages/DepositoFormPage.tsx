import { IonButton, IonCard, IonCardContent, IonInput, IonSelect, IonSelectOption, IonSpinner, IonTextarea } from "@ionic/react";
import { useEffect, useState } from "react";
import { useHistory, useLocation, useParams } from "react-router-dom";
import { AppShell } from "../components/AppShell";
import { api, money } from "../services/api";
import type { Deposito, Operador } from "../types/api";

const numericFields = ["por_20k", "por_10k", "por_05k", "por_02k", "por_01k", "por_05c", "por_01c", "por_50u", "por_10u", "aceite_c", "promo_c", "aceite_v", "promo_v"] as const;

export default function DepositoFormPage() {
  const { id } = useParams<{ id?: string }>();
  const history = useHistory();
  const location = useLocation<{ item?: Deposito; operadores?: Operador[] }>();
  const [item, setItem] = useState<Deposito | null>(location.state?.item ?? null);
  const [operadores, setOperadores] = useState<Operador[]>(location.state?.operadores ?? []);
  const [ocrWarning] = useState<string>((location.state as { ocr_warning?: string } | undefined)?.ocr_warning ?? "");
  const [ocrText] = useState<string>((location.state as { ocr_text?: string } | undefined)?.ocr_text ?? "");
  const [error, setError] = useState("");

  useEffect(() => {
    if (item) return;
    const loader = id ? api.deposito(id) : api.depositoNuevo();
    void loader.then((data) => {
      setItem(data.item);
      setOperadores(data.operadores);
    }).catch((exc) => {
      setError(exc instanceof Error ? exc.message : "No se pudo cargar el deposito.");
    });
  }, [id, item]);

  const set = (field: keyof Deposito, value: string | number) => setItem((current) => current ? { ...current, [field]: value } : current);

  const save = async () => {
    if (!item) return;
    setError("");
    try {
      await api.guardarDeposito(item);
      history.push("/depositos");
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "No se pudo guardar.");
    }
  };

  return (
    <AppShell title={id ? "Editar deposito" : "Nuevo deposito"}>
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
                {numericFields.map((field) => <IonInput key={field} label={field} labelPlacement="stacked" type="number" value={item[field]} onIonInput={(e) => set(field, Number(e.detail.value ?? 0))} />)}
              </div>
              <p className="muted">Total calculado en backend al guardar: <strong>{money(item.total_v)}</strong></p>
              {ocrText && <IonTextarea label="Texto detectado por OCR" labelPlacement="stacked" value={ocrText} readonly autoGrow />}
              {error && <p className="ion-text-danger">{error}</p>}
              <div className="form-actions"><IonButton onClick={() => void save()}>Guardar</IonButton><IonButton fill="outline" onClick={() => history.push("/depositos")}>Cancelar</IonButton></div>
            </>
          )}
        </IonCardContent></IonCard>
      </div>
    </AppShell>
  );
}
