import { IndianRupee, ReceiptText, TrendingDown, TrendingUp, Users } from "lucide-react";
import { useEffect, useState } from "react";
import toast from "react-hot-toast";
import { Link } from "react-router-dom";

import api from "../api/client.js";
import EmptyState from "../components/EmptyState.jsx";
import Loading from "../components/Loading.jsx";
import StatCard from "../components/StatCard.jsx";
import TransactionTable from "../components/TransactionTable.jsx";
import { formatCurrency, getErrorMessage } from "../utils.js";

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get("/api/dashboard")
      .then((response) => setData(response.data))
      .catch((error) => toast.error(getErrorMessage(error)))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Loading label="Loading dashboard..." />;

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard title="Total Suppliers" value={data?.total_suppliers || 0} icon={Users} />
        <StatCard title="Total Credit" value={formatCurrency(data?.total_credit)} icon={TrendingUp} tone="emerald" />
        <StatCard title="Total Debit" value={formatCurrency(data?.total_debit)} icon={TrendingDown} tone="rose" />
        <StatCard title="Net Balance" value={formatCurrency(data?.net_balance)} icon={IndianRupee} tone="indigo" />
      </div>

      <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
        <div>
          <h2 className="text-xl font-bold text-slate-950">Recent Transactions</h2>
          <p className="text-sm font-medium text-slate-500">Latest ledger activity across suppliers</p>
        </div>
        <Link to="/voice-entry" className="btn-primary">
          <ReceiptText size={18} />
          Add Voice Entry
        </Link>
      </div>

      {data?.recent_transactions?.length ? (
        <TransactionTable transactions={data.recent_transactions} />
      ) : (
        <EmptyState
          title="No transactions yet"
          action={
            <Link to="/suppliers/new" className="btn-primary">
              Add Supplier
            </Link>
          }
        />
      )}
    </div>
  );
}
