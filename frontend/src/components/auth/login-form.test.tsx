import "@testing-library/jest-dom/vitest";

import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import vi_messages from "../../../messages/vi.json";
import { resetMockState } from "@/lib/api/mock";
import { MOCK_PASSWORD } from "@/lib/api/mock-config";

import { formatCountdown, LoginForm } from "./login-form";

const replace = vi.fn();
vi.mock("next/navigation", () => ({ useRouter: () => ({ replace }) }));

const backend = vi.hoisted(() => ({ rejectCrossSite: false }));

vi.mock("@/lib/api/client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api/client")>();
  const { handleMockRequest } = await import("@/lib/api/mock");
  return {
    ...actual,
    apiMockEnabled: false,
    api: actual.createApiClient({
      baseUrl: "http://api.test",
      fetch: async (request) =>
        backend.rejectCrossSite
          ? Response.json(
              { detail: { code: "cross_site_request", message: "Cross-site request rejected" } },
              { status: 403 },
            )
          : handleMockRequest(request),
      onUnauthorized: () => {},
    }),
  };
});

function renderForm(props: { next?: string; expired?: boolean } = {}) {
  return render(
    <NextIntlClientProvider locale="vi" messages={vi_messages}>
      <LoginForm next={props.next ?? "/"} expired={props.expired ?? false} />
    </NextIntlClientProvider>,
  );
}

describe("LoginForm", () => {
  beforeEach(() => {
    resetMockState();
    replace.mockReset();
    backend.rejectCrossSite = false;
  });
  afterEach(cleanup);

  it("asks for a password before calling the API", async () => {
    renderForm();
    fireEvent.click(screen.getByRole("button", { name: "Vào ứng dụng" }));
    expect(await screen.findByText("Nhập mật khẩu để tiếp tục.")).toBeInTheDocument();
    expect(screen.getByLabelText("Mật khẩu")).toHaveAttribute("aria-invalid", "true");
  });

  it("shows remaining attempts on a wrong password", async () => {
    renderForm();
    fireEvent.change(screen.getByLabelText("Mật khẩu"), { target: { value: "wrong" } });
    fireEvent.click(screen.getByRole("button", { name: "Vào ứng dụng" }));
    expect(
      await screen.findByText("Mật khẩu không đúng. Còn 4 lần thử trước khi tạm khóa."),
    ).toBeInTheDocument();
    expect(replace).not.toHaveBeenCalled();
  });

  it("goes to the requested page after signing in", async () => {
    renderForm({ next: "/settings/ai" });
    fireEvent.change(screen.getByLabelText("Mật khẩu"), { target: { value: MOCK_PASSWORD } });
    fireEvent.click(screen.getByRole("button", { name: "Vào ứng dụng" }));
    await waitFor(() => expect(replace).toHaveBeenCalledWith("/settings/ai"));
  });

  it("toggles password visibility", () => {
    renderForm();
    const input = screen.getByLabelText("Mật khẩu");
    const toggle = screen.getByRole("button", { name: "Hiện mật khẩu" });
    expect(input).toHaveAttribute("type", "password");
    fireEvent.click(toggle);
    expect(input).toHaveAttribute("type", "text");
    expect(toggle).toHaveAttribute("aria-pressed", "true");
  });

  it("announces a lock once, counts down from the full duration and refocuses when it ends", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    try {
      renderForm();
      const input = screen.getByLabelText("Mật khẩu");
      const submit = screen.getByRole("button", { name: "Vào ứng dụng" });
      act(() => vi.advanceTimersByTime(5_000));
      for (let i = 0; i < 6 && !screen.queryByText("Tạm khóa đăng nhập"); i++) {
        fireEvent.change(input, { target: { value: "wrong" } });
        fireEvent.click(submit);
        await waitFor(() => expect(submit).not.toHaveTextContent("Đang kiểm tra…"));
      }

      expect(screen.getByText("Thử lại sau 1:00.")).toBeInTheDocument();
      expect(screen.getByRole("status")).toHaveTextContent(
        "Tạm khóa đăng nhập. Thử lại sau 60 giây.",
      );
      expect(input).toBeDisabled();

      act(() => vi.advanceTimersByTime(61_000));

      expect(screen.getByRole("status")).toHaveTextContent("Đã hết thời gian khóa");
      expect(input).toBeEnabled();
      expect(input).toHaveFocus();
    } finally {
      vi.useRealTimers();
    }
  });

  it("explains a cross-site rejection instead of blaming the network", async () => {
    backend.rejectCrossSite = true;
    renderForm();
    fireEvent.change(screen.getByLabelText("Mật khẩu"), { target: { value: MOCK_PASSWORD } });
    fireEvent.click(screen.getByRole("button", { name: "Vào ứng dụng" }));
    expect(await screen.findByText(/không đến từ đúng địa chỉ của ứng dụng/)).toBeInTheDocument();
    expect(screen.queryByText(/Không kết nối được máy chủ/)).not.toBeInTheDocument();
    expect(replace).not.toHaveBeenCalled();
  });

  it("explains an expired session", () => {
    renderForm({ expired: true });
    expect(screen.getByText(/Phiên đã hết hạn/)).toBeInTheDocument();
  });
});

describe("formatCountdown", () => {
  it("formats m:ss", () => {
    expect(formatCountdown(48)).toBe("0:48");
    expect(formatCountdown(60)).toBe("1:00");
    expect(formatCountdown(-3)).toBe("0:00");
  });
});
