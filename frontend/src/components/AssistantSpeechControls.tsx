import type {
  SpeechPlaybackState,
} from "../hooks/useSpeechSynthesis";


type AssistantSpeechControlsProps = {
  messageId: string;
  text: string;
  supported: boolean;
  state: SpeechPlaybackState;
  activeMessageId: string | null;
  lastSpokenMessageId: string | null;
  error: string | null;
  onListen: (
    messageId: string,
    text: string,
  ) => void;
  onPause: () => void;
  onResume: () => void;
  onStop: () => void;
  onReplay: (
    messageId: string,
    text: string,
  ) => void;
};


export function AssistantSpeechControls({
  messageId,
  text,
  supported,
  state,
  activeMessageId,
  lastSpokenMessageId,
  error,
  onListen,
  onPause,
  onResume,
  onStop,
  onReplay,
}: AssistantSpeechControlsProps) {
  const isActive =
    activeMessageId === messageId;

  const wasLastSpoken =
    lastSpokenMessageId === messageId;


  if (!text.trim()) {
    return null;
  }


  if (!supported) {
    return (
      <div
        className="assistant-speech-controls"
      >
        <button
          className="assistant-speech-button"
          type="button"
          disabled
          title={
            (
              "Text-to-speech is not "
              + "available in this browser."
            )
          }
        >
          Listen unavailable
        </button>
      </div>
    );
  }


  return (
    <div
      className="assistant-speech-controls"
      aria-label="MIRA response audio"
    >
      {(
        isActive
        && state === "speaking"
      ) ? (
        <>
          <button
            className="assistant-speech-button"
            type="button"
            onClick={onPause}
          >
            Pause
          </button>

          <button
            className="assistant-speech-button"
            type="button"
            onClick={onStop}
          >
            Stop
          </button>
        </>
      ) : null}


      {(
        isActive
        && state === "paused"
      ) ? (
        <>
          <button
            className="assistant-speech-button"
            type="button"
            onClick={onResume}
          >
            Resume
          </button>

          <button
            className="assistant-speech-button"
            type="button"
            onClick={onStop}
          >
            Stop
          </button>

          <button
            className="assistant-speech-button"
            type="button"
            onClick={() => {
              onReplay(
                messageId,
                text,
              );
            }}
          >
            Replay
          </button>
        </>
      ) : null}


      {(
        !isActive
        && state !== "unsupported"
      ) ? (
        <button
          className="assistant-speech-button"
          type="button"
          onClick={() => {
            if (wasLastSpoken) {
              onReplay(
                messageId,
                text,
              );

              return;
            }

            onListen(
              messageId,
              text,
            );
          }}
        >
          {wasLastSpoken
            ? "Replay"
            : "Listen"}
        </button>
      ) : null}


      {(
        wasLastSpoken
        && state === "error"
        && error
      ) ? (
        <span
          className="assistant-speech-error"
          role="alert"
        >
          {error}
        </span>
      ) : null}
    </div>
  );
}
