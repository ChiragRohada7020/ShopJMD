import { Menu } from "lucide-react";
import { useState } from "react";
import { Outlet, useLocation } from "react-router-dom";

import Sidebar from "./Sidebar.jsx";
import MobileBottomNav from "./MobileBottomNav.jsx";
import VoiceFloatingButton from "./VoiceFloatingButton.jsx";

const pageTitles = {
  "/": "Dashboard",
  "/suppliers": "Suppliers",
  "/suppliers/new": "Add Supplier",
  "/transactions": "Transactions",
  "/voice-entry": "Voice Entry",
  "/reports": "PDF Reports",
};

export default function Layout() {
  const [open, setOpen] = useState(false);
  const location = useLocation();
  const title = pageTitles[location.pathname] || "Supplier Ledger";

  return (
    <div className="min-h-screen bg-[#f6f7fb]">
      <Sidebar open={open} onClose={() => setOpen(false)} />
      <div className="lg:pl-72">
        <header className="sticky top-0 z-30 border-b border-slate-200 bg-white/95 backdrop-blur">
          <div className="flex min-h-14 items-center justify-between px-3 sm:min-h-16 sm:px-6 lg:px-8">
            <div className="flex items-center gap-3">
              <button
                className="hidden btn-secondary px-3 sm:inline-flex lg:hidden"
                onClick={() => setOpen(true)}
                type="button"
                aria-label="Open menu"
              >
                <Menu size={20} />
              </button>
              <div>
                <p className="text-xs font-bold uppercase tracking-wide text-emerald-700">Shop Ledger</p>
                <h1 className="text-lg font-bold text-slate-900 sm:text-xl">{title}</h1>
              </div>
            </div>
            <div className="hidden rounded-lg border border-emerald-100 bg-emerald-50 px-3 py-2 text-sm font-semibold text-emerald-700 sm:block">
              Supplier Accounts
            </div>
          </div>
        </header>
        <main className="px-3 pb-32 pt-4 sm:px-6 sm:py-6 lg:px-8 lg:pb-8">
          <div className="fade-in mx-auto max-w-7xl">
            <Outlet />
          </div>
        </main>
      </div>
      <VoiceFloatingButton />
      <MobileBottomNav />
    </div>
  );
}
