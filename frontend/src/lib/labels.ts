export function getTaskStatusLabel(status: string) {
  switch (status) {
    case "pending":
      return "Pendente";
    case "in_progress":
      return "Em andamento";
    case "done":
      return "Concluída";
    case "overdue":
      return "Atrasada";
    default:
      return status;
  }
}

export function getTaskPriorityLabel(priority: string) {
  switch (priority) {
    case "low":
      return "Baixa";
    case "normal":
      return "Normal";
    case "high":
      return "Alta";
    case "urgent":
      return "Urgente";
    default:
      return priority;
  }
}
