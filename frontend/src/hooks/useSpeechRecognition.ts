import {
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";

import {
  createSpeechRecognition,
  isSpeechRecognitionSupported,
} from "../voice/speechRecognition";

import type {
  SpeechRecognitionController,
  VoiceRecognitionError,
  VoiceRecognitionState,
} from "../voice/voiceTypes";


interface UseSpeechRecognitionOptions {
  onFinalTranscript?: (
    transcript: string,
  ) => void;

  onListeningChange?: (
    listening: boolean,
  ) => void;
}


export function
useSpeechRecognition({
  onFinalTranscript,
  onListeningChange,
}: UseSpeechRecognitionOptions) {
  const supported =
    isSpeechRecognitionSupported();


  const [
    state,
    setState,
  ] = useState<
    VoiceRecognitionState
  >(
    supported
      ? "idle"
      : "unsupported",
  );


  const [
    interimTranscript,
    setInterimTranscript,
  ] = useState("");


  const [
    error,
    setError,
  ] = useState<
    VoiceRecognitionError | null
  >(null);


  const controllerRef =
    useRef<
      SpeechRecognitionController
      | null
    >(null);


  const recognitionErroredRef =
    useRef(false);


  const finalTranscriptCallbackRef =
    useRef(
      onFinalTranscript,
    );


  const listeningCallbackRef =
    useRef(
      onListeningChange,
    );


  useEffect(
    () => {
      finalTranscriptCallbackRef
        .current =
        onFinalTranscript;
    },
    [
      onFinalTranscript,
    ],
  );


  useEffect(
    () => {
      listeningCallbackRef
        .current =
        onListeningChange;
    },
    [
      onListeningChange,
    ],
  );


  const setListening =
    useCallback(
      (
        listening: boolean,
      ) => {
        listeningCallbackRef
          .current?.(
            listening,
          );
      },
      [],
    );


  const stop =
    useCallback(
      () => {
        controllerRef
          .current?.stop();
      },
      [],
    );


  const abort =
    useCallback(
      () => {
        controllerRef
          .current?.abort();

        controllerRef.current =
          null;

        recognitionErroredRef.current =
          false;

        setInterimTranscript(
          "",
        );

        setError(
          null,
        );

        setState(
          supported
            ? "idle"
            : "unsupported",
        );

        setListening(
          false,
        );
      },
      [
        setListening,
        supported,
      ],
    );


  const start =
    useCallback(
      () => {
        if (!supported) {
          setState(
            "unsupported",
          );

          return;
        }

        /*
         * Prevent duplicate recognition
         * sessions while one is already
         * active or starting.
         */
        if (
          controllerRef.current
        ) {
          return;
        }


        recognitionErroredRef.current =
          false;

        setError(
          null,
        );

        setInterimTranscript(
          "",
        );


        const controller =
          createSpeechRecognition({
            onStart: () => {
              setState(
                "listening",
              );

              setListening(
                true,
              );
            },

            onEnd: () => {
              controllerRef.current =
                null;

              setInterimTranscript(
                "",
              );

              /*
               * Browsers often emit
               * onerror followed by onend.
               *
               * Preserve the error state
               * instead of immediately
               * replacing it with idle.
               */
              if (
                !recognitionErroredRef
                  .current
              ) {
                setState(
                  "idle",
                );
              }

              setListening(
                false,
              );
            },

            onFinalTranscript: (
              transcript,
            ) => {
              finalTranscriptCallbackRef
                .current?.(
                  transcript,
                );
            },

            onInterimTranscript: (
              transcript,
            ) => {
              setInterimTranscript(
                transcript,
              );
            },

            onError: (
              recognitionError,
            ) => {
              recognitionErroredRef.current =
                true;

              setError(
                recognitionError,
              );

              setState(
                "error",
              );

              setListening(
                false,
              );
            },
          });


        if (!controller) {
          setState(
            "unsupported",
          );

          return;
        }


        controllerRef.current =
          controller;


        try {
          controller.start();
        } catch {
          controllerRef.current =
            null;

          recognitionErroredRef.current =
            true;

          setState(
            "error",
          );

          setError({
            code:
              "start-failed",

            message:
              (
                "Voice input could not "
                + "be started."
              ),
          });

          setListening(
            false,
          );
        }
      },
      [
        setListening,
        supported,
      ],
    );


  useEffect(
    () => (
      () => {
        controllerRef
          .current?.abort();

        controllerRef.current =
          null;
      }
    ),
    [],
  );


  return {
    supported,

    state,

    isListening:
      state === "listening",

    interimTranscript,

    error,

    start,

    stop,

    abort,
  };
}