import type {
  ComponentProps,
} from "react";

import {
  render,
  screen,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import {
  describe,
  expect,
  it,
  vi,
} from "vitest";

import {
  AssistantSpeechControls,
} from "./AssistantSpeechControls";


function renderControls(
  overrides: Partial<
    ComponentProps<
      typeof AssistantSpeechControls
    >
  > = {},
) {
  const props:
    ComponentProps<
      typeof AssistantSpeechControls
    > = {
      messageId: "message-1",
      text: "Final answer only.",
      supported: true,
      state: "idle",
      activeMessageId: null,
      lastSpokenMessageId: null,
      error: null,
      onListen: vi.fn(),
      onPause: vi.fn(),
      onResume: vi.fn(),
      onStop: vi.fn(),
      onReplay: vi.fn(),
      ...overrides,
    };

  render(
    <AssistantSpeechControls
      {...props}
    />,
  );

  return props;
}


describe(
  "AssistantSpeechControls",
  () => {
    it(
      "starts playback with the assistant answer",
      async () => {
        const user =
          userEvent.setup();

        const props =
          renderControls();

        await user.click(
          screen.getByRole(
            "button",
            {
              name: "Listen",
            },
          ),
        );

        expect(
          props.onListen,
        ).toHaveBeenCalledWith(
          "message-1",
          "Final answer only.",
        );
      },
    );


    it(
      "shows pause and stop while speaking",
      () => {
        renderControls({
          state: "speaking",
          activeMessageId:
            "message-1",
        });

        expect(
          screen.getByRole(
            "button",
            {
              name: "Pause",
            },
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByRole(
            "button",
            {
              name: "Stop",
            },
          ),
        ).toBeInTheDocument();
      },
    );


    it(
      "shows resume and replay while paused",
      () => {
        renderControls({
          state: "paused",
          activeMessageId:
            "message-1",
          lastSpokenMessageId:
            "message-1",
        });

        expect(
          screen.getByRole(
            "button",
            {
              name: "Resume",
            },
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByRole(
            "button",
            {
              name: "Replay",
            },
          ),
        ).toBeInTheDocument();
      },
    );


    it(
      "uses Replay after the message has finished",
      () => {
        renderControls({
          lastSpokenMessageId:
            "message-1",
        });

        expect(
          screen.getByRole(
            "button",
            {
              name: "Replay",
            },
          ),
        ).toBeInTheDocument();
      },
    );


    it(
      "renders an unavailable control when unsupported",
      () => {
        renderControls({
          supported: false,
          state: "unsupported",
        });

        expect(
          screen.getByRole(
            "button",
            {
              name:
                "Listen unavailable",
            },
          ),
        ).toBeDisabled();
      },
    );
  },
);
