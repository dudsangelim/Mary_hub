"use client";

import { SessionStep } from "@/lib/tutorApi";
import AudioPlayer from "./AudioPlayer";
import BigButton from "./BigButton";

interface StepScreenProps {
  step: SessionStep;
  stepNumber: number;
  totalSteps: number;
  audioUrl: string | null;
  onDone: () => void;
  loading: boolean;
}

export default function StepScreen({ step, stepNumber, totalSteps, audioUrl, onDone, loading }: StepScreenProps) {
  return (
    <div className="flex min-h-screen flex-col bg-white p-6">
      <div className="mb-4 text-sm text-gray-400">
        Tarefa {stepNumber} de {totalSteps}
      </div>

      <div className="flex flex-1 flex-col gap-4">
        {step.subject && (
          <div className="inline-block rounded-full bg-blue-100 px-4 py-1 text-sm font-semibold text-blue-700">
            {step.subject}
          </div>
        )}
        <h2 className="text-2xl font-bold text-gray-800">{step.task_title}</h2>
        <p className="text-lg text-gray-600">{step.instruction}</p>

        {step.pages && (
          <div className="rounded-xl bg-yellow-50 px-4 py-3">
            <span className="font-semibold text-yellow-700">📄 Páginas:</span>{" "}
            <span className="text-yellow-800">{step.pages}</span>
          </div>
        )}
        {step.book_reference && (
          <div className="rounded-xl bg-orange-50 px-4 py-3">
            <span className="font-semibold text-orange-700">📚 Livro:</span>{" "}
            <span className="text-orange-800">{step.book_reference}</span>
          </div>
        )}

        <AudioPlayer audioUrl={audioUrl} autoPlay />
      </div>

      <div className="pb-4">
        <BigButton
          label={loading ? "Salvando..." : "Feito! ✅"}
          onClick={onDone}
          disabled={loading}
          variant="success"
        />
      </div>
    </div>
  );
}
