import { describe, expect, it } from "vitest";

import { SecurityDashboard } from "./SecurityDashboard";
import { ScanRunCard } from "./ScanRunCard";
import { FindingsTable } from "./FindingsTable";

describe("SecurityDashboard module", () => {
  it("exports SecurityDashboard as a function component", () => {
    expect(typeof SecurityDashboard).toBe("function");
  });

  it("exports ScanRunCard as a function component", () => {
    expect(typeof ScanRunCard).toBe("function");
  });

  it("exports FindingsTable as a function component", () => {
    expect(typeof FindingsTable).toBe("function");
  });

  it("SecurityDashboard accepts token prop signature", () => {
    // Verify the function has the expected arity (1 props argument)
    expect(SecurityDashboard.length).toBe(1);
  });

  it("ScanRunCard accepts props signature", () => {
    expect(ScanRunCard.length).toBe(1);
  });

  it("FindingsTable accepts props signature", () => {
    expect(FindingsTable.length).toBe(1);
  });
});
