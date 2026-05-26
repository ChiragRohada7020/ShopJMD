import { CalendarDays, Download, FileText, RotateCcw, UserRound } from "lucide-react";
import { useEffect, useState } from "react";
import toast from "react-hot-toast";

import api from "../api/client.js";
import Loading from "../components/Loading.jsx";
import { formatCurrency, getErrorMessage } from "../utils.js";

export default function PdfReports() {
  const [suppliers, setSuppliers] = useState([]);
  const [supplierId, setSupplierId] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [loading, setLoading] = useState(true);

  const selectedSupplier = suppliers.find((supplier) => supplier.id === supplierId);

  useEffect(() => {
    api
      .get("/api/suppliers")
      .then((response) => {
        setSuppliers(response.data.suppliers);
        setSupplierId(response.data.suppliers[0]?.id || "");
      })
      .catch((error) => toast.error(getErrorMessage(error)))
      .finally(() => setLoading(false));
  }, []);

  const download = () => {
    if (!supplierId) {
      toast.error("Select a supplier");
      return;
    }
    const params = new URLSearchParams();
    if (startDate) params.set("start_date", startDate);
    if (endDate) params.set("end_date", endDate);
    const baseUrl = import.meta.env.VITE_API_URL || "http://localhost:5000";
    window.open(`${baseUrl}/api/suppliers/${supplierId}/pdf?${params.toString()}`, "_blank");
  };

  const resetDates = () => {
    setStartDate("");
    setEndDate("");
  };

  if (loading) return <Loading label="Loading report options..." />;

  return (
    <div className="mx-auto max-w-5xl space-y-4 sm:space-y-5">
      <section className="card overflow-hidden">
        <div className="border-b border-slate-200 bg-slate-50 px-4 py-5 sm:px-6">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-start gap-3">
              <div className="grid h-12 w-12 shrink-0 place-items-center rounded-lg bg-emerald-600 text-white">
                <FileText size={24} />
              </div>
              <div>
                <h2 className="text-2xl font-bold text-slate-950">Professional Ledger PDF</h2>
                <p className="mt-1 text-sm font-medium text-slate-500">Create a clean supplier account statement ready to share</p>
              </div>
            </div>
            <button className="btn-primary w-full sm:w-auto" onClick={download} type="button">
              <Download size={18} />
              Download PDF
            </button>
          </div>
        </div>

        <div className="grid gap-5 p-4 sm:p-6 lg:grid-cols-[1.2fr_0.8fr]">
          <div className="space-y-4">
            <label className="space-y-2">
              <span className="label">Supplier</span>
              <select className="input" value={supplierId} onChange={(event) => setSupplierId(event.target.value)}>
                <option value="">Select supplier</option>
                {suppliers.map((supplier) => (
                  <option key={supplier.id} value={supplier.id}>
                    {supplier.supplier_name}
                  </option>
                ))}
              </select>
            </label>

            <div className="grid gap-4 sm:grid-cols-2">
              <label className="space-y-2">
                <span className="label">Start date</span>
                <input className="input" type="date" value={startDate} onChange={(event) => setStartDate(event.target.value)} />
              </label>
              <label className="space-y-2">
                <span className="label">End date</span>
                <input className="input" type="date" value={endDate} onChange={(event) => setEndDate(event.target.value)} />
              </label>
            </div>

            <div className="flex flex-col gap-3 sm:flex-row">
              <button className="btn-primary w-full sm:w-auto" onClick={download} type="button">
                <Download size={18} />
                Download Statement
              </button>
              <button className="btn-secondary w-full sm:w-auto" onClick={resetDates} type="button">
                <RotateCcw size={18} />
                All Dates
              </button>
            </div>
          </div>

          <div className="rounded-lg border border-slate-200 bg-white p-4">
            <div className="flex items-center gap-2 text-slate-500">
              <UserRound size={18} />
              <p className="text-sm font-bold uppercase tracking-wide">Statement Preview</p>
            </div>
            <div className="mt-4 space-y-3">
              <div>
                <p className="text-xs font-bold uppercase tracking-wide text-slate-500">Supplier</p>
                <p className="text-lg font-bold text-slate-950">{selectedSupplier?.supplier_name || "No supplier selected"}</p>
              </div>
              <div>
                <p className="text-xs font-bold uppercase tracking-wide text-slate-500">Current balance</p>
                <p className="text-xl font-bold text-emerald-700">{selectedSupplier ? formatCurrency(selectedSupplier.balance) : "-"}</p>
              </div>
              <div className="flex items-center gap-2 rounded-lg bg-slate-50 p-3 text-sm font-semibold text-slate-600">
                <CalendarDays size={17} />
                {startDate || "Opening"} to {endDate || "Today"}
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
