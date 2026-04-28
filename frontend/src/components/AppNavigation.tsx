import { useEffect, useState } from "react";

import {
  APP_PRIMARY_NAV_ITEMS,
  APP_SECONDARY_NAV_GROUPS,
  getAppTabLabel,
  isSecondaryAppTab,
  type AppTab
} from "../data/navigation";

interface AppNavigationProps {
  activeTab: AppTab;
  onNavigate: (tab: AppTab) => void;
}

export function AppNavigation({ activeTab, onNavigate }: AppNavigationProps): JSX.Element {
  const isToolsSectionActive = isSecondaryAppTab(activeTab);
  const [isToolsOpen, setIsToolsOpen] = useState(isToolsSectionActive);

  useEffect(() => {
    if (isToolsSectionActive) {
      setIsToolsOpen(true);
    }
  }, [isToolsSectionActive]);

  return (
    <nav className="main-nav cockpit-sidebar-nav" aria-label="Main navigation">
      <section className="main-nav-group main-nav-primary" aria-label="Cockpit navigation">
        <span className="main-nav-group-label">Cockpit</span>
        <div className="main-nav-group-tabs">
          {APP_PRIMARY_NAV_ITEMS.map((item) => (
            <button
              key={item.id}
              type="button"
              className={activeTab === item.id ? "active" : ""}
              onClick={() => onNavigate(item.id)}
              aria-current={activeTab === item.id ? "page" : undefined}
            >
              <span className="main-nav-button-label">{getAppTabLabel(item.id)}</span>
              <small>{item.description}</small>
            </button>
          ))}
        </div>
      </section>

      <details
        className="main-nav-group main-nav-tools"
        open={isToolsOpen}
        onToggle={(event) => setIsToolsOpen(event.currentTarget.open)}
      >
        <summary>
          <span>Tools & advanced surfaces</span>
        </summary>
        <p className="main-nav-tools-description">
          Specialized builders, MCP, analytics, marketplace, and setup panels.
        </p>
        <div className="main-nav-tool-groups">
          {APP_SECONDARY_NAV_GROUPS.map((group) => (
            <section key={group.label} className="main-nav-tool-group" aria-label={`${group.label} tools`}>
              <span className="main-nav-group-label">{group.label}</span>
              <div className="main-nav-group-tabs">
                {group.tabs.map((tab) => (
                  <button
                    key={tab.id}
                    type="button"
                    className={activeTab === tab.id ? "active" : ""}
                    onClick={() => onNavigate(tab.id)}
                    aria-current={activeTab === tab.id ? "page" : undefined}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>
            </section>
          ))}
        </div>
      </details>
    </nav>
  );
}
