import React from "react";
import { createRoot } from "react-dom/client";
import { setupIonicReact } from "@ionic/react";

import "@ionic/react/css/core.css";
import "@ionic/react/css/normalize.css";
import "@ionic/react/css/structure.css";
import "@ionic/react/css/typography.css";
import "@ionic/react/css/display.css";
import "@ionic/react/css/flex-utils.css";

import "./theme.css";
import App from "./App";

setupIonicReact();

createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
