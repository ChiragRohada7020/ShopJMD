import { Navigate, Route, Routes } from "react-router-dom";

import Layout from "./components/Layout.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import PdfReports from "./pages/PdfReports.jsx";
import SupplierDetails from "./pages/SupplierDetails.jsx";
import SupplierForm from "./pages/SupplierForm.jsx";
import Suppliers from "./pages/Suppliers.jsx";
import Transactions from "./pages/Transactions.jsx";
import VoiceEntry from "./pages/VoiceEntry.jsx";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/suppliers" element={<Suppliers />} />
        <Route path="/suppliers/new" element={<SupplierForm />} />
        <Route path="/suppliers/:id" element={<SupplierDetails />} />
        <Route path="/suppliers/:id/edit" element={<SupplierForm />} />
        <Route path="/transactions" element={<Transactions />} />
        <Route path="/voice-entry" element={<VoiceEntry />} />
        <Route path="/reports" element={<PdfReports />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
