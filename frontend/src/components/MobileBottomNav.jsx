import { FileText, Home, Mic, ReceiptText, Users } from "lucide-react";
import { NavLink } from "react-router-dom";

const items = [
  { to: "/", label: "Home", icon: Home },
  { to: "/suppliers", label: "Suppliers", icon: Users },
  { to: "/voice-entry", label: "Voice", icon: Mic },
  { to: "/transactions", label: "Ledger", icon: ReceiptText },
  { to: "/reports", label: "PDF", icon: FileText },
];

export default function MobileBottomNav() {
  return (
    <nav className="fixed inset-x-0 bottom-0 z-40 border-t border-slate-200 bg-white/95 px-2 pb-[max(env(safe-area-inset-bottom),0.5rem)] pt-2 shadow-[0_-10px_30px_rgba(15,23,42,0.08)] backdrop-blur lg:hidden">
      <div className="grid grid-cols-5 gap-1">
        {items.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex min-h-14 flex-col items-center justify-center gap-1 rounded-lg text-[11px] font-bold transition ${
                  isActive ? "bg-emerald-50 text-emerald-700" : "text-slate-500"
                }`
              }
            >
              <Icon size={20} />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </div>
    </nav>
  );
}
