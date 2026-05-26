export default function EmptyState({ title, action }) {
  return (
    <div className="card grid min-h-44 place-items-center p-6 text-center">
      <div>
        <p className="text-lg font-bold text-slate-900">{title}</p>
        {action && <div className="mt-4">{action}</div>}
      </div>
    </div>
  );
}
