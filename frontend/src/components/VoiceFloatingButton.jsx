import { Mic } from "lucide-react";
import { Link } from "react-router-dom";

export default function VoiceFloatingButton() {
  return (
    <Link
      to="/voice-entry"
      className="fixed bottom-24 right-4 z-30 grid h-14 w-14 place-items-center rounded-full bg-emerald-600 text-white shadow-2xl shadow-emerald-600/30 transition hover:scale-105 hover:bg-emerald-700 sm:h-16 sm:w-16 lg:bottom-5 lg:right-5"
      aria-label="Voice entry"
      title="Voice entry"
    >
      <Mic size={26} />
    </Link>
  );
}
