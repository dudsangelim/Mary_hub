"use client";

import { SessionStep } from "@/lib/tutorApi";
import AudioPlayer from "./AudioPlayer";
import BigButton from "./BigButton";

interface WelcomeScreenProps {
  step: SessionStep;
  studentName: string;
  audioUrl: string | null;
  onStart: () => void;
  loading: boolean;
}

export default function WelcomeScreen({ step, studentName, audioUrl, onStart, loading }: WelcomeScreenProps) {
  return (
    <div className="flex min-h-screen flex-col items-center justify-between bg-blue-50 p-6">
      <div className="flex flex-1 flex-col items-center justify-center gap-6 text-center">
        <div className="text-6xl">👋</div>
        <h1 className="text-3xl font-bold text-blue-700">Olá, {studentName}!</h1>
        <p className="text-xl text-gray-700">{step.instruction}</p>
        <AudioPlayer audioUrl={audioUrl} autoPlay />
      </div>
      <div className="w-full max-w-sm pb-4">
        <BigButton
          label={loading ? "Carregando..." : "Vamos começar! 🚀"}
          onClick={onStart}
          disabled={loading}
          variant="primary"
        />
      </div>
    </div>
  );
}
