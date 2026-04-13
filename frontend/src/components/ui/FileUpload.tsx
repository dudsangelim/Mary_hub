"use client";

export function FileUpload({ file, onChange }: { file: File | null; onChange: (file: File | null) => void }) {
  const preview = file && file.type.startsWith("image/") ? URL.createObjectURL(file) : null;

  return (
    <label className="flex cursor-pointer flex-col items-center justify-center rounded-3xl border border-dashed border-slate-300 bg-white p-6 text-center">
      <span className="text-sm font-medium text-slate-700">Arraste uma foto/PDF ou clique para escolher</span>
      <input className="hidden" type="file" accept="image/jpeg,image/png,image/webp,application/pdf" onChange={(event) => onChange(event.target.files?.[0] ?? null)} />
      {file ? <span className="mt-3 text-sm text-slate-600">{file.name}</span> : null}
      {preview ? <img src={preview} alt="Pré-visualização" className="mt-4 h-32 rounded-2xl object-cover" /> : null}
    </label>
  );
}
