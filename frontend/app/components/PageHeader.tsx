export default function PageHeader({ title, subtitle }: { title: string; subtitle: string }) {
  return (
    <div className="mb-8">
      <h1 className="text-2xl font-semibold text-[#f0ead8] mb-1 tracking-tight">{title}</h1>
      <p className="text-xs text-[#f0ead8]/30 tracking-widest uppercase">{subtitle}</p>
    </div>
  )
}
