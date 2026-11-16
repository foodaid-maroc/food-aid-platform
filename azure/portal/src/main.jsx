import React from "react";
import ReactDOM from "react-dom/client";
import { PublicClientApplication } from "@azure/msal-browser";
import { MsalProvider } from "@azure/msal-react";
import { AUTH_MODE, msalConfig } from "./authConfig";
import App from "./App";

const root = ReactDOM.createRoot(document.getElementById("root"));

if (AUTH_MODE === "entra") {
  const msal = new PublicClientApplication(msalConfig);
  msal.initialize().then(() =>
    root.render(<MsalProvider instance={msal}><App /></MsalProvider>)
  );
} else {
  root.render(<App />);
}
