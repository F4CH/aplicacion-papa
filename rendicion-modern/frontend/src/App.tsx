import { IonApp, IonLoading, IonRouterOutlet } from "@ionic/react";
import { IonReactRouter } from "@ionic/react-router";
import { Redirect, Route } from "react-router-dom";
import { AuthProvider, useAuth } from "./hooks/useAuth";
import LoginPage from "./pages/LoginPage";
import DashboardPage from "./pages/DashboardPage";
import CuadraturasPage from "./pages/CuadraturasPage";
import CuadraturaFormPage from "./pages/CuadraturaFormPage";
import ImportarCuadraturaPage from "./pages/ImportarCuadraturaPage";
import DepositosPage from "./pages/DepositosPage";
import DepositoFormPage from "./pages/DepositoFormPage";
import ImportarDepositoPage from "./pages/ImportarDepositoPage";
import OperadoresPage from "./pages/OperadoresPage";
import OperadorFormPage from "./pages/OperadorFormPage";
import UsuariosPage from "./pages/UsuariosPage";
import UsuarioFormPage from "./pages/UsuarioFormPage";
import ConfiguracionPage from "./pages/ConfiguracionPage";
import ReportesPage from "./pages/ReportesPage";

function PrivateRoute({ component: Component, admin = false, ...rest }: { component: React.ComponentType; path: string; exact?: boolean; admin?: boolean }) {
  const { user, loading } = useAuth();

  if (loading) {
    return <IonLoading isOpen message="Cargando sesion..." />;
  }

  return (
    <Route
      {...rest}
      render={() => {
        if (!user) return <Redirect to="/login" />;
        if (admin && user.rol !== "admin") return <Redirect to="/dashboard" />;
        return <Component />;
      }}
    />
  );
}

export default function App() {
  return (
    <IonApp>
      <AuthProvider>
        <IonReactRouter>
          <IonRouterOutlet>
            <Route exact path="/login" component={LoginPage} />
            <PrivateRoute exact path="/dashboard" component={DashboardPage} />
            <PrivateRoute exact path="/cuadraturas" component={CuadraturasPage} />
            <PrivateRoute exact path="/cuadraturas/nuevo" component={CuadraturaFormPage} />
            <PrivateRoute exact path="/cuadraturas/importar" component={ImportarCuadraturaPage} />
            <PrivateRoute exact path="/cuadraturas/editar/:id" component={CuadraturaFormPage} />
            <PrivateRoute exact path="/depositos" component={DepositosPage} />
            <PrivateRoute exact path="/depositos/nuevo" component={DepositoFormPage} />
            <PrivateRoute exact path="/depositos/importar" component={ImportarDepositoPage} />
            <PrivateRoute exact path="/depositos/editar/:id" component={DepositoFormPage} />
            <PrivateRoute exact path="/operadores" component={OperadoresPage} />
            <PrivateRoute exact path="/operadores/nuevo" component={OperadorFormPage} />
            <PrivateRoute exact path="/operadores/editar/:codigo" component={OperadorFormPage} />
            <PrivateRoute exact path="/usuarios" component={UsuariosPage} admin />
            <PrivateRoute exact path="/usuarios/nuevo" component={UsuarioFormPage} admin />
            <PrivateRoute exact path="/usuarios/editar/:id" component={UsuarioFormPage} admin />
            <PrivateRoute exact path="/configuracion" component={ConfiguracionPage} admin />
            <PrivateRoute exact path="/reportes" component={ReportesPage} />
            <Route exact path="/">
              <Redirect to="/dashboard" />
            </Route>
          </IonRouterOutlet>
        </IonReactRouter>
      </AuthProvider>
    </IonApp>
  );
}
