import {
  IonContent,
  IonHeader,
  IonButtons,
  IonItem,
  IonLabel,
  IonList,
  IonMenu,
  IonMenuButton,
  IonMenuToggle,
  IonPage,
  IonSplitPane,
  IonTitle,
  IonToolbar
} from "@ionic/react";
import { ReactNode } from "react";
import { useLocation } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

const links = [
  { href: "/dashboard", label: "Panel" },
  { href: "/cuadraturas", label: "Cuadraturas" },
  { href: "/cuadraturas/importar", label: "Leer cuadratura" },
  { href: "/depositos", label: "Depositos" },
  { href: "/depositos/importar", label: "Leer boleta" },
  { href: "/operadores", label: "Operadores" },
  { href: "/reportes", label: "Reportes" },
  { href: "/usuarios", label: "Usuarios", admin: true },
  { href: "/configuracion", label: "Configuracion", admin: true }
];

export function AppShell({ title, children }: { title: string; children: ReactNode }) {
  const location = useLocation();
  const { user, logout } = useAuth();

  return (
    <IonSplitPane contentId="main-content">
      <IonMenu contentId="main-content" type="overlay">
        <IonHeader>
          <IonToolbar color="dark">
            <IonTitle>Rendicion</IonTitle>
          </IonToolbar>
        </IonHeader>
        <IonContent>
          <div className="menu-user">
            <strong>{user?.codigo}</strong>
            <span>{user?.rol}</span>
          </div>
          <IonList>
            {links
              .filter((link) => !link.admin || user?.rol === "admin")
              .map((link) => (
                <IonMenuToggle key={link.href} autoHide={false}>
                  <IonItem routerLink={link.href} routerDirection="none" className={location.pathname === link.href ? "selected" : ""}>
                    <IonLabel>{link.label}</IonLabel>
                  </IonItem>
                </IonMenuToggle>
              ))}
            <IonItem button onClick={() => void logout()} routerLink="/login">
              <IonLabel>Cerrar sesion</IonLabel>
            </IonItem>
          </IonList>
        </IonContent>
      </IonMenu>

      <IonPage id="main-content">
        <IonHeader>
          <IonToolbar>
            <IonButtons slot="start">
              <IonMenuButton />
            </IonButtons>
            <IonTitle>{title}</IonTitle>
          </IonToolbar>
        </IonHeader>
        <IonContent fullscreen className="app-content">
          {children}
        </IonContent>
      </IonPage>
    </IonSplitPane>
  );
}
