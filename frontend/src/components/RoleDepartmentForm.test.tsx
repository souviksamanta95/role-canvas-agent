import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { departments, newUser } from "../test/fixtures";
import { RoleDepartmentForm } from "./RoleDepartmentForm";

function setup(onSubmit = vi.fn().mockResolvedValue(undefined)) {
  render(<RoleDepartmentForm departments={departments} user={newUser} submitLabel="Continue" onSubmit={onSubmit} />);
  return { onSubmit, user: userEvent.setup() };
}

describe("RoleDepartmentForm", () => {
  it("disables the role list until a department is chosen", () => {
    setup();
    expect(screen.getByLabelText("Role")).toBeDisabled();
    expect(screen.getByRole("button", { name: "Continue" })).toBeDisabled();
  });

  it("lists only the roles that belong to the chosen department", async () => {
    const { user } = setup();
    await user.selectOptions(screen.getByLabelText("Department"), "finance");
    const options = screen.getAllByRole("option").map((o) => o.textContent);
    expect(options).toContain("Finance Analyst");
    expect(options).toContain("Controller");
    expect(options).not.toContain("Marketing Analyst");
  });

  it("clears the role when the department changes", async () => {
    const { user } = setup();
    await user.selectOptions(screen.getByLabelText("Department"), "finance");
    await user.selectOptions(screen.getByLabelText("Role"), "controller");
    await user.selectOptions(screen.getByLabelText("Department"), "marketing");
    expect(screen.getByLabelText("Role")).toHaveValue("");
    expect(screen.getByRole("button", { name: "Continue" })).toBeDisabled();
  });

  it("submits department, role and region", async () => {
    const { user, onSubmit } = setup();
    await user.selectOptions(screen.getByLabelText("Department"), "finance");
    await user.selectOptions(screen.getByLabelText("Role"), "finance-analyst");
    await user.type(screen.getByLabelText(/Region/), " EMEA ");
    await user.click(screen.getByRole("button", { name: "Continue" }));
    expect(onSubmit).toHaveBeenCalledWith({ department: "finance", role: "finance-analyst", region: "EMEA" });
  });

  it("shows the server's message when saving fails", async () => {
    const { user } = setup(vi.fn().mockRejectedValue(new Error("Unknown role for this department.")));
    await user.selectOptions(screen.getByLabelText("Department"), "finance");
    await user.selectOptions(screen.getByLabelText("Role"), "controller");
    await user.click(screen.getByRole("button", { name: "Continue" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Unknown role for this department.");
  });
});
