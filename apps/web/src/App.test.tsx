import { describe, expect, it } from "vitest";
import App from "./App";

describe("PolyNexus web scaffold", () => {
  it("exports the root App component", () => {
    expect(typeof App).toBe("function");
  });
});
