import { Link, NavLink, Outlet, Route, Routes } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "./api/client";
import { HomePage } from "./pages/HomePage";
import { WindowsPage } from "./pages/WindowsPage";
import { TargetsPage } from "./pages/TargetsPage";
import { SignInPage } from "./pages/SignInPage";
import { VerifyPage } from "./pages/VerifyPage";
import { SavedPage } from "./pages/SavedPage";
import { HistoryPage } from "./pages/HistoryPage";

function Shell() {
  const me = useQuery({ queryKey: ["me"], queryFn: api.me });
  const user = me.data?.user;
  return (
    <div className="min-h-screen">
      <header className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4">
        <Link to="/" className="flex items-center gap-2 font-display text-lg tracking-tight">
          <MoonMark />
          Astro Window
        </Link>
        <nav className="flex items-center gap-4 text-sm text-cream-dim">
          {user ? (
            <>
              <NavLink to="/saved" className="hover:text-cream">
                Saved places
              </NavLink>
              <span className="hidden sm:inline">{user.email}</span>
              <button
                type="button"
                className="hover:text-cream"
                onClick={async () => {
                  await api.logout();
                  me.refetch();
                }}
              >
                Sign out
              </button>
            </>
          ) : (
            <NavLink to="/sign-in" className="hover:text-cream">
              Sign in
            </NavLink>
          )}
        </nav>
      </header>
      <Outlet context={{ user }} />
      <footer className="mx-auto max-w-6xl px-4 py-10 text-xs text-cream-dim">
        <p>
          Weather: Open-Meteo. Places: GeoNames (CC-BY 4.0). Deep-sky catalogue derived from OpenNGC
          (CC-BY-SA 4.0).
        </p>
      </footer>
    </div>
  );
}

function MoonMark() {
  return (
    <svg width="28" height="28" viewBox="0 0 32 32" aria-hidden="true">
      <circle cx="16" cy="16" r="12" fill="#e8a54b" opacity="0.9" />
      <circle cx="21" cy="13" r="10" fill="#1a1624" />
    </svg>
  );
}

export default function App() {
  return (
    <Routes>
      <Route element={<Shell />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/windows" element={<WindowsPage />} />
        <Route path="/targets" element={<TargetsPage />} />
        <Route path="/sign-in" element={<SignInPage />} />
        <Route path="/auth/verify" element={<VerifyPage />} />
        <Route path="/saved" element={<SavedPage />} />
        <Route path="/saved/:id/history" element={<HistoryPage />} />
      </Route>
    </Routes>
  );
}
