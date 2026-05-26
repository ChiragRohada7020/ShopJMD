import { FileText, Home, Mic, ReceiptText, Store, Users, X } from "lucide-react";
import { NavLink } from "react-router-dom";

const navItems = [
  { to: "/", label: "Dashboard", icon: Home },
  { to: "/suppliers", label: "Suppliers", icon: Users },
  { to: "/transactions", label: "Transactions", icon: ReceiptText },
  { to: "/voice-entry", label: "Voice Entry", icon: Mic },
  { to: "/reports", label: "PDF Reports", icon: FileText },
];

export default function Sidebar({ open, onClose }) {
  const content = (
    <aside className="flex h-full flex-col bg-white">
      <div className="flex h-16 items-center justify-between border-b border-slate-200 px-5">
        <div className="flex items-center gap-3">
          <div className="grid h-10 w-10 place-items-center rounded-lg bg-emerald-600 text-white">
            <Store size={21} />
          </div>
          <div>
            <p className="font-bold text-slate-950">Shop Manager</p>
            <p className="text-xs font-medium text-slate-500">Supplier ledger</p>
          </div>
        </div>
        <button className="btn-secondary px-3 lg:hidden" onClick={onClose} type="button" aria-label="Close menu">
          <X size={18} />
        </button>
      </div>

      <nav className="flex-1 space-y-1 px-3 py-5">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              onClick={onClose}
              className={({ isActive }) =>
                `flex min-h-12 items-center gap-3 rounded-lg px-3 font-semibold transition ${
                  isActive ? "bg-emerald-50 text-emerald-700" : "text-slate-600 hover:bg-slate-50 hover:text-slate-950"
                }`
              }
            >
              <Icon size={20} />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </nav>
    </aside>
  );

  return (
    <>
      <div className="fixed inset-y-0 left-0 z-40 hidden w-72 border-r border-slate-200 lg:block">{content}</div>
      {open && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <button className="absolute inset-0 bg-slate-950/40" onClick={onClose} type="button" aria-label="Close menu" />
          <div className="relative h-full w-72 max-w-[85vw] shadow-2xl">{content}</div>
        </div>
      )}
    </>
  );
}
