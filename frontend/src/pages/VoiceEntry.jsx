import { Mic, MicOff, Save, Wand2 } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import toast from "react-hot-toast";

import api from "../api/client.js";
import { formatCurrency, getErrorMessage } from "../utils.js";

const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

const compactRepeatedWords = (text) =>
  text
    .split(/\s+/)
    .filter((word, index, words) => index === 0 || word.toLowerCase() !== words[index - 1].toLowerCase())
    .join(" ")
    .trim();

const appendUniqueText = (baseText, nextText) => {
  const base = baseText.trim();
  const next = compactRepeatedWords(nextText);
  if (!next) return base;
  if (!base) return next;
  if (base.toLowerCase().endsWith(next.toLowerCase())) return base;
  return compactRepeatedWords(`${base} ${next}`);
};

export default function VoiceEntry() {
  const [voiceText, setVoiceText] = useState("");
  const [listening, setListening] = useState(false);
  const [parsing, setParsing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [parsed, setParsed] = useState(null);
  const [suppliers, setSuppliers] = useState([]);
  const [voiceLang, setVoiceLang] = useState("en-IN");
  const [liveText, setLiveText] = useState("");
  const recognitionRef = useRef(null);
  const silenceTimerRef = useRef(null);
  const finalTranscriptRef = useRef("");

  useEffect(() => {
    api.get("/api/suppliers").then((response) => setSuppliers(response.data.suppliers)).catch(() => {});
  }, []);

  const startListening = () => {
    if (!SpeechRecognition) {
      toast.error("SpeechRecognition is not supported in this browser");
      return;
    }
    window.clearTimeout(silenceTimerRef.current);
    setLiveText("");
    finalTranscriptRef.current = "";
    setParsed(null);

    const instance = new SpeechRecognition();
    instance.lang = voiceLang;
    instance.interimResults = true;
    instance.continuous = false;
    instance.maxAlternatives = 1;

    instance.onresult = (event) => {
      let newFinalText = "";
      let interimText = "";

      for (let index = event.resultIndex; index < event.results.length; index += 1) {
        const result = event.results[index];
        const transcript = compactRepeatedWords(result[0]?.transcript || "");
        if (!transcript) continue;

        if (result.isFinal) {
          newFinalText = appendUniqueText(newFinalText, transcript);
        } else {
          interimText = appendUniqueText(interimText, transcript);
        }
      }

      if (newFinalText) {
        finalTranscriptRef.current = appendUniqueText(finalTranscriptRef.current, newFinalText);
      }

      const nextText = [finalTranscriptRef.current, interimText].filter(Boolean).join(" ").trim();
      setVoiceText(nextText);
      setLiveText(interimText);

      if (newFinalText) {
        window.clearTimeout(silenceTimerRef.current);
        silenceTimerRef.current = window.setTimeout(() => {
          parseText(finalTranscriptRef.current);
        }, 1200);
      }
    };

    instance.onerror = (event) => {
      setListening(false);
      setLiveText("");
      if (event.error === "no-speech") {
        toast.error("Voice is too low or unclear. Try again closer to the phone mic.");
      } else if (event.error === "not-allowed") {
        toast.error("Microphone permission is blocked");
      } else {
        toast.error("Voice recognition failed");
      }
    };

    instance.onend = () => {
      setListening(false);
      setLiveText("");
    };

    recognitionRef.current = instance;
    setListening(true);
    instance.start();
  };

  const stopListening = () => {
    recognitionRef.current?.stop();
    window.clearTimeout(silenceTimerRef.current);
    if (voiceText.trim()) {
      parseText(voiceText);
    }
    setListening(false);
    setLiveText("");
  };

  useEffect(() => {
    return () => {
      window.clearTimeout(silenceTimerRef.current);
      recognitionRef.current?.abort();
    };
  }, []);

  const parseText = async (text = voiceText) => {
    if (!text.trim()) {
      toast.error("Enter or speak transaction text");
      return;
    }
    setParsing(true);
    try {
      const response = await api.post("/api/parse-voice", { text });
      const parsedResponse = response.data.parsed;
      setParsed(parsedResponse);
      if (parsedResponse.supplier_id && parsedResponse.supplier_name) {
        setSuppliers((current) => {
          const exists = current.some((supplier) => supplier.id === parsedResponse.supplier_id);
          if (exists) return current;
          return [
            {
              id: parsedResponse.supplier_id,
              supplier_name: parsedResponse.supplier_name,
              balance: 0,
            },
            ...current,
          ];
        });
      }
      toast.success("Voice entry parsed");
    } catch (error) {
      toast.error(getErrorMessage(error));
    } finally {
      setParsing(false);
    }
  };

  const updateParsed = (field, value) => setParsed((current) => ({ ...current, [field]: value }));

  const updateNumber = (field, value) => {
    const number = Number(value || 0);
    setParsed((current) => {
      const next = { ...current, [field]: number };
      if ((field === "quantity" || field === "rate") && (!next.amount || next.amount <= 0)) {
        next.amount = Number(next.quantity || 0) * Number(next.rate || 0);
      }
      return next;
    });
  };

  const saveTransaction = async () => {
    if (!parsed?.supplier_id) {
      toast.error("Supplier name was not detected. Speak supplier name or select one.");
      return;
    }
    setSaving(true);
    try {
      await api.post("/api/transactions", {
        ...parsed,
        supplier_id: parsed.supplier_id,
        supplier_name: parsed.supplier_name,
      });
      toast.success("Transaction saved");
      setParsed(null);
      setVoiceText("");
    } catch (error) {
      toast.error(getErrorMessage(error));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="mx-auto max-w-4xl space-y-4 sm:space-y-5">
      <section className="card p-4 sm:p-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-2xl font-bold text-slate-950">Voice Transaction Entry</h2>
            <p className="mt-1 text-sm font-medium text-slate-500">Hindi and Hinglish supplier ledger input</p>
          </div>
          <button className={`${listening ? "btn-danger" : "btn-primary"} w-full sm:w-auto`} onClick={listening ? stopListening : startListening} type="button">
            {listening ? <MicOff size={19} /> : <Mic size={19} />}
            {listening ? "Stop" : "Start Mic"}
          </button>
        </div>

        <div className="mt-4 grid grid-cols-2 gap-2 rounded-lg bg-slate-50 p-1">
          <button
            className={`min-h-11 rounded-md text-sm font-bold transition ${voiceLang === "en-IN" ? "bg-white text-emerald-700 shadow-sm" : "text-slate-600"}`}
            onClick={() => setVoiceLang("en-IN")}
            type="button"
          >
            Hinglish
          </button>
          <button
            className={`min-h-11 rounded-md text-sm font-bold transition ${voiceLang === "hi-IN" ? "bg-white text-emerald-700 shadow-sm" : "text-slate-600"}`}
            onClick={() => setVoiceLang("hi-IN")}
            type="button"
          >
            Hindi
          </button>
        </div>

        <label className="mt-5 block space-y-2">
          <span className="label">Spoken text</span>
          <textarea
            className="input min-h-36 text-lg"
            value={voiceText}
            onChange={(event) => setVoiceText(event.target.value)}
            placeholder="Ramesh supplier ko 10 katta 500 rupaye me debit karo"
          />
        </label>
        {listening && (
          <div className="mt-3 rounded-lg border border-emerald-100 bg-emerald-50 px-3 py-2 text-sm font-semibold text-emerald-800">
            Listening... {liveText || "Speak now"}
          </div>
        )}

        <div className="mt-5 flex flex-col gap-3 sm:flex-row sm:justify-end">
          <button className="btn-secondary w-full sm:w-auto" onClick={() => parseText()} disabled={parsing} type="button">
            <Wand2 size={18} />
            {parsing ? "Parsing..." : "Parse & Review"}
          </button>
          <button className="btn-primary w-full sm:w-auto" onClick={saveTransaction} disabled={!parsed || saving} type="button">
            <Save size={18} />
            {saving ? "Saving..." : "Save Transaction"}
          </button>
        </div>
      </section>

      {parsed && (
        <section className="card p-4 sm:p-6">
          <div className="mb-5 flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
            <div>
              <h3 className="text-xl font-bold text-slate-950">Confirm Transaction</h3>
              <p className="mt-1 text-sm font-semibold text-slate-500">{parsed.transaction_type?.toUpperCase()} - {formatCurrency(parsed.amount)}</p>
            </div>
            <button className="btn-primary hidden sm:inline-flex" onClick={saveTransaction} disabled={saving} type="button">
              <Save size={18} />
              {saving ? "Saving..." : "Save Transaction"}
            </button>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <label className="space-y-2 sm:col-span-2">
              <span className="label">Supplier</span>
              <select className="input" value={parsed.supplier_id || ""} onChange={(event) => updateParsed("supplier_id", event.target.value)}>
                <option value="">Select supplier</option>
                {suppliers.map((supplier) => (
                  <option key={supplier.id} value={supplier.id}>
                    {supplier.supplier_name}
                  </option>
                ))}
              </select>
              {parsed.supplier_id && parsed.supplier_match_score && (
                <span className="block text-xs font-semibold text-emerald-700">
                  {parsed.supplier_match_type === "created"
                    ? "New supplier auto-created from voice"
                    : `Auto-matched from voice with ${Math.round(parsed.supplier_match_score * 100)}% confidence`}
                </span>
              )}
            </label>
            <label className="space-y-2">
              <span className="label">Type</span>
              <select className="input" value={parsed.transaction_type} onChange={(event) => updateParsed("transaction_type", event.target.value)}>
                <option value="debit">Debit</option>
                <option value="credit">Credit</option>
              </select>
            </label>
            <label className="space-y-2">
              <span className="label">Date</span>
              <input className="input" type="date" value={parsed.date} onChange={(event) => updateParsed("date", event.target.value)} />
            </label>
            <label className="space-y-2">
              <span className="label">Quantity</span>
              <input className="input" type="number" step="0.01" value={parsed.quantity} onChange={(event) => updateNumber("quantity", event.target.value)} />
            </label>
            <label className="space-y-2">
              <span className="label">Unit</span>
              <input className="input" value={parsed.unit} onChange={(event) => updateParsed("unit", event.target.value)} />
            </label>
            <label className="space-y-2">
              <span className="label">Rate</span>
              <input className="input" type="number" step="0.01" value={parsed.rate} onChange={(event) => updateNumber("rate", event.target.value)} />
            </label>
            <label className="space-y-2">
              <span className="label">Amount</span>
              <input className="input" type="number" step="0.01" value={parsed.amount} onChange={(event) => updateNumber("amount", event.target.value)} />
            </label>
            <label className="space-y-2 sm:col-span-2">
              <span className="label">Description</span>
              <textarea className="input min-h-20" value={parsed.description} onChange={(event) => updateParsed("description", event.target.value)} />
            </label>
          </div>

          <div className="mt-5 rounded-lg bg-slate-50 p-4">
            <p className="text-sm font-semibold text-slate-500">Amount</p>
            <p className="text-2xl font-bold text-slate-950">{formatCurrency(parsed.amount)}</p>
          </div>

          <div className="mt-5 flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
            <button className="btn-secondary w-full sm:w-auto" onClick={() => setParsed(null)} type="button">
              Cancel
            </button>
            <button className="btn-primary w-full sm:w-auto" onClick={saveTransaction} disabled={saving} type="button">
              <Save size={18} />
              {saving ? "Saving..." : "Save Transaction"}
            </button>
          </div>
        </section>
      )}
    </div>
  );
}
