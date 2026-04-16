"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { createOrGetSession, nextStep, requestTTS, getTTSAudioUrl, TutorSession, SessionStep } from "@/lib/tutorApi";
import WelcomeScreen from "@/components/tutor/WelcomeScreen";
import StepScreen from "@/components/tutor/StepScreen";
import CelebrationScreen from "@/components/tutor/CelebrationScreen";

type Screen = "loading" | "welcome" | "task" | "celebration" | "error";

export default function TutorPage() {
  const { student_id } = useParams<{ student_id: string }>();

  const [screen, setScreen] = useState<Screen>("loading");
  const [session, setSession] = useState<TutorSession | null>(null);
  const [currentStep, setCurrentStep] = useState<SessionStep | null>(null);
  const [stepIndex, setStepIndex] = useState(0);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [completedTasks, setCompletedTasks] = useState(0);

  const today = new Date().toISOString().split("T")[0];

  useEffect(() => {
    if (!student_id) return;
    (async () => {
      try {
        const s = await createOrGetSession(student_id, today);
        setSession(s);
        const firstStep = s.steps[0] ?? null;
        setCurrentStep(firstStep);
        setStepIndex(0);
        if (firstStep?.instruction) {
          await fetchAudio(firstStep.instruction);
        }
        setScreen(firstStep?.kind === "intro" ? "welcome" : "task");
      } catch {
        setError("Não foi possível carregar a sessão.");
        setScreen("error");
      }
    })();
  }, [student_id]);

  const fetchAudio = async (text: string) => {
    try {
      const tts = await requestTTS(text);
      setAudioUrl(getTTSAudioUrl(tts.audio_key));
    } catch {
      setAudioUrl(null);
    }
  };

  const handleStart = async () => {
    if (!session) return;
    setLoading(true);
    try {
      const res = await nextStep(session.id, 0, false);
      if (res.step) {
        setCurrentStep(res.step);
        setStepIndex(res.step.index);
        if (res.step.instruction) await fetchAudio(res.step.instruction);
        setScreen(res.step.kind === "celebration" ? "celebration" : "task");
      } else {
        setScreen("celebration");
      }
    } catch {
      setError("Erro ao avançar sessão.");
    } finally {
      setLoading(false);
    }
  };

  const handleDone = async () => {
    if (!session || !currentStep) return;
    setLoading(true);
    try {
      const res = await nextStep(session.id, stepIndex, true);
      if (currentStep.kind === "task") {
        setCompletedTasks((n) => n + 1);
      }
      if (res.is_last || !res.step) {
        if (res.step?.instruction) await fetchAudio(res.step.instruction);
        setScreen("celebration");
      } else {
        setCurrentStep(res.step);
        setStepIndex(res.step.index);
        if (res.step.instruction) await fetchAudio(res.step.instruction);
        setScreen(res.step.kind === "celebration" ? "celebration" : "task");
      }
    } catch {
      setError("Erro ao salvar progresso.");
    } finally {
      setLoading(false);
    }
  };

  const studentName = "Lucas";

  if (screen === "loading") {
    return (
      <div className="flex min-h-screen items-center justify-center bg-blue-50">
        <p className="text-xl text-blue-600">Carregando...</p>
      </div>
    );
  }

  if (screen === "error") {
    return (
      <div className="flex min-h-screen items-center justify-center bg-red-50 p-6">
        <p className="text-center text-xl text-red-600">{error ?? "Erro desconhecido."}</p>
      </div>
    );
  }

  if (screen === "celebration") {
    return <CelebrationScreen studentName={studentName} audioUrl={audioUrl} completedTasks={completedTasks} />;
  }

  if (screen === "welcome" && currentStep) {
    return (
      <WelcomeScreen
        step={currentStep}
        studentName={studentName}
        audioUrl={audioUrl}
        onStart={handleStart}
        loading={loading}
      />
    );
  }

  if (screen === "task" && currentStep) {
    const taskSteps = session?.steps.filter((s) => s.kind === "task") ?? [];
    const taskNumber = taskSteps.findIndex((s) => s.index === currentStep.index) + 1;
    return (
      <StepScreen
        step={currentStep}
        stepNumber={taskNumber}
        totalSteps={taskSteps.length}
        audioUrl={audioUrl}
        onDone={handleDone}
        loading={loading}
      />
    );
  }

  return null;
}
