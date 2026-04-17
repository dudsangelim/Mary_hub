"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";
import { createOrGetSession, nextStep, requestTTS, getTTSAudioUrl, TutorSession, SessionStep } from "@/lib/tutorApi";
import WelcomeScreen from "@/components/tutor/WelcomeScreen";
import StepScreen from "@/components/tutor/StepScreen";
import CelebrationScreen from "@/components/tutor/CelebrationScreen";

type Screen = "loading" | "welcome" | "task" | "celebration" | "error";

export default function TutorPage() {
  const { student_id } = useParams<{ student_id: string }>();
  const router = useRouter();

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

  const handleStuck = async () => {
    if (!session || !currentStep) return;
    setLoading(true);
    try {
      const stepId = String(currentStep.index);
      await apiFetch(`/tutor/sessions/${session.id}/stuck`, {
        method: "POST",
        body: JSON.stringify({ step_id: stepId, reason: "Criança pediu ajuda" }),
      });
      alert("Tudo bem! Pede pro papai ou mamãe te ajudar 😊");
    } catch {
      // silencioso
    } finally {
      setLoading(false);
    }
  };

  const studentName = (session?.student_name ?? "Lucas").split(" ")[0];

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
        <div className="text-center">
          <p className="text-xl text-red-600">{error ?? "Erro desconhecido."}</p>
          <button
            onClick={() => router.push("/dashboard")}
            className="mt-4 rounded-2xl bg-slate-100 px-6 py-3 text-sm font-semibold text-slate-700"
          >
            Voltar ao painel
          </button>
        </div>
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
        onStuck={handleStuck}
        loading={loading}
      />
    );
  }

  return null;
}
