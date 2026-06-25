import { IonButton, IonCard, IonCardContent, IonTextarea } from "@ionic/react";
import { useState } from "react";
import { useHistory } from "react-router-dom";
import { AppShell } from "../components/AppShell";
import { api } from "../services/api";
import type { Cuadratura, Operador } from "../types/api";

export default function ImportarCuadraturaPage() {
  const history = useHistory();
  const [file, setFile] = useState<File | null>(null);
  const [parsedItem, setParsedItem] = useState<Cuadratura | null>(null);
  const [parsedOperadores, setParsedOperadores] = useState<Operador[]>([]);
  const [ocrText, setOcrText] = useState("");
  const [warning, setWarning] = useState("");
  const [loading, setLoading] = useState(false);

  const upload = async () => {
    if (!file) return;
    setLoading(true);
    setParsedItem(null);
    setParsedOperadores([]);
    setOcrText("");
    setWarning("");
    try {
      const data = await api.importarCuadratura(file);
      setOcrText(data.ocr_text);
      setWarning(data.ocr_warning);
      setParsedItem(data.item as Cuadratura);
      setParsedOperadores(data.operadores as Operador[]);
    } catch (exc) {
      setWarning(exc instanceof Error ? exc.message : "No se pudo leer la cuadratura.");
    } finally {
      setLoading(false);
    }
  };

  const useParsedData = () => {
    if (!parsedItem) return;
    history.push("/cuadraturas/nuevo", {
      item: parsedItem,
      operadores: parsedOperadores,
      ocr_warning: warning,
      ocr_text: ocrText
    });
  };

  return (
    <AppShell title="Leer cuadratura">
      <div className="page-pad">
        <IonCard className="data-card">
          <IonCardContent>
            <label className="file-drop">
              Imagen o PDF de cuadratura
              <input type="file" accept="image/*,application/pdf,.pdf" onChange={(event) => setFile(event.target.files?.[0] ?? null)} />
            </label>
            {file && <p className="muted">Archivo seleccionado: {file.name}</p>}
            {warning && <p className="ion-text-warning">{warning}</p>}
            <div className="form-actions">
              <IonButton disabled={!file || loading} onClick={() => void upload()}>{loading ? "Leyendo..." : "Leer archivo"}</IonButton>
              <IonButton disabled={!parsedItem} onClick={useParsedData}>Usar datos en cuadratura</IonButton>
            </div>
            {ocrText && <IonTextarea label="Texto detectado" labelPlacement="stacked" value={ocrText} readonly autoGrow />}
          </IonCardContent>
        </IonCard>
      </div>
    </AppShell>
  );
}
