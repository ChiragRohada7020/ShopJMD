import { Save } from "lucide-react";
import { useEffect, useState } from "react";
import toast from "react-hot-toast";
import { Link, useNavigate, useParams } from "react-router-dom";

import api from "../api/client.js";
import Loading from "../components/Loading.jsx";
import { getErrorMessage } from "../utils.js";

const emptyForm = {
  supplier_name: "",
  mobile_number: "",
  address: "",
  notes: "",
  opening_balance: 0,
};

export default function SupplierForm() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [form, setForm] = useState(emptyForm);
  const [loading, setLoading] = useState(Boolean(id));
  const [saving, setSaving] = useState(false);
  const isEdit = Boolean(id);

  useEffect(() => {
    if (!id) return;
    api
      .get(`/api/suppliers/${id}`)
      .then((response) => setForm(response.data.supplier))
      .catch((error) => toast.error(getErrorMessage(error)))
      .finally(() => setLoading(false));
  }, [id]);

  const updateField = (field, value) => {
    setForm((current) => ({ ...current, [field]: value }));
  };

  const submit = async (event) => {
    event.preventDefault();
    if (!form.supplier_name.trim()) {
      toast.error("Supplier name is required");
      return;
    }

    setSaving(true);
    try {
      const payload = { ...form, opening_balance: Number(form.opening_balance || 0) };
      const response = isEdit ? await api.put(`/api/suppliers/${id}`, payload) : await api.post("/api/suppliers", payload);
      toast.success(isEdit ? "Supplier updated" : "Supplier added");
      navigate(`/suppliers/${response.data.supplier.id}`);
    } catch (error) {
      toast.error(getErrorMessage(error));
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <Loading label="Loading supplier..." />;

  return (
    <form className="card mx-auto max-w-3xl p-4 sm:p-6" onSubmit={submit}>
      <div className="grid gap-4 sm:grid-cols-2">
        <label className="space-y-2 sm:col-span-2">
          <span className="label">Supplier name</span>
          <input className="input" value={form.supplier_name} onChange={(event) => updateField("supplier_name", event.target.value)} required />
        </label>
        <label className="space-y-2">
          <span className="label">Mobile number</span>
          <input className="input" value={form.mobile_number} onChange={(event) => updateField("mobile_number", event.target.value)} inputMode="tel" />
        </label>
        <label className="space-y-2">
          <span className="label">Opening balance</span>
          <input className="input" type="number" step="0.01" value={form.opening_balance} onChange={(event) => updateField("opening_balance", event.target.value)} />
        </label>
        <label className="space-y-2 sm:col-span-2">
          <span className="label">Address</span>
          <textarea className="input min-h-24" value={form.address} onChange={(event) => updateField("address", event.target.value)} />
        </label>
        <label className="space-y-2 sm:col-span-2">
          <span className="label">Notes</span>
          <textarea className="input min-h-24" value={form.notes} onChange={(event) => updateField("notes", event.target.value)} />
        </label>
      </div>

      <div className="mt-6 flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
        <Link to="/suppliers" className="btn-secondary w-full sm:w-auto">
          Cancel
        </Link>
        <button className="btn-primary w-full sm:w-auto" disabled={saving} type="submit">
          <Save size={18} />
          {saving ? "Saving..." : "Save Supplier"}
        </button>
      </div>
    </form>
  );
}
