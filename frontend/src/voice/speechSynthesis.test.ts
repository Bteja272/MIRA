import {
  afterEach,
  describe,
  expect,
  it,
  vi,
} from "vitest";

import {
  createSpeechUtterance,
  isSpeechSynthesisSupported,
  prepareTextForSpeech,
} from "./speechSynthesis";


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


function installSpeechMock(): void {
  Object.defineProperty(
    window,
    "speechSynthesis",
    {
      configurable: true,
      value: {
        speak: vi.fn(),
        cancel: vi.fn(),
        pause: vi.fn(),
        resume: vi.fn(),
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
  "speechSynthesis",
  () => {
    it(
      "detects supported browsers",
      () => {
        installSpeechMock();

        expect(
          isSpeechSynthesisSupported(),
        ).toBe(
          true,
        );
      },
    );


    it(
      "returns null when unsupported",
      () => {
        expect(
          isSpeechSynthesisSupported(),
        ).toBe(
          false,
        );

        expect(
          createSpeechUtterance(
            "Hello",
          ),
        ).toBeNull();
      },
    );


    it(
      "creates an utterance from trimmed text",
      () => {
        installSpeechMock();

        const utterance =
          createSpeechUtterance(
            "  MIRA response  ",
          );

        expect(
          utterance,
        ).not.toBeNull();

        expect(
          utterance?.text,
        ).toBe(
          "MIRA response",
        );

        expect(
          utterance?.rate,
        ).toBe(
          1,
        );

        expect(
          utterance?.pitch,
        ).toBe(
          1,
        );

        expect(
          utterance?.volume,
        ).toBe(
          1,
        );
      },
    );

    it(
  "removes source markers from spoken text",
  () => {
    expect(
      prepareTextForSpeech(
        (
          "Your A1c is 5.7%. "
          + "[Source 1]"
        ),
      ),
    ).toBe(
      "Your A1c is 5.7%.",
    );
  },
);


it(
  "removes markdown emphasis markers",
  () => {
    expect(
      prepareTextForSpeech(
        (
          "**Hemoglobin A1c** "
          + "is a blood test."
        ),
      ),
    ).toBe(
      (
        "Hemoglobin A1c "
        + "is a blood test."
        ),
        );
    },
    );


    it(
    (
        "removes source markers and "
        + "markdown together"
    ),
    () => {
        expect(
        prepareTextForSpeech(
            (
            "**Lisinopril** is listed "
            + "as 10 mg daily. "
            + "[Source 1]"
            ),
        ),
        ).toBe(
        (
            "Lisinopril is listed "
            + "as 10 mg daily."
        ),
        );
    },
    );


    it(
      "does not create an empty utterance",
      () => {
        installSpeechMock();

        expect(
          createSpeechUtterance(
            "   ",
          ),
        ).toBeNull();
      },
    );
  },
);
