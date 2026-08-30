export type VoiceRecognitionState =
  | "idle"
  | "listening"
  | "unsupported"
  | "error";

export interface VoiceRecognitionError {
  code: string;
  message: string;
}

export interface SpeechRecognitionController {
  start: () => void;
  stop: () => void;
  abort: () => void;
}

export interface SpeechRecognitionCallbacks {
  onStart?: () => void;
  onEnd?: () => void;

  onFinalTranscript?: (
    transcript: string,
  ) => void;

  onInterimTranscript?: (
    transcript: string,
  ) => void;

  onError?: (
    error: VoiceRecognitionError,
  ) => void;
}