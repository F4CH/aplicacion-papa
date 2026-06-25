import { IonButton, IonCard, IonCardContent, IonCardHeader, IonCardTitle, IonContent, IonInput, IonPage, IonText } from "@ionic/react";
import { FormEvent, useState } from "react";
import { useHistory } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

export default function LoginPage() {
  const history = useHistory();
  const { login } = useAuth();
  const [codigo, setCodigo] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      await login(codigo, password);
      history.replace("/dashboard");
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "No se pudo iniciar sesion.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <IonPage>
      <IonContent fullscreen>
        <main className="login-page">
          <IonCard className="login-card">
            <IonCardHeader>
              <IonCardTitle>Rendicion</IonCardTitle>
              <p className="muted">Acceso al sistema de cuadratura y depositos</p>
            </IonCardHeader>
            <IonCardContent>
              <form onSubmit={submit}>
                <IonInput label="Usuario" labelPlacement="stacked" value={codigo} onIonInput={(event) => setCodigo(String(event.detail.value ?? ""))} autocomplete="username" required />
                <IonInput label="Password" labelPlacement="stacked" type="password" value={password} onIonInput={(event) => setPassword(String(event.detail.value ?? ""))} autocomplete="current-password" required />
                {error && <IonText color="danger"><p>{error}</p></IonText>}
                <IonButton expand="block" type="submit" disabled={loading}>{loading ? "Ingresando..." : "Ingresar"}</IonButton>
              </form>
            </IonCardContent>
          </IonCard>
        </main>
      </IonContent>
    </IonPage>
  );
}
