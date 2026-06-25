import { IonButton, IonCard, IonCardContent, IonTextarea } from "@ionic/react";
import { useState } from "react";
import { useHistory } from "react-router-dom";
import { AppShell } from "../components/AppShell";
import { api } from "../services/api";
import type { Deposito, Operador } from "../types/api";

export default function ImportarDepositoPage() {
  const history = useHistory();
  const [file, setFile] = useState<File | null>(null);
  const [parsedItem, setParsedItem] = useState<Deposito | null>(null);
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
      const data = await api.importarDeposito(file);
      setOcrText(data.ocr_text);
      setWarning(data.ocr_warning);
      setParsedItem(data.item as Deposito);
      setParsedOperadores(data.operadores as Operador[]);
    } catch (exc) {
      setWarning(exc instanceof Error ? exc.message : "No se pudo leer la imagen.");
    } finally {
      setLoading(false);
    }
  };

  const useParsedData = () => {
    if (!parsedItem) return;
    history.push("/depositos/nuevo", {
      item: parsedItem,
      operadores: parsedOperadores,
      ocr_warning: warning,
      ocr_text: ocrText
    });
  };

  return (
    <AppShell title="Leer boleta">
      <div className="page-pad">
        <IonCard className="data-card">
          <IonCardContent>
            <label className="file-drop">
              Imagen o PDF de boleta
              <input type="file" accept="image/*,application/pdf,.pdf" onChange={(event) => setFile(event.target.files?.[0] ?? null)} />
            </label>
            {file && <p className="muted">Archivo seleccionado: {file.name}</p>}
            {warning && <p className="ion-text-warning">{warning}</p>}
            <div className="form-actions">
              <IonButton disabled={!file || loading} onClick={() => void upload()}>{loading ? "Leyendo..." : "Leer imagen"}</IonButton>
              <IonButton disabled={!parsedItem} onClick={useParsedData}>Usar datos en deposito</IonButton>
            </div>
            {ocrText && <IonTextarea label="Texto detectado" labelPlacement="stacked" value={ocrText} readonly autoGrow />}
          </IonCardContent>
        </IonCard>
      </div>
    </AppShell>
  );
}
