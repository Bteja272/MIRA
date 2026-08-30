import type {
  SpeechRecognitionCallbacks,
  SpeechRecognitionController,
  VoiceRecognitionError,
} from "./voiceTypes";


interface BrowserSpeechRecognitionAlternative {
  transcript: string;
  confidence?: number;
}


interface BrowserSpeechRecognitionResult {
  readonly isFinal: boolean;

  readonly length: number;

  [index: number]:
    BrowserSpeechRecognitionAlternative;
}


interface BrowserSpeechRecognitionResultList {
  readonly length: number;

  [index: number]:
    BrowserSpeechRecognitionResult;
}


interface BrowserSpeechRecognitionEvent
  extends Event {
  readonly resultIndex: number;

  readonly results:
    BrowserSpeechRecognitionResultList;
}


interface BrowserSpeechRecognitionErrorEvent
  extends Event {
  readonly error: string;
  readonly message?: string;
}


interface BrowserSpeechRecognition {
  continuous: boolean;
  interimResults: boolean;
  lang: string;

  onstart:
    | (() => void)
    | null;

  onend:
    | (() => void)
    | null;

  onresult:
    | ((
      event:
        BrowserSpeechRecognitionEvent,
    ) => void)
    | null;

  onerror:
    | ((
      event:
        BrowserSpeechRecognitionErrorEvent,
    ) => void)
    | null;

  start(): void;

  stop(): void;

  abort(): void;
}


type BrowserSpeechRecognitionConstructor =
  new () =>
    BrowserSpeechRecognition;


interface SpeechWindow
  extends Window {
  SpeechRecognition?:
    BrowserSpeechRecognitionConstructor;

  webkitSpeechRecognition?:
    BrowserSpeechRecognitionConstructor;
}


function speechWindow():
  SpeechWindow | null {
  if (
    typeof window === "undefined"
  ) {
    return null;
  }

  return window as SpeechWindow;
}


function recognitionConstructor():
  BrowserSpeechRecognitionConstructor
  | null {
  const browserWindow =
    speechWindow();

  if (!browserWindow) {
    return null;
  }

  return (
    browserWindow
      .SpeechRecognition
    ?? browserWindow
      .webkitSpeechRecognition
    ?? null
  );
}


export function
isSpeechRecognitionSupported():
  boolean {
  return (
    recognitionConstructor()
    !== null
  );
}


export function
voiceErrorMessage(
  errorCode: string,
): string {
  switch (errorCode) {
    case "not-allowed":
    case "service-not-allowed":
      return (
        "Microphone access was denied. "
        + "Allow microphone access in "
        + "your browser settings and "
        + "try again."
      );

    case "audio-capture":
      return (
        "No usable microphone was "
        + "detected."
      );

    case "no-speech":
      return (
        "No speech was detected. "
        + "Try speaking again."
      );

    case "network":
      return (
        "Speech recognition could not "
        + "reach the browser speech "
        + "service."
      );

    case "aborted":
      return (
        "Voice input was cancelled."
      );

    default:
      return (
        "Voice input could not be "
        + "completed."
      );
  }
}


export function
createSpeechRecognition(
  callbacks:
    SpeechRecognitionCallbacks,
): SpeechRecognitionController
  | null {
  const Recognition =
    recognitionConstructor();

  if (!Recognition) {
    return null;
  }

  const recognition =
    new Recognition();

  recognition.continuous =
    false;

  recognition.interimResults =
    true;

  recognition.lang =
    (
      typeof navigator
      !== "undefined"
      && navigator.language
    )
      ? navigator.language
      : "en-US";


  recognition.onstart =
    () => {
      callbacks.onStart?.();
    };


  recognition.onend =
    () => {
      callbacks
        .onInterimTranscript?.(
          "",
        );

      callbacks.onEnd?.();
    };


  recognition.onerror =
    (
      event:
        BrowserSpeechRecognitionErrorEvent,
    ) => {
      const error:
        VoiceRecognitionError = {
          code:
            event.error,

          message:
            voiceErrorMessage(
              event.error,
            ),
        };

      callbacks.onError?.(
        error,
      );
    };


  recognition.onresult =
    (
      event:
        BrowserSpeechRecognitionEvent,
    ) => {
      const finalParts:
        string[] = [];

      const interimParts:
        string[] = [];

      for (
        let index =
          event.resultIndex;
        index
          < event.results.length;
        index += 1
      ) {
        const result =
          event.results[index];

        const alternative =
          result?.[0];

        const transcript =
          alternative
            ?.transcript
            ?.trim();

        if (!transcript) {
          continue;
        }

        if (result.isFinal) {
          finalParts.push(
            transcript,
          );
        } else {
          interimParts.push(
            transcript,
          );
        }
      }

      if (
        interimParts.length > 0
      ) {
        callbacks
          .onInterimTranscript?.(
            interimParts.join(
              " ",
            ),
          );
      } else {
        callbacks
          .onInterimTranscript?.(
            "",
          );
      }

      if (
        finalParts.length > 0
      ) {
        callbacks
          .onFinalTranscript?.(
            finalParts.join(
              " ",
            ),
          );
      }
    };


  return {
    start: () => {
      recognition.start();
    },

    stop: () => {
      recognition.stop();
    },

    abort: () => {
      recognition.abort();
    },
  };
}