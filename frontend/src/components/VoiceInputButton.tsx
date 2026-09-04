import {
  forwardRef,
  useImperativeHandle,
} from "react";

import {
  useSpeechRecognition,
} from "../hooks/useSpeechRecognition";


export type VoiceInputButtonHandle = {
  abort: () => void;
  stop: () => void;
};


interface VoiceInputButtonProps {
  disabled?: boolean;

  onTranscript: (
    transcript: string,
  ) => void;

  onListeningChange?: (
    listening: boolean,
  ) => void;

  /*
   * Used by AskMiraPage to stop TTS
   * before recognition begins.
   */
  onBeforeStart?: () => void;
}


export const VoiceInputButton =
forwardRef<
  VoiceInputButtonHandle,
  VoiceInputButtonProps
>(
  function VoiceInputButton(
    {
      disabled = false,
      onTranscript,
      onListeningChange,
      onBeforeStart,
    },
    ref,
  ) {
    const {
      supported,
      isListening,
      interimTranscript,
      error,
      start,
      stop,
      abort,
    } = useSpeechRecognition({
      onFinalTranscript:
        onTranscript,

      onListeningChange,
    });


    useImperativeHandle(
      ref,
      () => ({
        abort,
        stop,
      }),
      [
        abort,
        stop,
      ],
    );


    function handleStart():
    void {
      /*
       * Browser recognition and browser
       * synthesis should never run at the
       * same time.
       */
      onBeforeStart?.();

      start();
    }


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
            onClick={
              handleStart
            }
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
  },
);