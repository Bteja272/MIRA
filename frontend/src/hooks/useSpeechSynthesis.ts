import {
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";

import {
  createSpeechUtterance,
  isSpeechSynthesisSupported,
} from "../voice/speechSynthesis";


export type SpeechPlaybackState =
  | "unsupported"
  | "idle"
  | "speaking"
  | "paused"
  | "error";


export type UseSpeechSynthesisResult = {
  supported: boolean;
  state: SpeechPlaybackState;
  activeMessageId: string | null;
  lastSpokenMessageId: string | null;
  error: string | null;

  speak: (
    messageId: string,
    text: string,
  ) => void;

  pause: () => void;

  resume: () => void;

  stop: () => void;

  replay: (
    messageId: string,
    text: string,
  ) => void;
};


function playbackErrorMessage():
string {
  return (
    "MIRA could not play this response "
    + "through the browser speech service."
  );
}


function getSpeechSynthesis():
SpeechSynthesis | null {
  if (
    typeof window === "undefined"
    || !window.speechSynthesis
  ) {
    return null;
  }

  return window.speechSynthesis;
}


export function useSpeechSynthesis():
UseSpeechSynthesisResult {
  const supported =
    isSpeechSynthesisSupported();

  const [
    state,
    setState,
  ] = useState<SpeechPlaybackState>(
    supported
      ? "idle"
      : "unsupported",
  );

  const [
    activeMessageId,
    setActiveMessageId,
  ] = useState<string | null>(
    null,
  );

  const [
    lastSpokenMessageId,
    setLastSpokenMessageId,
  ] = useState<string | null>(
    null,
  );

  const [
    error,
    setError,
  ] = useState<string | null>(
    null,
  );

  const sessionRef =
    useRef(0);


  const stop = useCallback(
    () => {
        sessionRef.current += 1;


        /*
        * speechSynthesis is browser-global.
        *
        * Always cancel the native queue,
        * even if React currently believes
        * nothing is active.
        */
        getSpeechSynthesis()
        ?.cancel();


        setActiveMessageId(
        null,
        );

        setLastSpokenMessageId(
        null,
        );

        setError(
        null,
        );

        setState(
        supported
            ? "idle"
            : "unsupported",
        );
    },
    [
        supported,
    ],
    );


  const speak = useCallback(
    (
      messageId: string,
      text: string,
    ) => {
      if (!supported) {
        return;
      }

      const speechSynthesis =
        getSpeechSynthesis();

      if (!speechSynthesis) {
        setActiveMessageId(
          null,
        );

        setError(
          playbackErrorMessage(),
        );

        setState(
          "error",
        );

        return;
      }

      const utterance =
        createSpeechUtterance(
          text,
        );

      if (!utterance) {
        setActiveMessageId(
          null,
        );

        setError(
          playbackErrorMessage(),
        );

        setState(
          "error",
        );

        return;
      }

      sessionRef.current += 1;

      const sessionId =
        sessionRef.current;

      /*
       * Only one MIRA response should
       * play at a time.
       */
      speechSynthesis.cancel();

      setError(
        null,
      );

      setActiveMessageId(
        messageId,
      );

      setLastSpokenMessageId(
        messageId,
      );

      setState(
        "speaking",
      );


      utterance.onstart = () => {
        if (
          sessionRef.current
          !== sessionId
        ) {
          return;
        }

        setState(
          "speaking",
        );
      };


      utterance.onend = () => {
        if (
          sessionRef.current
          !== sessionId
        ) {
          return;
        }

        setActiveMessageId(
          null,
        );

        setState(
          "idle",
        );
      };


      utterance.onerror = () => {
        if (
          sessionRef.current
          !== sessionId
        ) {
          return;
        }

        setActiveMessageId(
          null,
        );

        setError(
          playbackErrorMessage(),
        );

        setState(
          "error",
        );
      };


      try {
        speechSynthesis.speak(
          utterance,
        );
      } catch {
        if (
          sessionRef.current
          !== sessionId
        ) {
          return;
        }

        setActiveMessageId(
          null,
        );

        setError(
          playbackErrorMessage(),
        );

        setState(
          "error",
        );
      }
    },
    [
      supported,
    ],
  );


  const pause = useCallback(
    () => {
      if (
        !supported
        || !activeMessageId
        || state !== "speaking"
      ) {
        return;
      }

      const speechSynthesis =
        getSpeechSynthesis();

      if (!speechSynthesis) {
        setActiveMessageId(
          null,
        );

        setError(
          playbackErrorMessage(),
        );

        setState(
          "error",
        );

        return;
      }

      speechSynthesis.pause();

      setState(
        "paused",
      );
    },
    [
      activeMessageId,
      state,
      supported,
    ],
  );


  const resume = useCallback(
    () => {
      if (
        !supported
        || !activeMessageId
        || state !== "paused"
      ) {
        return;
      }

      const speechSynthesis =
        getSpeechSynthesis();

      if (!speechSynthesis) {
        setActiveMessageId(
          null,
        );

        setError(
          playbackErrorMessage(),
        );

        setState(
          "error",
        );

        return;
      }

      speechSynthesis.resume();

      setState(
        "speaking",
      );
    },
    [
      activeMessageId,
      state,
      supported,
    ],
  );


  const replay = useCallback(
    (
      messageId: string,
      text: string,
    ) => {
      speak(
        messageId,
        text,
      );
    },
    [
      speak,
    ],
  );


  useEffect(
    () => {
      return () => {
        if (!supported) {
          return;
        }

        /*
         * In tests or during unusual
         * browser teardown, the native
         * speech API may disappear before
         * React runs this cleanup.
         */
        sessionRef.current += 1;

        getSpeechSynthesis()
          ?.cancel();
      };
    },
    [
      supported,
    ],
  );


  return {
    supported,
    state,
    activeMessageId,
    lastSpokenMessageId,
    error,
    speak,
    pause,
    resume,
    stop,
    replay,
  };
}