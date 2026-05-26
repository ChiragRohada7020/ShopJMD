export default function Loading({ label = "Loading..." }) {
  return (
    <div className="card grid min-h-40 place-items-center p-6 text-center">
      <div>
        <div className="mx-auto h-10 w-10 animate-spin rounded-full border-4 border-emerald-100 border-t-emerald-600" />
        <p className="mt-3 font-semibold text-slate-500">{label}</p>
      </div>
    </div>
  );
}
