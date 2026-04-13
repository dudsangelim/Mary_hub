import type { Student, Subject, Task } from "@/lib/types";

import { EmptyState } from "@/components/ui/EmptyState";
import { TaskCard } from "@/components/tasks/TaskCard";

export function TaskList({
  tasks,
  students,
  subjects,
  onStatusChange
}: {
  tasks: Task[];
  students: Student[];
  subjects: Subject[];
  onStatusChange?: (task: Task, status: string) => void;
}) {
  if (tasks.length === 0) {
    return <EmptyState title="Nenhuma tarefa" description="Crie um dever manual para Lucas ou Malu." href="/tasks/new" cta="Nova tarefa" />;
  }

  return (
    <div className="grid gap-4">
      {tasks.map((task) => (
        <TaskCard key={task.id} task={task} students={students} subjects={subjects} onStatusChange={onStatusChange} />
      ))}
    </div>
  );
}
