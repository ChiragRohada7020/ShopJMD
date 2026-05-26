import { formatCurrency, formatDate } from "../utils.js";

export default function TransactionTable({ transactions = [], showSupplier = true }) {
  return (
    <div>
      <div className="space-y-3 md:hidden">
        {transactions.map((transaction) => {
          const isCredit = transaction.transaction_type === "credit";
          return (
            <article key={transaction.id} className="card p-4">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-xs font-bold uppercase tracking-wide text-slate-500">{formatDate(transaction.date)}</p>
                  {showSupplier && <h3 className="mt-1 text-base font-bold text-slate-950">{transaction.supplier_name}</h3>}
                </div>
                <span className={`rounded-lg px-2.5 py-1 text-xs font-bold uppercase ${isCredit ? "bg-emerald-50 text-emerald-700" : "bg-rose-50 text-rose-700"}`}>
                  {transaction.transaction_type}
                </span>
              </div>
              <p className="mt-3 text-sm font-medium text-slate-700">{transaction.description}</p>
              <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
                <div className="rounded-lg bg-slate-50 p-3">
                  <p className="text-xs font-bold uppercase text-slate-500">Qty</p>
                  <p className="mt-1 font-bold text-slate-900">
                    {Number(transaction.quantity || 0).toLocaleString("en-IN")} {transaction.unit}
                  </p>
                </div>
                <div className="rounded-lg bg-slate-50 p-3">
                  <p className="text-xs font-bold uppercase text-slate-500">Rate</p>
                  <p className="mt-1 font-bold text-slate-900">{formatCurrency(transaction.rate)}</p>
                </div>
                <div className={`rounded-lg p-3 ${isCredit ? "bg-emerald-50" : "bg-rose-50"}`}>
                  <p className="text-xs font-bold uppercase text-slate-500">Amount</p>
                  <p className={`mt-1 font-bold ${isCredit ? "text-emerald-700" : "text-rose-700"}`}>{formatCurrency(transaction.amount)}</p>
                </div>
                <div className="rounded-lg bg-slate-900 p-3 text-white">
                  <p className="text-xs font-bold uppercase text-slate-300">Balance</p>
                  <p className="mt-1 font-bold">{transaction.balance !== undefined ? formatCurrency(transaction.balance) : "-"}</p>
                </div>
              </div>
            </article>
          );
        })}
        {transactions.length === 0 && (
          <div className="card px-4 py-10 text-center font-semibold text-slate-500">No transactions found</div>
        )}
      </div>

      <div className="card hidden overflow-hidden md:block">
        <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-200">
          <thead className="table-head">
            <tr>
              <th className="px-4 py-3">Date</th>
              {showSupplier && <th className="px-4 py-3">Supplier</th>}
              <th className="px-4 py-3">Description</th>
              <th className="px-4 py-3">Qty</th>
              <th className="px-4 py-3">Rate</th>
              <th className="px-4 py-3">Credit</th>
              <th className="px-4 py-3">Debit</th>
              <th className="px-4 py-3">Balance</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 bg-white">
            {transactions.map((transaction) => {
              const isCredit = transaction.transaction_type === "credit";
              return (
                <tr key={transaction.id} className="hover:bg-slate-50">
                  <td className="whitespace-nowrap px-4 py-3 text-sm font-medium text-slate-700">{formatDate(transaction.date)}</td>
                  {showSupplier && <td className="whitespace-nowrap px-4 py-3 text-sm font-semibold text-slate-900">{transaction.supplier_name}</td>}
                  <td className="min-w-52 px-4 py-3 text-sm text-slate-600">{transaction.description}</td>
                  <td className="whitespace-nowrap px-4 py-3 text-sm text-slate-700">
                    {Number(transaction.quantity || 0).toLocaleString("en-IN")} {transaction.unit}
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-sm text-slate-700">{formatCurrency(transaction.rate)}</td>
                  <td className="whitespace-nowrap px-4 py-3 text-sm font-bold text-emerald-700">
                    {isCredit ? formatCurrency(transaction.amount) : "-"}
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-sm font-bold text-rose-700">
                    {!isCredit ? formatCurrency(transaction.amount) : "-"}
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-sm font-bold text-slate-950">
                    {transaction.balance !== undefined ? formatCurrency(transaction.balance) : "-"}
                  </td>
                </tr>
              );
            })}
            {transactions.length === 0 && (
              <tr>
                <td colSpan={showSupplier ? 8 : 7} className="px-4 py-10 text-center font-semibold text-slate-500">
                  No transactions found
                </td>
              </tr>
            )}
          </tbody>
        </table>
        </div>
      </div>
    </div>
  );
}
