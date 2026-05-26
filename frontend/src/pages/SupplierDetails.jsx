import { Download, Edit, Plus } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import toast from "react-hot-toast";
import { Link, useParams } from "react-router-dom";

import api from "../api/client.js";
import Loading from "../components/Loading.jsx";
import TransactionTable from "../components/TransactionTable.jsx";
import { formatCurrency, getErrorMessage, today } from "../utils.js";

const emptyTransaction = {
  transaction_type: "debit",
  quantity: "",
  unit: "bag",
  rate: "",
  amount: "",
  description: "",
  date: today(),
};

export default function SupplierDetails() {
  const { id } = useParams();
  const [supplier, setSupplier] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [form, setForm] = useState(emptyTransaction);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const calculatedAmount = useMemo(() => Number(form.amount || 0) || Number(form.quantity || 0) * Number(form.rate || 0), [form]);

  const load = async () => {
    setLoading(true);
    try {
      const [supplierResponse, transactionsResponse] = await Promise.all([
        api.get(`/api/suppliers/${id}`),
        api.get(`/api/suppliers/${id}/transactions`),
      ]);
      setSupplier(supplierResponse.data.supplier);
      setTransactions(transactionsResponse.data.transactions);
    } catch (error) {
      toast.error(getErrorMessage(error));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [id]);

  const updateField = (field, value) => setForm((current) => ({ ...current, [field]: value }));

  const submitTransaction = async (event) => {
    event.preventDefault();
    if (calculatedAmount <= 0) {
      toast.error("Amount must be greater than zero");
      return;
    }
    setSaving(true);
    try {
      await api.post("/api/transactions", {
        ...form,
        supplier_id: id,
        supplier_name: supplier.supplier_name,
        quantity: Number(form.quantity || 0),
        rate: Number(form.rate || 0),
        amount: calculatedAmount,
      });
      toast.success("Transaction saved");
      setForm(emptyTransaction);
      load();
    } catch (error) {
      toast.error(getErrorMessage(error));
    } finally {
      setSaving(false);
    }
  };

  const downloadPdf = () => {
    window.open(`${import.meta.env.VITE_API_URL || "http://localhost:5000"}/api/suppliers/${id}/pdf`, "_blank");
  };

  if (loading) return <Loading label="Loading ledger..." />;
  if (!supplier) return null;

  return (
    <div className="space-y-4 sm:space-y-6">
      <section className="card p-4 sm:p-5">
        <div className="flex flex-col justify-between gap-4 lg:flex-row lg:items-start">
          <div>
            <h2 className="text-2xl font-bold text-slate-950">{supplier.supplier_name}</h2>
            <p className="mt-1 text-sm font-semibold text-slate-500">{supplier.mobile_number || "No mobile number"}</p>
            <p className="mt-3 max-w-3xl text-sm text-slate-600">{supplier.address || "No address added"}</p>
            {supplier.notes && <p className="mt-2 max-w-3xl text-sm text-slate-500">{supplier.notes}</p>}
          </div>
          <div className="flex flex-col gap-2 sm:flex-row">
            <Link to={`/suppliers/${id}/edit`} className="btn-secondary w-full sm:w-auto">
              <Edit size={18} />
              Edit
            </Link>
            <button className="btn-primary w-full sm:w-auto" onClick={downloadPdf} type="button">
              <Download size={18} />
              Download PDF
            </button>
          </div>
        </div>
        <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          <div className="rounded-lg bg-slate-50 p-4">
            <p className="text-sm font-semibold text-slate-500">Opening balance</p>
            <p className="mt-1 text-xl font-bold text-slate-950">{formatCurrency(supplier.opening_balance)}</p>
          </div>
          <div className="rounded-lg bg-emerald-50 p-4">
            <p className="text-sm font-semibold text-emerald-700">Current balance</p>
            <p className="mt-1 text-xl font-bold text-emerald-800">{formatCurrency(supplier.balance)}</p>
          </div>
        </div>
      </section>

      <form className="card p-4 sm:p-5" onSubmit={submitTransaction}>
        <div className="mb-4 flex items-start justify-between gap-3">
          <div className="flex items-center gap-2">
            <Plus className="text-emerald-700" size={20} />
            <h3 className="text-lg font-bold text-slate-950">Add Transaction</h3>
          </div>
          <div className="rounded-lg bg-slate-50 px-3 py-2 text-right">
            <p className="text-xs font-bold uppercase text-slate-500">Amount</p>
            <p className="text-sm font-bold text-slate-950">{formatCurrency(calculatedAmount)}</p>
          </div>
        </div>
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <label className="space-y-2">
            <span className="label">Type</span>
            <select className="input" value={form.transaction_type} onChange={(event) => updateField("transaction_type", event.target.value)}>
              <option value="debit">Debit</option>
              <option value="credit">Credit</option>
            </select>
          </label>
          <label className="space-y-2">
            <span className="label">Quantity</span>
            <input className="input" type="number" step="0.01" value={form.quantity} onChange={(event) => updateField("quantity", event.target.value)} />
          </label>
          <label className="space-y-2">
            <span className="label">Unit</span>
            <input className="input" value={form.unit} onChange={(event) => updateField("unit", event.target.value)} />
          </label>
          <label className="space-y-2">
            <span className="label">Rate</span>
            <input className="input" type="number" step="0.01" value={form.rate} onChange={(event) => updateField("rate", event.target.value)} />
          </label>
          <label className="space-y-2">
            <span className="label">Amount</span>
            <input className="input" type="number" step="0.01" value={form.amount} onChange={(event) => updateField("amount", event.target.value)} placeholder={String(calculatedAmount || "")} />
          </label>
          <label className="space-y-2">
            <span className="label">Date</span>
            <input className="input" type="date" value={form.date} onChange={(event) => updateField("date", event.target.value)} />
          </label>
          <label className="space-y-2 md:col-span-2">
            <span className="label">Description</span>
            <input className="input" value={form.description} onChange={(event) => updateField("description", event.target.value)} />
          </label>
        </div>
        <div className="mt-5 flex justify-end">
          <button className="btn-primary w-full sm:w-auto" disabled={saving} type="submit">
            {saving ? "Saving..." : "Save Transaction"}
          </button>
        </div>
      </form>

      <TransactionTable transactions={transactions} showSupplier={false} />
    </div>
  );
}
