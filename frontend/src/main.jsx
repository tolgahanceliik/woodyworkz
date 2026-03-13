import React from "react";
import ReactDOM from "react-dom/client";
import { Toaster } from "react-hot-toast";
import App from "./App";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <App />
    <Toaster
      position="top-right"
      toastOptions={{
        style: {
          background: "#1e1e2e",
          color: "#e2e8f0",
          border: "1px solid #313149",
        },
      }}
    />
  </React.StrictMode>
);
