import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ProtectedAdminRoute } from "../components/layout/ProtectedAdminRoute";
import AdminBookingsPage from "../pages/admin/AdminBookingsPage";
import AdminHousingDetailPage from "../pages/admin/AdminHousingDetailPage";
import AdminHousingPage from "../pages/admin/AdminHousingPage";
import AdminLoginPage from "../pages/admin/AdminLoginPage";
import AdminNotificationsPage from "../pages/admin/AdminNotificationsPage";
import AdminReportsPage from "../pages/admin/AdminReportsPage";
import { useAdminAuthStore } from "../store/adminAuthStore";

const mockNavigate = vi.fn();
const mutateLogin = vi.fn();
const getPendingHousing = vi.fn();
const updateHousingApproval = vi.fn();
const getAdminBookings = vi.fn();
const overrideBookingStatus = vi.fn();
const sendBroadcast = vi.fn();
const getReportKPIs = vi.fn();
const exportMutateAsync = vi.fn();

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

vi.mock("../hooks/useAdminAuth", () => ({
  useAdminAuth: () => ({
    loginMutation: {
      mutateAsync: mutateLogin,
      isPending: false,
    },
  }),
}));

vi.mock("../api/admin/housing", () => ({
  getPendingHousing: (...args) => getPendingHousing(...args),
  updateHousingApproval: (...args) => updateHousingApproval(...args),
}));

vi.mock("../api/admin/bookings", () => ({
  getAdminBookings: (...args) => getAdminBookings(...args),
  overrideBookingStatus: (...args) => overrideBookingStatus(...args),
}));

vi.mock("../api/admin/notifications", () => ({
  sendBroadcast: (...args) => sendBroadcast(...args),
}));

vi.mock("../api/admin/reports", () => ({
  getReportKPIs: (...args) => getReportKPIs(...args),
  getDashboardOverview: vi.fn(),
  exportReports: vi.fn(),
}));

vi.mock("../hooks/useExport", () => ({
  useExport: () => ({
    mutateAsync: exportMutateAsync,
    isPending: false,
  }),
}));

function renderWithProviders(ui, { initialEntries = ["/"] } = {}) {
  const client = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={initialEntries}>{ui}</MemoryRouter>
    </QueryClientProvider>
  );
}

describe("Phase 15 admin workflows", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    useAdminAuthStore.getState().logout();
  });

  it("1) admin login redirects to dashboard", async () => {
    mutateLogin.mockResolvedValue({
      user: { id: 1, roles: ["admin"] },
      tokens: { access_token: "token" },
    });
    renderWithProviders(<AdminLoginPage />);

    await userEvent.type(screen.getByLabelText("Email"), "admin@nestu.com");
    await userEvent.type(screen.getByLabelText("Password"), "super-secret");
    await userEvent.click(screen.getByRole("button", { name: /sign in to dashboard/i }));

    await waitFor(() => expect(mutateLogin).toHaveBeenCalled());
    expect(mockNavigate).toHaveBeenCalledWith("/admin/dashboard");
  });

  it("2) unauthenticated admin route access redirects to /admin/login", async () => {
    renderWithProviders(
      <Routes>
        <Route
          path="/admin/dashboard"
          element={
            <ProtectedAdminRoute>
              <div>Dashboard Page</div>
            </ProtectedAdminRoute>
          }
        />
        <Route path="/admin/login" element={<div>Login Page</div>} />
      </Routes>,
      { initialEntries: ["/admin/dashboard"] }
    );

    expect(await screen.findByText("Login Page")).toBeInTheDocument();
    expect(screen.queryByText("Dashboard Page")).not.toBeInTheDocument();
  });

  it("3) approve listing removes item from pending queue", async () => {
    let queue = [
      { id: 1, title: "Blue Apartment", location: "Center", created_at: new Date().toISOString(), moderation_status: "pending" },
      { id: 2, title: "Green Studio", location: "West", created_at: new Date().toISOString(), moderation_status: "pending" },
    ];
    getPendingHousing.mockImplementation(async () => ({ results: queue }));
    updateHousingApproval.mockImplementation(async (id, payload) => {
      if (payload.approval === "approved") {
        queue = queue.filter((item) => item.id !== id);
      }
      return { success: true };
    });

    renderWithProviders(<AdminHousingPage />);
    expect(await screen.findByText("Blue Apartment")).toBeInTheDocument();

    const approveButtons = await screen.findAllByRole("button", { name: /approve/i });
    await userEvent.click(approveButtons[0]);

    await waitFor(() => expect(updateHousingApproval).toHaveBeenCalledWith(1, expect.objectContaining({ approval: "approved" })));
    await waitFor(() => expect(screen.queryByText("Blue Apartment")).not.toBeInTheDocument());
  });

  it("4) reject listing with reason writes an audit entry", async () => {
    let history = [{ id: 1, admin_name: "Ahmed", action: "Submitted for review", reason: "", created_at: new Date().toISOString() }];
    getPendingHousing.mockImplementation(async () => ({
      results: [
        {
          id: 7,
          title: "Pending Flat",
          description: "Needs review",
          moderation_status: "pending",
          history,
        },
      ],
    }));
    updateHousingApproval.mockImplementation(async (_id, payload) => {
      history = [
        ...history,
        {
          id: 2,
          admin_name: "Admin",
          action: "Rejected listing",
          reason: payload.reason,
          created_at: new Date().toISOString(),
        },
      ];
      return { success: true };
    });

    renderWithProviders(
      <Routes>
        <Route path="/admin/housing/:id" element={<AdminHousingDetailPage />} />
      </Routes>,
      { initialEntries: ["/admin/housing/7"] }
    );

    await screen.findByText("Pending Flat");
    await userEvent.type(screen.getByLabelText("Rejection reason"), "Missing safety certification");
    await userEvent.click(screen.getByRole("button", { name: /reject listing/i }));

    await waitFor(() =>
      expect(updateHousingApproval).toHaveBeenCalledWith("7", {
        approval: "rejected",
        reason: "Missing safety certification",
      })
    );
    expect(await screen.findByText("Missing safety certification")).toBeInTheDocument();
  });

  it("5) booking override requires a reason before confirm", async () => {
    getAdminBookings.mockResolvedValue({
      results: [
        {
          id: 11,
          user_name: "Sara T",
          user_email: "sara@test.com",
          unit_name: "Unit 11",
          start_date: "2026-01-10",
          end_date: "2026-01-20",
          total_price: 500,
          status: "pending",
          payment_status: "pending",
        },
      ],
    });
    overrideBookingStatus.mockResolvedValue({ success: true });

    renderWithProviders(<AdminBookingsPage />);
    await screen.findByText("Sara T");
    await userEvent.click(screen.getByRole("button", { name: /override/i }));

    const confirmBtn = screen.getByRole("button", { name: /confirm override/i });
    expect(confirmBtn).toBeDisabled();

    const reasonBox = screen.getByPlaceholderText(/reason for override/i);
    fireEvent.change(reasonBox, { target: { value: "short reason" } });
    expect(confirmBtn).toBeDisabled();

    fireEvent.change(reasonBox, {
      target: { value: "This booking was manually updated after payment provider timeout." },
    });
    expect(confirmBtn).toBeEnabled();

    await userEvent.click(confirmBtn);
    await waitFor(() => expect(overrideBookingStatus).toHaveBeenCalled());
  });

  it("6) broadcast shows confirmation modal and sends to selected audience", async () => {
    sendBroadcast.mockResolvedValue({ success: true });
    renderWithProviders(<AdminNotificationsPage />);

    await userEvent.type(screen.getByPlaceholderText("Enter title"), "System Maintenance");
    await userEvent.type(screen.getByPlaceholderText("Write your message"), "Tonight at 11 PM.");
    await userEvent.selectOptions(screen.getByDisplayValue("All Users"), "students_only");
    await userEvent.click(screen.getByRole("button", { name: /send broadcast/i }));

    expect(await screen.findByText(/you are about to notify 6,020 users/i)).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: /confirm & send/i }));

    await waitFor(() =>
      expect(sendBroadcast).toHaveBeenCalledWith(
        expect.objectContaining({
          audience: "students_only",
          title: "System Maintenance",
        })
      )
    );
  });

  it("7) report export generation exposes download link", async () => {
    getReportKPIs.mockResolvedValue({ kpis: { new_registrations: 10 } });
    exportMutateAsync.mockResolvedValue({ download_url: "https://example.com/report.csv" });

    renderWithProviders(<AdminReportsPage />);
    await screen.findByText("Bookings Over Time");
    await userEvent.click(screen.getByRole("button", { name: /generate export/i }));

    await waitFor(() => expect(exportMutateAsync).toHaveBeenCalled());
    const link = await screen.findByRole("link", { name: /download export/i });
    expect(link).toHaveAttribute("href", "https://example.com/report.csv");
  });
});
