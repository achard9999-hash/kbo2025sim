import React from "react";
import ReactDOM from "react-dom/client";
import { withStreamlitConnection } from "streamlit-component-lib";
import HanwhaDashboard from "./HanwhaDashboard";
import "./styles.css";

const WrappedDashboard = withStreamlitConnection(HanwhaDashboard);

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <WrappedDashboard />
  </React.StrictMode>
);