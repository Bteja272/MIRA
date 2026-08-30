import {
  useSpeechRecognition,
} from "../hooks/useSpeechRecognition";


interface VoiceInputButtonProps {
  disabled?: boolean;

  onTranscript: (
    transcript: string,
  ) => void;

  onListeningChange?: (
    listening: boolean,
  ) => void;
}


export function VoiceInputButton({
  disabled = false,
  onTranscript,
  onListeningChange,
}: VoiceInputButtonProps) {
  const {
    supported,
    isListening,
    interimTranscript,
    error,
    start,
    stop,
  } = useSpeechRecognition({
    onFinalTranscript:
      onTranscript,

    onListeningChange,
  });


  if (!supported) {
    return (
      <div
        className={
          "voice-input-control"
        }
      >
        <button
          className={
            "button "
            + "button--secondary "
            + "voice-input-button"
          }
          type="button"
          disabled
          title={
            (
              "Voice input is not "
              + "supported by this "
              + "browser."
            )
          }
        >
          <span
            aria-hidden="true"
          >
            🎤
          </span>

          Voice unavailable
        </button>
      </div>
    );
  }


  return (
    <div
      className={
        "voice-input-control"
      }
    >
      {isListening ? (
        <button
          className={
            "button "
            + "button--secondary "
            + "voice-input-button "
            + "voice-input-button"
            + "--listening"
          }
          type="button"
          onClick={stop}
        >
          <span
            className={
              "voice-listening-dot"
            }
            aria-hidden="true"
          />

          Stop listening
        </button>
      ) : (
        <button
          className={
            "button "
            + "button--secondary "
            + "voice-input-button"
          }
          type="button"
          disabled={disabled}
          onClick={start}
        >
          <span
            aria-hidden="true"
          >
            🎤
          </span>

          Voice input
        </button>
      )}


      {isListening ? (
        <span
          className={
            "voice-input-status"
          }
          role="status"
          aria-live="polite"
        >
          {interimTranscript
            ? (
              `Listening: ${
                interimTranscript
              }`
            )
            : "Listening…"}
        </span>
      ) : null}


      {error ? (
        <span
          className={
            "voice-input-error"
          }
          role="alert"
        >
          {error.message}
        </span>
      ) : null}
    </div>
  );
}