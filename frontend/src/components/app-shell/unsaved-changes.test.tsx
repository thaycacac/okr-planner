import "@testing-library/jest-dom/vitest";

import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { useState } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import vi_messages from "../../../messages/vi.json";

import { UnsavedChangesProvider, useLeaveGuard, useUnsavedChanges } from "./unsaved-changes";

vi.mock("next/navigation", () => ({ useRouter: () => ({ push: vi.fn() }) }));

function DirtyForm() {
  const [count, setCount] = useState(0);
  useUnsavedChanges(count);
  return (
    <button type="button" onClick={() => setCount((c) => c + 1)}>
      edit
    </button>
  );
}

function LeaveButton({ onLeave }: { onLeave: () => void }) {
  const { confirmLeave } = useLeaveGuard();
  return (
    <button type="button" onClick={() => confirmLeave(onLeave)}>
      leave
    </button>
  );
}

function renderGuard(onLeave: () => void) {
  return render(
    <NextIntlClientProvider locale="vi" messages={vi_messages}>
      <UnsavedChangesProvider>
        <DirtyForm />
        <LeaveButton onLeave={onLeave} />
      </UnsavedChangesProvider>
    </NextIntlClientProvider>,
  );
}

describe("UnsavedChangesProvider", () => {
  afterEach(cleanup);

  it("leaves straight away when nothing is unsaved", () => {
    const onLeave = vi.fn();
    renderGuard(onLeave);
    fireEvent.click(screen.getByText("leave"));
    expect(onLeave).toHaveBeenCalledOnce();
    expect(screen.queryByRole("alertdialog")).not.toBeInTheDocument();
  });

  it("asks first, keeps the user on Stay, and leaves on Discard", () => {
    const onLeave = vi.fn();
    renderGuard(onLeave);
    fireEvent.click(screen.getByText("edit"));
    fireEvent.click(screen.getByText("edit"));
    fireEvent.click(screen.getByText("leave"));

    const dialog = screen.getByRole("alertdialog");
    expect(dialog).toHaveTextContent("Bỏ 2 thay đổi chưa lưu?");
    expect(screen.getByRole("button", { name: "Ở lại" })).toHaveFocus();

    fireEvent.click(screen.getByRole("button", { name: "Ở lại" }));
    expect(onLeave).not.toHaveBeenCalled();

    fireEvent.click(screen.getByText("leave"));
    fireEvent.click(screen.getByRole("button", { name: "Bỏ thay đổi" }));
    expect(onLeave).toHaveBeenCalledOnce();
  });

  it("blocks unloading the page only while changes are unsaved", () => {
    renderGuard(() => {});
    const clean = new Event("beforeunload", { cancelable: true });
    window.dispatchEvent(clean);
    expect(clean.defaultPrevented).toBe(false);

    fireEvent.click(screen.getByText("edit"));
    const dirty = new Event("beforeunload", { cancelable: true });
    window.dispatchEvent(dirty);
    expect(dirty.defaultPrevented).toBe(true);
  });
});
