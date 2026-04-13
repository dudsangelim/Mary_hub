import Link from "next/link";

export function EmptyState({ title, description, href, cta }: { title: string; description: string; href: string; cta: string }) {
  return (
    <div className="rounded-3xl border border-dashed border-slate-300 bg-white p-8 text-center">
      <h3 className="text-lg font-semibold text-slate-900">{title}</h3>
      <p className="mt-2 text-sm text-slate-600">{description}</p>
      <Link href={href} className="mt-4 inline-flex rounded-2xl bg-slate-900 px-4 py-2 text-sm font-semibold text-white">
        {cta}
      </Link>
    </div>
  );
}
