import { describe, expect, it } from "vitest";

import { componentSecurityDomain } from "./componentSecurity";

describe("componentSecurityDomain", () => {
  it("should have correct domain id", () => {
    expect(componentSecurityDomain.id).toBe("component-security");
  });

  it("should have correct domain metadata", () => {
    expect(componentSecurityDomain.title).toBe("Component Security");
    expect(componentSecurityDomain.description).toBeDefined();
  });

  it("should have exactly 7 operations", () => {
    expect(componentSecurityDomain.operations.length).toBe(7);
  });

  it("should have all required operation fields", () => {
    componentSecurityDomain.operations.forEach((op) => {
      expect(op.id).toBeDefined();
      expect(op.title).toBeDefined();
      expect(op.description).toBeDefined();
      expect(op.method).toMatch(/^(GET|POST|DELETE)$/);
      expect(op.path).toMatch(/^\/v1\/component-security/);
    });
  });

  it("should have unique operation ids", () => {
    const ids = componentSecurityDomain.operations.map((op) => op.id);
    const uniqueIds = new Set(ids);
    expect(uniqueIds.size).toBe(ids.length);
  });

  it("should map to correct backend routes", () => {
    const operations = componentSecurityDomain.operations;

    // Create Run
    const createRun = operations.find((op) => op.id === "sec-create-run");
    expect(createRun?.method).toBe("POST");
    expect(createRun?.path).toBe("/v1/component-security/runs");

    // List Runs
    const listRuns = operations.find((op) => op.id === "sec-list-runs");
    expect(listRuns?.method).toBe("GET");
    expect(listRuns?.path).toBe("/v1/component-security/runs");

    // Get Run
    const getRun = operations.find((op) => op.id === "sec-get-run");
    expect(getRun?.method).toBe("GET");
    expect(getRun?.path).toBe("/v1/component-security/runs/{run_id}");

    // Get Findings
    const getFindings = operations.find((op) => op.id === "sec-get-findings");
    expect(getFindings?.method).toBe("GET");
    expect(getFindings?.path).toBe("/v1/component-security/runs/{run_id}/findings");

    // Cancel Run
    const cancelRun = operations.find((op) => op.id === "sec-cancel-run");
    expect(cancelRun?.method).toBe("POST");
    expect(cancelRun?.path).toBe("/v1/component-security/runs/{run_id}/cancel");

    // Delete Run
    const deleteRun = operations.find((op) => op.id === "sec-delete-run");
    expect(deleteRun?.method).toBe("DELETE");
    expect(deleteRun?.path).toBe("/v1/component-security/runs/{run_id}");

    // Get Status
    const getStatus = operations.find((op) => op.id === "sec-run-status");
    expect(getStatus?.method).toBe("GET");
    expect(getStatus?.path).toBe("/v1/component-security/runs/{run_id}/status");
  });

  it("should have valid default values for create run", () => {
    const createRun = componentSecurityDomain.operations.find((op) => op.id === "sec-create-run");
    expect(createRun?.defaultBody).toBeDefined();

    if (createRun?.defaultBody) {
      const body = JSON.parse(createRun.defaultBody);
      expect(body.target).toBeDefined();
      expect(body.target.repository_path).toBeDefined();
      expect(body.profile).toMatch(/^(quick|standard|deep)$/);
      expect(body.options).toBeDefined();
    }
  });

  it("should have path params for operations requiring run_id", () => {
    const opsWithRunId = ["sec-get-run", "sec-get-findings", "sec-cancel-run", "sec-delete-run", "sec-run-status"];

    opsWithRunId.forEach((opId) => {
      const op = componentSecurityDomain.operations.find((o) => o.id === opId);
      expect(op?.defaultPathParams).toBeDefined();
      expect(op?.defaultPathParams?.run_id).toBe("replace-with-run-id");
    });
  });
});
