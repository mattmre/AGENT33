import { APP_TAB_GROUPS, type AppTab } from "../data/navigation";

interface AppNavigationProps {
  activeTab: AppTab;
  onNavigate: (tab: AppTab) => void;
}

export function AppNavigation({ activeTab, onNavigate }: AppNavigationProps): JSX.Element {
  return (
    <nav className="main-nav cockpit-sidebar-nav" aria-label="Main navigation">
      {APP_TAB_GROUPS.map((group) => (
        <section key={group.label} className="main-nav-group" aria-label={`${group.label} navigation`}>
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
    </nav>
  );
}
