import type { ReactElement } from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter, Outlet, Route, Routes } from "react-router-dom";
import { HomePage } from "../pages/HomePage";
import { WindowsPage } from "../pages/WindowsPage";
import { TargetsPage } from "../pages/TargetsPage";
import { WindowCardView } from "../components/WindowCardView";
import { TargetCardView } from "../components/TargetCardView";
import { SaveLocationPrompt } from "../components/SaveLocationPrompt";
import { ErrorRetry } from "../pages/WindowsPage";
import { loadingPhrase } from "../lib/demo";
import type { TargetCard, WindowCard } from "../api/types";

vi.mock("../api/client", () => ({
  ApiError: class ApiError extends Error {
    status: number;
    constructor(message: string, status: number) {
      super(message);
      this.status = status;
    }
  },
  api: {
    windows: () => new Promise(() => {}),
    targets: () => new Promise(() => {}),
    searchPlaces: () => new Promise(() => {}),
    me: () => Promise.resolve({ user: null }),
    listLocations: () => new Promise(() => {}),
  },
}));

function wrap(ui: ReactElement, path = "/") {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[path]}>
        <Routes>
          <Route element={<Outlet context={{ user: null }} />}>
            <Route path="*" element={ui} />
          </Route>
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

const sampleWindow: WindowCard = {
  start: "2026-01-15T21:30:00+00:00",
  end: "2026-01-16T00:30:00+00:00",
  night_date: "2026-01-15",
  label: "Tonight",
  rating: "Good",
  explanation: "Clear for a couple of hours before cloud moves in.",
  duration_minutes: 180,
};

const sampleTarget: TargetCard = {
  name: "Andromeda Galaxy",
  object_type: "Galaxy",
  rating: "Excellent",
  direction: "Northeast, about halfway up the sky",
  best_portion: "Best around 11pm",
  reason: "A strong target for most of this window.",
  featured: true,
  kind: "dso",
  details: {
    altitude_deg: 48,
    azimuth_deg: 42,
    ra: 10.68,
    dec: 41.27,
    catalogue_ids: ["M31"],
    moon_separation_deg: 70,
    moon_illumination: 0.3,
    rise: null,
    set: null,
    transit: null,
    weather: { cloud_cover: 12 },
  },
};

test("home shows the simple ask and location actions", () => {
  wrap(<HomePage />);
  expect(screen.getByRole("heading", { name: /find your next clear night/i })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /use my location/i })).toBeInTheDocument();
  expect(screen.getByLabelText(/uk place or postcode/i)).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /brighton/i })).toBeInTheDocument();
});

test("window card shows rating text not a percentage", () => {
  wrap(
    <WindowCardView window={sampleWindow} lat={50.8} lon={-0.1} name="Hove" />,
  );
  expect(screen.getByText("Tonight")).toBeInTheDocument();
  expect(screen.getByText("Good")).toBeInTheDocument();
  expect(screen.queryByText(/82%/)).not.toBeInTheDocument();
  expect(screen.getByText(/clear for a couple of hours/i)).toBeInTheDocument();
});

test("target details are collapsed by default", async () => {
  const user = userEvent.setup();
  wrap(<TargetCardView target={sampleTarget} featured />);
  expect(screen.getByText("Andromeda Galaxy")).toBeInTheDocument();
  expect(screen.getByText(/northeast/i)).toBeInTheDocument();
  expect(screen.queryByText(/Altitude/)).not.toBeInTheDocument();
  await user.click(screen.getByRole("button", { name: /details/i }));
  expect(screen.getByText("Altitude")).toBeInTheDocument();
});

test("save prompt appears after forecast value", () => {
  wrap(
    <SaveLocationPrompt name="Hove" lat={50.8} lon={-0.1} />,
    "/windows",
  );
  expect(screen.getByText(/keep an eye on this spot/i)).toBeInTheDocument();
  expect(screen.getByRole("link", { name: /save this location/i })).toBeInTheDocument();
});

test("error state offers retry", async () => {
  const user = userEvent.setup();
  const onRetry = vi.fn();
  wrap(<ErrorRetry message="We couldn't check the clouds just now." onRetry={onRetry} />);
  expect(screen.getByText(/couldn't check the clouds/i)).toBeInTheDocument();
  await user.click(screen.getByRole("button", { name: /try again/i }));
  expect(onRetry).toHaveBeenCalled();
});

test("loadingPhrase rotates through the friendly copy", () => {
  expect(loadingPhrase(0)).toBe("Checking the clouds…");
  expect(loadingPhrase(1)).toBe("Looking for a dark patch…");
  expect(loadingPhrase(3)).toBe("Checking the clouds…");
  expect(loadingPhrase(0, ["Finding a good target…"])).toBe("Finding a good target…");
});

test("windows page shows a skeleton instead of a blank screen", async () => {
  wrap(<WindowsPage />, "/windows?lat=50.8279&lon=-0.1688&name=Hove");
  expect(await screen.findByTestId("windows-skeleton")).toBeInTheDocument();
  expect(screen.getByRole("status")).toHaveTextContent(
    /checking the clouds|looking for a dark patch|seeing what's up/i,
  );
  expect(screen.queryByText(/keep an eye on this spot/i)).not.toBeInTheDocument();
});

test("targets page shows a skeleton while ranking", async () => {
  wrap(
    <TargetsPage />,
    "/targets?lat=50.8279&lon=-0.1688&name=Hove&start=2026-01-15T21:30:00Z&end=2026-01-16T00:30:00Z&label=Tonight",
  );
  expect(await screen.findByTestId("targets-skeleton")).toBeInTheDocument();
  expect(screen.getByRole("status")).toHaveTextContent(
    /seeing what's up|finding a good target|checking what's well placed/i,
  );
  expect(screen.queryByText(/keep an eye on this spot/i)).not.toBeInTheDocument();
});

test("home search shows a skeleton while places load", async () => {
  const user = userEvent.setup();
  wrap(<HomePage />);
  await user.type(screen.getByLabelText(/uk place or postcode/i), "Ho");
  expect(await screen.findByTestId("search-skeleton")).toBeInTheDocument();
});
