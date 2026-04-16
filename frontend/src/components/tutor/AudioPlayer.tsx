"use client";

import { useEffect, useRef, useState } from "react";

interface AudioPlayerProps {
  audioUrl: string | null;
  autoPlay?: boolean;
  onEnded?: () => void;
}

export default function AudioPlayer({ audioUrl, autoPlay = true, onEnded }: AudioPlayerProps) {
  const audioRef = useRef<HTMLAudioElement>(null);
  const [playing, setPlaying] = useState(false);
  const [error, setError] = useState(false);

  useEffect(() => {
    if (!audioUrl) return;
    setError(false);
    const audio = audioRef.current;
    if (!audio) return;
    audio.src = audioUrl;
    if (autoPlay) {
      audio.play().catch(() => setError(true));
    }
  }, [audioUrl, autoPlay]);

  const toggle = () => {
    const audio = audioRef.current;
    if (!audio) return;
    if (playing) {
      audio.pause();
    } else {
      audio.play().catch(() => setError(true));
    }
  };

  if (!audioUrl) return null;

  return (
    <div className="flex items-center gap-3">
      <audio
        ref={audioRef}
        onPlay={() => setPlaying(true)}
        onPause={() => setPlaying(false)}
        onEnded={() => { setPlaying(false); onEnded?.(); }}
        onError={() => setError(true)}
      />
      <button
        onClick={toggle}
        className="flex h-14 w-14 items-center justify-center rounded-full bg-blue-100 text-2xl shadow hover:bg-blue-200 active:scale-95"
        aria-label={playing ? "Pausar" : "Ouvir"}
      >
        {error ? "🔇" : playing ? "⏸" : "▶️"}
      </button>
      {error && <span className="text-sm text-red-500">Áudio indisponível</span>}
    </div>
  );
}
