"use client";

import { useRouter } from "next/navigation";
import AudioPlayer from "./AudioPlayer";
import BigButton from "./BigButton";

interface CelebrationScreenProps {
  studentName: string;
  audioUrl: string | null;
  completedTasks: number;
}

export default function CelebrationScreen({ studentName, audioUrl, completedTasks }: CelebrationScreenProps) {
  const router = useRouter();

  return (
    <div className="flex min-h-screen flex-col items-center justify-between bg-green-50 p-6">
      <div className="flex flex-1 flex-col items-center justify-center gap-6 text-center">
        <div className="text-8xl">🎉</div>
        <h1 className="text-3xl font-bold text-green-700">Parabéns, {studentName}!</h1>
        <p className="text-xl text-gray-700">
          Você completou {completedTasks} {completedTasks === 1 ? "tarefa" : "tarefas"} hoje!
        </p>
        <AudioPlayer audioUrl={audioUrl} autoPlay />
      </div>
      <div className="w-full max-w-sm pb-4">
        <BigButton
          label="Voltar para o início"
          onClick={() => router.push("/")}
          variant="secondary"
        />
      </div>
    </div>
  );
}
