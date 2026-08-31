import {
  act,
  renderHook,
} from "@testing-library/react";
import {
  afterEach,
  beforeEach,
  describe,
  expect,
  it,
  vi,
} from "vitest";

import {
  useSpeechSynthesis,
} from "./useSpeechSynthesis";


class MockUtterance {
  text: string;

  lang = "";
  rate = 1;
  pitch = 1;
  volume = 1;

  onstart:
    | (() => void)
    | null = null;

  onend:
    | (() => void)
    | null = null;

  onerror:
    | (() => void)
    | null = null;


  constructor(
    text: string,
  ) {
    this.text = text;
  }
}


const speakMock =
  vi.fn();

const cancelMock =
  vi.fn();

const pauseMock =
  vi.fn();

const resumeMock =
  vi.fn();


function installSpeechMock(): void {
  Object.defineProperty(
    window,
    "speechSynthesis",
    {
      configurable: true,
      value: {
        speak: speakMock,
        cancel: cancelMock,
        pause: pauseMock,
        resume: resumeMock,
      },
    },
  );

  Object.defineProperty(
    globalThis,
    "SpeechSynthesisUtterance",
    {
      configurable: true,
      value: MockUtterance,
    },
  );
}


beforeEach(() => {
  vi.clearAllMocks();
  installSpeechMock();
});


afterEach(() => {
  Reflect.deleteProperty(
    window,
    "speechSynthesis",
  );

  Reflect.deleteProperty(
    globalThis,
    "SpeechSynthesisUtterance",
  );
});


describe(
  "useSpeechSynthesis",
  () => {
    it(
      "speaks one assistant message",
      () => {
        const { result } =
          renderHook(
            () => useSpeechSynthesis(),
          );

        act(() => {
          result.current.speak(
            "message-1",
            "Final assistant answer.",
          );
        });

        expect(
          cancelMock,
        ).toHaveBeenCalledTimes(
          1,
        );

        expect(
          speakMock,
        ).toHaveBeenCalledTimes(
          1,
        );

        const utterance =
          speakMock.mock.calls[0][0] as MockUtterance;

        expect(
          utterance.text,
        ).toBe(
          "Final assistant answer.",
        );

        expect(
          result.current.activeMessageId,
        ).toBe(
          "message-1",
        );

        expect(
          result.current.state,
        ).toBe(
          "speaking",
        );
      },
    );


    it(
      "pauses and resumes active playback",
      () => {
        const { result } =
          renderHook(
            () => useSpeechSynthesis(),
          );

        act(() => {
          result.current.speak(
            "message-1",
            "Answer",
          );
        });

        act(() => {
          result.current.pause();
        });

        expect(
          pauseMock,
        ).toHaveBeenCalledTimes(
          1,
        );

        expect(
          result.current.state,
        ).toBe(
          "paused",
        );

        act(() => {
          result.current.resume();
        });

        expect(
          resumeMock,
        ).toHaveBeenCalledTimes(
          1,
        );

        expect(
          result.current.state,
        ).toBe(
          "speaking",
        );
      },
    );


    it(
      "stops playback and clears the active message",
      () => {
        const { result } =
          renderHook(
            () => useSpeechSynthesis(),
          );

        act(() => {
          result.current.speak(
            "message-1",
            "Answer",
          );
        });

        act(() => {
          result.current.stop();
        });

        expect(
          cancelMock,
        ).toHaveBeenCalledTimes(
          2,
        );

        expect(
          result.current.activeMessageId,
        ).toBeNull();

        expect(
          result.current.state,
        ).toBe(
          "idle",
        );
      },
    );


    it(
      "returns to idle when playback ends",
      () => {
        const { result } =
          renderHook(
            () => useSpeechSynthesis(),
          );

        act(() => {
          result.current.speak(
            "message-1",
            "Answer",
          );
        });

        const utterance =
          speakMock.mock.calls[0][0] as MockUtterance;

        act(() => {
          utterance.onend?.();
        });

        expect(
          result.current.activeMessageId,
        ).toBeNull();

        expect(
          result.current.lastSpokenMessageId,
        ).toBe(
          "message-1",
        );

        expect(
          result.current.state,
        ).toBe(
          "idle",
        );
      },
    );


    it(
      "cancels playback when the hook unmounts",
      () => {
        const { result, unmount } =
          renderHook(
            () => useSpeechSynthesis(),
          );

        act(() => {
          result.current.speak(
            "message-1",
            "Answer",
          );
        });

        cancelMock.mockClear();

        unmount();

        expect(
          cancelMock,
        ).toHaveBeenCalledTimes(
          1,
        );
      },
    );
  },
);
