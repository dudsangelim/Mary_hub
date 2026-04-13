import type { Material, Student, Subject } from "@/lib/types";

import { EmptyState } from "@/components/ui/EmptyState";
import { MaterialCard } from "@/components/materials/MaterialCard";

export function MaterialList({ materials, students, subjects }: { materials: Material[]; students: Student[]; subjects: Subject[] }) {
  if (materials.length === 0) {
    return <EmptyState title="Nenhum material" description="Cadastre um material manual, foto ou PDF." href="/materials/new" cta="Novo material" />;
  }

  return (
    <div className="grid gap-4">
      {materials.map((material) => (
        <MaterialCard key={material.id} material={material} students={students} subjects={subjects} />
      ))}
    </div>
  );
}
