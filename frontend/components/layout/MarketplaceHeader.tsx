"use client";
import { ReactNode } from "react";
import {
  Globe,
  Home,
  Sparkles,
  Menu,
  BriefcaseBusiness,
  Heart,
  Sun,
  Moon,
  UserRound,
  ArrowUpRight,
} from "lucide-react";
import { User } from "@/lib/api";
import { ActivityKind } from "@/lib/activities";
import { Logo } from "./Logo";
import { Avatar } from "../shared/Avatar";
type Props = {
  headerSearch: boolean;
  compactSearch: boolean;
  isExplore: boolean;
  activityKind: ActivityKind | null;
  user: User;
  menu: boolean;
  theme: "light" | "dark";
  clear: () => void;
  navigate: (route: string) => void;
  host: () => void;
  setMenu: (open: boolean) => void;
  setModal: (modal: string) => void;
  setTheme: (theme: "light" | "dark") => void;
  children: ReactNode;
};
export default function MarketplaceHeader({
  headerSearch,
  compactSearch,
  isExplore,
  activityKind,
  user,
  menu,
  theme,
  clear,
  navigate,
  host,
  setMenu,
  setModal,
  setTheme,
  children,
}: Props) {
  return (
    <header
      className={`site-header ${headerSearch ? "expanded" : ""} ${headerSearch && compactSearch ? "compact-search" : ""}`}
    >
      <div className="topbar">
        <button
          className="brand-button"
          onClick={() => {
            clear();
            navigate("explore");
          }}
          aria-label="Airbnb home"
        >
          <Logo />
        </button>
        <nav
          className="primary-nav"
          aria-label="Main navigation"
          inert={headerSearch && compactSearch}
        >
          <button
            className={isExplore ? "active" : ""}
            onClick={() => {
              navigate("explore");
            }}
          >
            <span className="nav-illustration house-illustration">
              <Home size={27} />
            </span>{" "}
            Homes
          </button>
          <button
            className={activityKind === "experiences" ? "active" : ""}
            onClick={() => navigate("experiences")}
          >
            <span className="nav-illustration balloon-illustration">
              <Globe size={27} />
            </span>{" "}
            Experiences <span className="new-label">NEW</span>
          </button>
          <button
            className={activityKind === "services" ? "active" : ""}
            onClick={() => navigate("services")}
          >
            <span className="nav-illustration service-illustration">
              <Sparkles size={26} />
            </span>{" "}
            Services <span className="new-label">NEW</span>
          </button>
        </nav>
        <div className="account-actions">
          <button className="host-link" onClick={host}>
            {user.role === "host" ? "Hosting dashboard" : "Become a host"}
          </button>
          <button
            className="icon-button language-button"
            aria-label="Language and currency"
            onClick={() => setModal("language")}
          >
            <Globe size={19} />
          </button>
          <div className="account-container">
            <button
              className="profile-button"
              aria-label="Open account menu"
              aria-expanded={menu}
              onClick={() => setMenu(!menu)}
            >
              <Menu size={18} />
              <span className="profile-avatar">
                <Avatar initials={user.avatar} name={user.name} />
              </span>
            </button>
            {menu && (
              <>
                <button
                  className="menu-dismiss"
                  tabIndex={-1}
                  aria-label="Close account menu"
                  onClick={() => setMenu(false)}
                />
                <div className="account-menu">
                  <div className="menu-profile">
                    <Avatar initials={user.avatar} name={user.name} />
                    <div>
                      <strong>{user.name}</strong>
                      <small>Demo {user.role} profile</small>
                    </div>
                  </div>
                  <button onClick={() => navigate("trips")}>
                    <BriefcaseBusiness size={18} /> Trips
                  </button>
                  <button onClick={() => navigate("wishlists")}>
                    <Heart size={18} /> Wishlists
                  </button>
                  <button onClick={host}>
                    <Home size={18} /> Hosting dashboard
                  </button>
                  <button
                    aria-label={
                      theme === "dark"
                        ? "Switch to light mode"
                        : "Switch to dark mode"
                    }
                    aria-pressed={theme === "dark"}
                    onClick={() => {
                      const next = theme === "dark" ? "light" : "dark";
                      setTheme(next);
                      document.documentElement.dataset.theme = next;
                      try {
                        localStorage.setItem("airbnb-theme-v1", next);
                      } catch {
                        /* Keep the selected theme for this visit. */
                      }
                      setMenu(false);
                    }}
                  >
                    {theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
                    {theme === "dark" ? "Light mode" : "Dark mode"}
                  </button>
                  <hr />
                  <button
                    onClick={() => {
                      setMenu(false);
                      setModal("profiles");
                    }}
                  >
                    <UserRound size={18} /> Switch demo profile
                  </button>
                  <button
                    onClick={() => {
                      setMenu(false);
                      setModal("help");
                    }}
                  >
                    Help centre <ArrowUpRight size={16} />
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
      {children}
    </header>
  );
}
