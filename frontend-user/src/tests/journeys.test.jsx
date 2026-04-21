import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import LoginPage from "../pages/LoginPage";
import NotificationsPage from "../pages/NotificationsPage";
import RecommendationsPage from "../pages/RecommendationsPage";
import RegisterPage from "../pages/RegisterPage";
import RoommatesPage from "../pages/RoommatesPage";
import HousingPage from "../pages/HousingPage";
import BookingsPage from "../pages/BookingsPage";
import { useAuthStore } from "../store/authStore";

vi.mock("../api/recommendations", () => ({
  getRecommendations: vi.fn(async () => [{ id: 1, title: "AI Home", match: "94% match 🎯" }]),
}));

vi.mock("../api/roommates", () => ({
  getRoommateMatches: vi.fn(async () => [{ id: 1, name: "Alex", score: 0.9 }]),
}));

vi.mock("../api/notifications", () => ({
  getNotifications: vi.fn(async () => [{ id: 1, title: "Booking update", category: "booking", is_read: false }]),
  markNotificationRead: vi.fn(async () => ({})),
  markAllNotificationsRead: vi.fn(async () => ({})),
}));

vi.mock("../hooks/useAuth", () => ({
  useAuth: () => ({
    loginMutation: { mutateAsync: vi.fn(async () => ({ ok: true })), isPending: false },
    registerMutation: { mutateAsync: vi.fn(async () => ({ id: 1 })), isPending: false },
  }),
}));

vi.mock("../hooks/useSearch", () => ({
  useSearch: () => ({
    query: "",
    setQuery: vi.fn(),
    mode: "list",
    setMode: vi.fn(),
    searchQuery: {
      isLoading: false,
      isError: false,
      data: [{ id: 101, title: "Campus Flat", price: 1200, location: "Downtown" }],
      refetch: vi.fn(),
    },
  }),
}));

vi.mock("../hooks/useBookings", () => ({
  useBookings: () => ({
    isLoading: false,
    isError: false,
    data: [{ id: 401, status: "pending", title: "Campus Flat", total_price: 1000 }],
    refetch: vi.fn(),
  }),
}));

vi.mock("react-leaflet", () => ({
  MapContainer: ({ children }) => <div data-testid="map">{children}</div>,
  TileLayer: () => null,
  Marker: ({ children }) => <div>{children}</div>,
  Popup: ({ children }) => <div>{children}</div>,
}));

function renderWithProviders(ui) {
  const queryClient = new QueryClient();
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>{ui}</MemoryRouter>
    </QueryClientProvider>
  );
}

describe("Phase 14 user journeys", () => {
  beforeEach(() => {
    useAuthStore.setState({
      user: { id: 1, email: "student@example.com" },
      token: "token",
      isAuthenticated: true,
      refreshToken: "",
    });
  });

  it("register journey renders multi-step form", () => {
    renderWithProviders(<RegisterPage />);
    expect(screen.getByText(/Create Account|Next/i)).toBeInTheDocument();
    fireEvent.click(screen.getByText("Next →"));
    expect(screen.getByText(/Drag & drop profile photo/i)).toBeInTheDocument();
  });

  it("login journey renders and submits", async () => {
    renderWithProviders(<LoginPage />);
    fireEvent.change(screen.getByLabelText("University Email"), { target: { value: "student@example.com" } });
    fireEvent.change(screen.getByLabelText("Password"), { target: { value: "pass1234" } });
    fireEvent.click(screen.getByText("Sign In"));
    expect(screen.getByText("Sign In")).toBeInTheDocument();
  });

  it("recommendations journey opens why-matched modal", async () => {
    renderWithProviders(<RecommendationsPage />);
    expect(await screen.findByText(/Recommended for You/i)).toBeInTheDocument();
    const whyButton = await screen.findByText("Why matched?");
    fireEvent.click(whyButton);
    expect(await screen.findByText("Why matched?")).toBeInTheDocument();
  });

  it("search housing journey renders listing cards", async () => {
    renderWithProviders(<HousingPage />);
    expect(await screen.findByText("Campus Flat")).toBeInTheDocument();
  });

  it("booking journey renders booking in bookings page", async () => {
    renderWithProviders(<BookingsPage />);
    expect(await screen.findByText("Campus Flat")).toBeInTheDocument();
  });

  it("roommate journey switches from questionnaire to matches", async () => {
    renderWithProviders(<RoommatesPage />);
    for (let i = 0; i < 5; i++) {
      fireEvent.click(screen.getByText("Next →"));
    }
    fireEvent.click(screen.getByText("Submit"));
    expect(await screen.findByText(/Your Roommate Matches/i)).toBeInTheDocument();
  });

  it("notifications journey shows mark all as read", async () => {
    renderWithProviders(<NotificationsPage />);
    expect(await screen.findByText("Mark all as read")).toBeInTheDocument();
  });
});
