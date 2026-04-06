"use client";

import { useState, useRef, useEffect } from "react";
import { Mic, MicOff, Volume2, VolumeX } from "lucide-react";

declare global {
  interface Window {
    SpeechRecognition: typeof SpeechRecognition;
    webkitSpeechRecognition: typeof SpeechRecognition;
  }
}

declare class SpeechRecognition extends EventTarget {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  onresult: ((event: SpeechRecognitionEvent) => void) | null;
  onerror: ((event: SpeechRecognitionErrorEvent) => void) | null;
  onend: (() => void) | null;
  start(): void;
  stop(): void;
}

interface SpeechRecognitionEvent extends Event {
  results: SpeechRecognitionResultList;
}

interface SpeechRecognitionResultList {
  [index: number]: SpeechRecognitionResult;
  length: number;
}

interface SpeechRecognitionResult {
  [index: number]: SpeechRecognitionAlternative;
  isFinal: boolean;
  length: number;
}

interface SpeechRecognitionAlternative {
  transcript: string;
  confidence: number;
}

interface SpeechRecognitionErrorEvent extends Event {
  error: string;
}

interface VoiceChatProps {
  onTranscript: (text: string) => void;
  lastResponse?: string;
  language?: "en-IN" | "hi-IN";
}

export function VoiceChat({
  onTranscript,
  lastResponse,
  language = "en-IN",
}: VoiceChatProps) {
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isSupported, setIsSupported] = useState(() => {
    const SpeechRecognitionAPI =
      (
        window as unknown as {
          SpeechRecognition?: typeof SpeechRecognition;
          webkitSpeechRecognition?: typeof SpeechRecognition;
        }
      ).SpeechRecognition ||
      (
        window as unknown as {
          webkitSpeechRecognition?: typeof SpeechRecognition;
        }
      ).webkitSpeechRecognition;
    return !!SpeechRecognitionAPI;
  });
  const [transcript, setTranscript] = useState("");

  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const synthesisRef = useRef<SpeechSynthesisUtterance | null>(null);

  const stopSpeaking = () => {
    if ("speechSynthesis" in window) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
    }
  };

  useEffect(() => {
    // Check browser support
    const SpeechRecognitionAPI =
      (
        window as unknown as {
          SpeechRecognition?: typeof SpeechRecognition;
          webkitSpeechRecognition?: typeof SpeechRecognition;
        }
      ).SpeechRecognition ||
      (
        window as unknown as {
          webkitSpeechRecognition?: typeof SpeechRecognition;
        }
      ).webkitSpeechRecognition;

    if (!SpeechRecognitionAPI) {
      console.error("Speech recognition not supported");
      return;
    }

    // Initialize speech recognition
    recognitionRef.current = new SpeechRecognitionAPI();
    recognitionRef.current.continuous = false;
    recognitionRef.current.interimResults = false;
    recognitionRef.current.lang = language;

    recognitionRef.current.onresult = (event: SpeechRecognitionEvent) => {
      const transcriptText = event.results[0][0].transcript;
      setTranscript(transcriptText);
      onTranscript(transcriptText);
      setIsListening(false);
    };

    recognitionRef.current.onerror = (event: SpeechRecognitionErrorEvent) => {
      console.error("Speech recognition error:", event.error);
      setIsListening(false);
    };

    recognitionRef.current.onend = () => {
      setIsListening(false);
    };

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
      stopSpeaking();
    };
  }, [language, onTranscript]);

  const startListening = () => {
    if (!recognitionRef.current) return;

    try {
      setTranscript("");
      recognitionRef.current.start();
      setIsListening(true);
    } catch (error) {
      console.error("Error starting recognition:", error);
    }
  };

  const stopListening = () => {
    if (!recognitionRef.current) return;

    try {
      recognitionRef.current.stop();
      setIsListening(false);
    } catch (error) {
      console.error("Error stopping recognition:", error);
    }
  };

  const speakText = (text: string) => {
    if (!("speechSynthesis" in window)) {
      console.error("Speech synthesis not supported");
      return;
    }

    // Stop any ongoing speech
    stopSpeaking();

    // Clean text for speech
    const cleanText = text
      .replace(/[*_~`#]/g, "")
      .replace(/\[([^\]]+)\]\([^\)]+\)/g, "$1")
      .replace(/\n+/g, ". ");

    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.lang = language;
    utterance.rate = 0.9;
    utterance.pitch = 1.0;
    utterance.volume = 1.0;

    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);

    synthesisRef.current = utterance;
    window.speechSynthesis.speak(utterance);
  };

  const toggleListening = () => {
    if (isListening) {
      stopListening();
    } else {
      startListening();
    }
  };

  const toggleSpeaking = () => {
    if (isSpeaking) {
      stopSpeaking();
    } else if (lastResponse) {
      speakText(lastResponse);
    }
  };

  if (!isSupported) {
    return (
      <div className="text-sm text-red-500 p-2 bg-red-50 rounded">
        ⚠️ Voice features not supported in this browser. Please use Chrome or
        Edge.
      </div>
    );
  }

  return (
    <div className="flex items-center gap-3">
      {/* Microphone button */}
      <button
        onClick={toggleListening}
        disabled={isSpeaking}
        className={`p-3 rounded-lg transition-all shadow-sm ${
          isListening
            ? "bg-red-500 text-white animate-pulse"
            : "bg-white border-2 border-slate-300 text-slate-700 hover:bg-slate-50 hover:border-slate-400"
        } disabled:opacity-50 disabled:cursor-not-allowed`}
        title={isListening ? "Stop listening" : "Start voice input"}
      >
        {isListening ? (
          <MicOff className="w-5 h-5" />
        ) : (
          <Mic className="w-5 h-5" />
        )}
      </button>

      {/* Speaker button */}
      <button
        onClick={toggleSpeaking}
        disabled={!lastResponse || isListening}
        className={`p-3 rounded-lg transition-all shadow-sm ${
          isSpeaking
            ? "bg-blue-500 text-white"
            : "bg-white border-2 border-slate-300 text-slate-700 hover:bg-slate-50 hover:border-slate-400"
        } disabled:opacity-50 disabled:cursor-not-allowed`}
        title={isSpeaking ? "Stop speaking" : "Read response aloud"}
      >
        {isSpeaking ? (
          <VolumeX className="w-5 h-5" />
        ) : (
          <Volume2 className="w-5 h-5" />
        )}
      </button>

      {/* Status indicator */}
      <div className="flex flex-col">
        {isListening && (
          <span className="text-sm text-red-600 font-medium animate-pulse">
            🎤 Listening...
          </span>
        )}

        {isSpeaking && (
          <span className="text-sm text-blue-600 font-medium">
            🔊 Speaking...
          </span>
        )}

        {transcript && !isListening && (
          <span className="text-xs text-slate-500 max-w-xs truncate">
            &quot;{transcript}&quot;
          </span>
        )}
      </div>
    </div>
  );
}
