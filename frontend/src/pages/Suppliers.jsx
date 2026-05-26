import { Edit, Eye, Plus, Search, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import toast from "react-hot-toast";
import { Link } from "react-router-dom";

import api from "../api/client.js";
import EmptyState from "../components/EmptyState.jsx";
import Loading from "../components/Loading.jsx";
import { formatCurrency, getErrorMessage } from "../utils.js";

export default function Suppliers() {
  const [suppliers, setSuppliers] = useState([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);

  const loadSuppliers = () => {
    setLoading(true);
    api
      .get("/api/suppliers", { params: { search } })
      .then((response) => setSuppliers(response.data.suppliers))
      .catch((error) => toast.error(getErrorMessage(error)))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    const timer = setTimeout(loadSuppliers, 250);
    return () => clearTimeout(timer);
  }, [search]);

  const deleteSupplier = async (supplier) => {
    const confirmed = window.confirm(`Delete ${supplier.supplier_name} and all related transactions?`);
    if (!confirmed) return;
    try {
      await api.delete(`/api/suppliers/${supplier.id}`);
      toast.success("Supplier deleted");
      loadSuppliers();
    } catch (error) {
      toast.error(getErrorMessage(error));
    }
  };

  return (
    <div className="space-y-5">
      <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
        <div className="relative w-full sm:max-w-md">
          <Search className="pointer-events-none absolute left-3 top-3.5 text-slate-400" size={18} />
          <input className="input pl-10" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search supplier" />
        </div>
        <Link to="/suppliers/new" className="btn-primary w-full sm:w-auto">
          <Plus size={18} />
          Add Supplier
        </Link>
      </div>

      {loading ? (
        <Loading label="Loading suppliers..." />
      ) : suppliers.length === 0 ? (
        <EmptyState
          title="No suppliers found"
          action={
            <Link to="/suppliers/new" className="btn-primary">
              Add Supplier
            </Link>
          }
        />
      ) : (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {suppliers.map((supplier) => (
            <div key={supplier.id} className="card p-5">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h2 className="text-lg font-bold text-slate-950">{supplier.supplier_name}</h2>
                  <p className="mt-1 text-sm font-medium text-slate-500">{supplier.mobile_number || "No mobile number"}</p>
                </div>
                <p className={`rounded-lg px-3 py-1 text-sm font-bold ${supplier.balance >= 0 ? "bg-emerald-50 text-emerald-700" : "bg-rose-50 text-rose-700"}`}>
                  {formatCurrency(supplier.balance)}
                </p>
              </div>
              <p className="mt-3 line-clamp-2 min-h-10 text-sm text-slate-600">{supplier.address || supplier.notes || "No address added"}</p>
              <div className="mt-5 flex flex-wrap gap-2">
                <Link to={`/suppliers/${supplier.id}`} className="btn-secondary flex-1">
                  <Eye size={17} />
                  View
                </Link>
                <Link to={`/suppliers/${supplier.id}/edit`} className="btn-secondary px-3" aria-label="Edit supplier" title="Edit">
                  <Edit size={17} />
                </Link>
                <button className="btn-danger px-3" onClick={() => deleteSupplier(supplier)} type="button" aria-label="Delete supplier" title="Delete">
                  <Trash2 size={17} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
