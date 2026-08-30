import {
  afterEach,
  beforeEach,
  describe,
  expect,
  it,
  vi,
} from "vitest";

import {
  createSpeechRecognition,
  isSpeechRecognitionSupported,
  voiceErrorMessage,
} from "./speechRecognition";


interface MockResult {
  isFinal: boolean;

  0: {
    transcript: string;
  };

  length: number;
}


class MockSpeechRecognition {
  static instances:
    MockSpeechRecognition[] = [];


  continuous = false;

  interimResults = false;

  lang = "";


  onstart:
    | (() => void)
    | null = null;


  onend:
    | (() => void)
    | null = null;


  onresult:
    | ((event: any) => void)
    | null = null;


  onerror:
    | ((event: any) => void)
    | null = null;


  start = vi.fn(
    () => {
      this.onstart?.();
    },
  );


  stop = vi.fn(
    () => {
      this.onend?.();
    },
  );


  abort = vi.fn();


  constructor() {
    MockSpeechRecognition
      .instances.push(
        this,
      );
  }


  emitResults(
    results: MockResult[],
  ): void {
    this.onresult?.({
      resultIndex: 0,
      results,
    });
  }


  emitError(
    error: string,
  ): void {
    this.onerror?.({
      error,
    });
  }
}


describe(
  "speechRecognition",
  () => {
    beforeEach(() => {
      MockSpeechRecognition.instances =
        [];

      Object.defineProperty(
        window,
        "SpeechRecognition",
        {
          configurable: true,
          writable: true,
          value:
            MockSpeechRecognition,
        },
      );
    });


    afterEach(() => {
      Reflect.deleteProperty(
        window,
        "SpeechRecognition",
      );

      Reflect.deleteProperty(
        window,
        "webkitSpeechRecognition",
      );

      vi.restoreAllMocks();
    });


    it(
      "detects supported browsers",
      () => {
        expect(
          isSpeechRecognitionSupported(),
        ).toBe(true);
      },
    );


    it(
      (
        "returns null when speech "
        + "recognition is unsupported"
      ),
      () => {
        Reflect.deleteProperty(
          window,
          "SpeechRecognition",
        );

        Reflect.deleteProperty(
          window,
          "webkitSpeechRecognition",
        );


        expect(
          isSpeechRecognitionSupported(),
        ).toBe(false);


        expect(
          createSpeechRecognition({}),
        ).toBeNull();
      },
    );


    it(
      (
        "configures recognition and "
        + "starts it"
      ),
      () => {
        const onStart =
          vi.fn();


        const controller =
          createSpeechRecognition({
            onStart,
          });


        expect(
          controller,
        ).not.toBeNull();


        controller!.start();


        const recognition =
          MockSpeechRecognition
            .instances[0];


        expect(
          recognition.continuous,
        ).toBe(false);

        expect(
          recognition.interimResults,
        ).toBe(true);

        expect(
          recognition.lang,
        ).toBeTruthy();

        expect(
          recognition.start,
        ).toHaveBeenCalledTimes(
          1,
        );

        expect(
          onStart,
        ).toHaveBeenCalledTimes(
          1,
        );
      },
    );


    it(
      (
        "separates interim and final "
        + "transcripts"
      ),
      () => {
        const onFinalTranscript =
          vi.fn();

        const onInterimTranscript =
          vi.fn();


        createSpeechRecognition({
          onFinalTranscript,
          onInterimTranscript,
        });


        const recognition =
          MockSpeechRecognition
            .instances[0];


        recognition.emitResults([
          {
            isFinal: false,
            0: {
              transcript:
                "what is",
            },
            length: 1,
          },
          {
            isFinal: true,
            0: {
              transcript:
                "hemoglobin A1c",
            },
            length: 1,
          },
        ]);


        expect(
          onInterimTranscript,
        ).toHaveBeenCalledWith(
          "what is",
        );


        expect(
          onFinalTranscript,
        ).toHaveBeenCalledWith(
          "hemoglobin A1c",
        );
      },
    );


    it(
      "ignores empty transcripts",
      () => {
        const onFinalTranscript =
          vi.fn();


        createSpeechRecognition({
          onFinalTranscript,
        });


        const recognition =
          MockSpeechRecognition
            .instances[0];


        recognition.emitResults([
          {
            isFinal: true,
            0: {
              transcript: "   ",
            },
            length: 1,
          },
        ]);


        expect(
          onFinalTranscript,
        ).not.toHaveBeenCalled();
      },
    );


    it(
      "maps permission denial errors",
      () => {
        const onError =
          vi.fn();


        createSpeechRecognition({
          onError,
        });


        const recognition =
          MockSpeechRecognition
            .instances[0];


        recognition.emitError(
          "not-allowed",
        );


        expect(
          onError,
        ).toHaveBeenCalledWith({
          code:
            "not-allowed",

          message:
            (
              "Microphone access was "
              + "denied. Allow microphone "
              + "access in your browser "
              + "settings and try again."
            ),
        });
      },
    );


    it(
      "maps no-speech errors",
      () => {
        expect(
          voiceErrorMessage(
            "no-speech",
          ),
        ).toBe(
          (
            "No speech was detected. "
            + "Try speaking again."
          ),
        );
      },
    );


    it(
      "forwards stop and abort",
      () => {
        const controller =
          createSpeechRecognition({})!;

        const recognition =
          MockSpeechRecognition
            .instances[0];


        controller.stop();

        controller.abort();


        expect(
          recognition.stop,
        ).toHaveBeenCalledTimes(
          1,
        );

        expect(
          recognition.abort,
        ).toHaveBeenCalledTimes(
          1,
        );
      },
    );
  },
);