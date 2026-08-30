import {
  fireEvent,
  render,
  screen,
} from "@testing-library/react";

import {
  beforeEach,
  describe,
  expect,
  it,
  vi,
} from "vitest";

import {
  useSpeechRecognition,
} from "../hooks/useSpeechRecognition";

import {
  VoiceInputButton,
} from "../components/VoiceInputButton";


vi.mock(
  "../hooks/useSpeechRecognition",
  () => ({
    useSpeechRecognition:
      vi.fn(),
  }),
);


const mockedUseSpeechRecognition =
  vi.mocked(
    useSpeechRecognition,
  );


describe(
  "VoiceInputButton",
  () => {
    const start =
      vi.fn();

    const stop =
      vi.fn();

    const abort =
      vi.fn();


    beforeEach(() => {
      vi.clearAllMocks();


      mockedUseSpeechRecognition
        .mockReturnValue({
          supported: true,

          state:
            "idle",

          isListening:
            false,

          interimTranscript:
            "",

          error:
            null,

          start,

          stop,

          abort,
        });
    });


    it(
      "starts voice recognition",
      () => {
        render(
          <VoiceInputButton
            onTranscript={
              vi.fn()
            }
          />,
        );


        fireEvent.click(
          screen.getByRole(
            "button",
            {
              name:
                "Voice input",
            },
          ),
        );


        expect(
          start,
        ).toHaveBeenCalledTimes(
          1,
        );
      },
    );


    it(
      (
        "renders a disabled control "
        + "when unsupported"
      ),
      () => {
        mockedUseSpeechRecognition
          .mockReturnValue({
            supported: false,

            state:
              "unsupported",

            isListening:
              false,

            interimTranscript:
              "",

            error:
              null,

            start,

            stop,

            abort,
          });


        render(
          <VoiceInputButton
            onTranscript={
              vi.fn()
            }
          />,
        );


        expect(
          screen.getByRole(
            "button",
            {
              name:
                "Voice unavailable",
            },
          ),
        ).toBeDisabled();
      },
    );


    it(
      (
        "shows interim text while "
        + "listening"
      ),
      () => {
        mockedUseSpeechRecognition
          .mockReturnValue({
            supported: true,

            state:
              "listening",

            isListening:
              true,

            interimTranscript:
              "what is hemoglobin",

            error:
              null,

            start,

            stop,

            abort,
          });


        render(
          <VoiceInputButton
            onTranscript={
              vi.fn()
            }
          />,
        );


        expect(
          screen.getByText(
            (
              "Listening: "
              + "what is hemoglobin"
            ),
          ),
        ).toBeInTheDocument();
      },
    );


    it(
      (
        "stops an active recognition "
        + "session"
      ),
      () => {
        mockedUseSpeechRecognition
          .mockReturnValue({
            supported: true,

            state:
              "listening",

            isListening:
              true,

            interimTranscript:
              "",

            error:
              null,

            start,

            stop,

            abort,
          });


        render(
          <VoiceInputButton
            onTranscript={
              vi.fn()
            }
          />,
        );


        fireEvent.click(
          screen.getByRole(
            "button",
            {
              name:
                "Stop listening",
            },
          ),
        );


        expect(
          stop,
        ).toHaveBeenCalledTimes(
          1,
        );
      },
    );


    it(
      "renders recognition errors",
      () => {
        mockedUseSpeechRecognition
          .mockReturnValue({
            supported: true,

            state:
              "error",

            isListening:
              false,

            interimTranscript:
              "",

            error: {
              code:
                "not-allowed",

              message:
                (
                  "Microphone access "
                  + "was denied."
                ),
            },

            start,

            stop,

            abort,
          });


        render(
          <VoiceInputButton
            onTranscript={
              vi.fn()
            }
          />,
        );


        expect(
          screen.getByRole(
            "alert",
          ),
        ).toHaveTextContent(
          (
            "Microphone access "
            + "was denied."
          ),
        );
      },
    );
  },
);