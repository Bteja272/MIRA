import {
  cleanup,
} from "@testing-library/react";
import "@testing-library/jest-dom/vitest";
import {
  afterEach,
  beforeAll,
  beforeEach,
  vi,
} from "vitest";

beforeAll(() => {
  HTMLDialogElement.prototype.showModal =
    function showModal(): void {
      this.setAttribute("open", "");
    };

  HTMLDialogElement.prototype.close =
    function close(): void {
      this.removeAttribute("open");
    };
});

beforeEach(() => {
  sessionStorage.clear();
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});