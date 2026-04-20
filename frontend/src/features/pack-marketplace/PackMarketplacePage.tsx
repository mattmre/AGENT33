import { useCallback, useEffect, useMemo, useState } from "react";

import {
  fetchCurationRecords,
  fetchFeaturedRecords,
  fetchInstalledPackDetail,
  fetchInstalledPacks,
  fetchMarketplaceCategories,
  fetchMarketplacePackDetail,
  fetchMarketplacePacks,
  fetchPackTrust,
  installMarketplacePack
} from "./api";
import type {
  CurationRecord,
  InstalledPackDetail,
  InstalledPackSummary,
  MarketplaceCategory,
  MarketplacePackDetail,
  MarketplacePackSummary,
  MarketplacePackVersionInfo,
  PackTrustResponse
} from "./types";

interface PackMarketplacePageProps {
  token: string | null;
  apiKey: string | null;
}

interface CategoryOption {
  slug: string;
  label: string;
  count: number;
  description: string;
}

function recordMap(records: CurationRecord[]): Record<string, CurationRecord> {
  return records.reduce<Record<string, CurationRecord>>((acc, record) => {
    acc[record.pack_name] = record;
    return acc;
  }, {});
}

function installedMap(packs: InstalledPackSummary[]): Record<string, InstalledPackSummary> {
  return packs.reduce<Record<string, InstalledPackSummary>>((acc, pack) => {
    acc[pack.name] = pack;
    return acc;
  }, {});
}

function formatStatus(value: string): string {
  return value.replace(/_/g, " ");
}

function formatTrust(value: string | null): string {
  return value ? value.replace(/_/g, " ") : "Unknown";
}

function filterMatches(pack: MarketplacePackSummary, query: string): boolean {
  const haystack = [
    pack.name,
    pack.description,
    pack.author,
    pack.category,
    ...pack.tags
  ]
    .join(" ")
    .toLowerCase();
  return haystack.includes(query.toLowerCase());
}

function buildCategoryOptions(
  packs: MarketplacePackSummary[],
  categories: MarketplaceCategory[]
): CategoryOption[] {
  const counts = packs.reduce<Record<string, number>>((acc, pack) => {
    if (!pack.category) {
      return acc;
    }
    acc[pack.category] = (acc[pack.category] ?? 0) + 1;
    return acc;
  }, {});

  return Object.entries(counts)
    .map(([slug, count]) => {
      const category = categories.find((entry) => entry.slug === slug);
      return {
        slug,
        label: category?.label ?? slug,
        count,
        description: category?.description ?? ""
      };
    })
    .sort((left, right) => left.label.localeCompare(right.label));
}

function versionLabel(version: MarketplacePackVersionInfo): string {
  return `${version.version}${version.trust_level ? ` · ${formatTrust(version.trust_level)}` : ""}`;
}

function qualityLabel(record: CurationRecord | null): string | null {
  if (!record?.quality) {
    return null;
  }
  return `${record.quality.label} quality · ${Math.round(record.quality.overall_score * 100)}%`;
}

function PackDetailPanel({
  pack,
  installed,
  trust,
  curation,
  selectedVersion,
  detailLoading,
  detailError,
  installPending,
  installFeedback,
  onVersionChange,
  onInstall,
  onClose
}: {
  pack: MarketplacePackDetail | null;
  installed: InstalledPackDetail | null;
  trust: PackTrustResponse | null;
  curation: CurationRecord | null;
  selectedVersion: string;
  detailLoading: boolean;
  detailError: string | null;
  installPending: boolean;
  installFeedback: string | null;
  onVersionChange: (value: string) => void;
  onInstall: () => void;
  onClose: () => void;
}): JSX.Element | null {
  if (!pack) {
    return null;
  }

  const installedSameVersion = installed?.version === selectedVersion;
  const quality = qualityLabel(curation);

  return (
    <aside className="pack-marketplace-detail" aria-label={`Details for ${pack.name}`}>
      <header className="pack-marketplace-detail-header">
        <div>
          <h2>{pack.name}</h2>
          <p>{pack.description || "No description available."}</p>
        </div>
        <button type="button" onClick={onClose} aria-label="Close marketplace detail panel">
          Close
        </button>
      </header>

      {detailLoading && <p className="pack-marketplace-loading">Loading pack details...</p>}
      {detailError && <p className="pack-marketplace-error">{detailError}</p>}

      {!detailLoading && !detailError && (
        <div className="pack-marketplace-detail-body">
          <div className="pack-marketplace-badges">
            {curation?.featured && <span className="marketplace-pill featured">Featured</span>}
            {curation?.verified && <span className="marketplace-pill verified">Verified</span>}
            {installed && <span className="marketplace-pill installed">Installed</span>}
            <span className="marketplace-pill neutral">{pack.latest_version}</span>
          </div>

          <dl className="pack-marketplace-metadata">
            <dt>Author</dt>
            <dd>{pack.author || "Unknown"}</dd>

            <dt>Category</dt>
            <dd>{pack.category || "Uncategorized"}</dd>

            <dt>Sources</dt>
            <dd>{pack.sources.length > 0 ? pack.sources.join(", ") : "None published"}</dd>

            <dt>Versions</dt>
            <dd>{pack.versions.length}</dd>

            {curation && (
              <>
                <dt>Curation</dt>
                <dd>{formatStatus(curation.status)}</dd>
              </>
            )}

            {quality && (
              <>
                <dt>Quality</dt>
                <dd>{quality}</dd>
              </>
            )}

            {curation && curation.download_count > 0 && (
              <>
                <dt>Downloads</dt>
                <dd>{curation.download_count}</dd>
              </>
            )}

            {installed && (
              <>
                <dt>Installed</dt>
                <dd>
                  {installed.version}
                  {installed.enabled_for_tenant ? " · enabled for tenant" : " · disabled for tenant"}
                </dd>
              </>
            )}

            {trust && (
              <>
                <dt>Trust</dt>
                <dd>{trust.allowed ? "Allowed by policy" : `Blocked: ${trust.reason || "policy"}`}</dd>
              </>
            )}
          </dl>

          {pack.tags.length > 0 && (
            <section>
              <h3>Tags</h3>
              <div className="pack-marketplace-tags">
                {pack.tags.map((tag) => (
                  <span key={tag} className="marketplace-tag">
                    {tag}
                  </span>
                ))}
              </div>
            </section>
          )}

          <section className="pack-marketplace-version-section">
            <div className="pack-marketplace-version-header">
              <h3>Available versions</h3>
              <label>
                <span>Select version</span>
                <select value={selectedVersion} onChange={(event) => onVersionChange(event.target.value)}>
                  {pack.versions.map((version) => (
                    <option key={version.version} value={version.version}>
                      {versionLabel(version)}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            <ul className="pack-marketplace-version-list">
              {pack.versions.map((version) => (
                <li key={version.version}>
                  <button
                    type="button"
                    className={`pack-marketplace-version-button ${
                      selectedVersion === version.version ? "active" : ""
                    }`}
                    aria-pressed={selectedVersion === version.version}
                    onClick={() => onVersionChange(version.version)}
                  >
                    <div>
                      <strong>{version.version}</strong>
                      <span>{version.source_name || version.source_type || "marketplace"}</span>
                    </div>
                    <div>
                      <span>{version.skills_count} skill(s)</span>
                      <span>{formatTrust(version.trust_level)}</span>
                    </div>
                  </button>
                </li>
              ))}
            </ul>
          </section>

          <div className="pack-marketplace-actions">
            <button
              type="button"
              className="pack-marketplace-primary"
              disabled={installPending || installedSameVersion}
              onClick={onInstall}
            >
              {installedSameVersion
                ? "Installed"
                : installPending
                  ? "Installing..."
                  : "Install selected version"}
            </button>
            {installFeedback && <p className="pack-marketplace-feedback">{installFeedback}</p>}
          </div>
        </div>
      )}
    </aside>
  );
}

export function PackMarketplacePage({ token, apiKey }: PackMarketplacePageProps): JSX.Element {
  const [packs, setPacks] = useState<MarketplacePackSummary[]>([]);
  const [categories, setCategories] = useState<MarketplaceCategory[]>([]);
  const [curationByPack, setCurationByPack] = useState<Record<string, CurationRecord>>({});
  const [installedByPack, setInstalledByPack] = useState<Record<string, InstalledPackSummary>>({});
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedPackName, setSelectedPackName] = useState<string | null>(null);
  const [selectedPackDetail, setSelectedPackDetail] = useState<MarketplacePackDetail | null>(null);
  const [selectedInstalledDetail, setSelectedInstalledDetail] = useState<InstalledPackDetail | null>(null);
  const [selectedTrust, setSelectedTrust] = useState<PackTrustResponse | null>(null);
  const [selectedVersion, setSelectedVersion] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState<string | null>(null);
  const [installPending, setInstallPending] = useState(false);
  const [installFeedback, setInstallFeedback] = useState<string | null>(null);

  const loadMarketplace = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const [packResult, categoryResult, featuredResult, curationResult, installedResult] =
        await Promise.allSettled([
          fetchMarketplacePacks(token, apiKey),
          fetchMarketplaceCategories(token, apiKey),
          fetchFeaturedRecords(token, apiKey),
          fetchCurationRecords(token, apiKey),
          fetchInstalledPacks(token, apiKey)
        ]);

      if (packResult.status === "rejected") {
        throw packResult.reason;
      }

      setPacks(packResult.value);
      setCategories(categoryResult.status === "fulfilled" ? categoryResult.value : []);
      setInstalledByPack(
        installedMap(installedResult.status === "fulfilled" ? installedResult.value : [])
      );

      const mergedCuration =
        curationResult.status === "fulfilled" ? recordMap(curationResult.value) : {};

      if (featuredResult.status === "fulfilled") {
        featuredResult.value.forEach((record) => {
          const existing = mergedCuration[record.pack_name];
          if (!existing) {
            mergedCuration[record.pack_name] = record;
            return;
          }

          mergedCuration[record.pack_name] = {
            ...existing,
            ...record,
            featured: true,
            badges: Array.from(new Set([...existing.badges, ...record.badges]))
          };
        });
      }

      setCurationByPack(mergedCuration);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load marketplace");
    } finally {
      setLoading(false);
    }
  }, [apiKey, token]);

  useEffect(() => {
    void loadMarketplace();
  }, [loadMarketplace]);

  useEffect(() => {
    if (!selectedPackName) {
      setSelectedPackDetail(null);
      setSelectedInstalledDetail(null);
      setSelectedTrust(null);
      setSelectedVersion("");
      setDetailError(null);
      return;
    }

    const packName = selectedPackName;
    let cancelled = false;

    async function loadSelectedPack(): Promise<void> {
      setDetailLoading(true);
      setDetailError(null);

      try {
        const detail = await fetchMarketplacePackDetail(token, apiKey, packName);
        if (cancelled) {
          return;
        }
        setSelectedPackDetail(detail);
        setSelectedVersion((current) => current || detail.latest_version);

        if (!installedByPack[packName]) {
          setSelectedInstalledDetail(null);
          setSelectedTrust(null);
          return;
        }

        const [installedResult, trustResult] = await Promise.allSettled([
          fetchInstalledPackDetail(token, apiKey, packName),
          fetchPackTrust(token, apiKey, packName)
        ]);

        if (cancelled) {
          return;
        }

        setSelectedInstalledDetail(installedResult.status === "fulfilled" ? installedResult.value : null);
        setSelectedTrust(trustResult.status === "fulfilled" ? trustResult.value : null);
      } catch (err) {
        if (!cancelled) {
          setDetailError(err instanceof Error ? err.message : "Failed to load pack detail");
        }
      } finally {
        if (!cancelled) {
          setDetailLoading(false);
        }
      }
    }

    void loadSelectedPack();

    return () => {
      cancelled = true;
    };
  }, [apiKey, installedByPack, selectedPackName, token]);

  const featuredPacks = useMemo(
    () => packs.filter((pack) => Boolean(curationByPack[pack.name]?.featured)).slice(0, 3),
    [curationByPack, packs]
  );

  const categoryOptions = useMemo(
    () => buildCategoryOptions(packs, categories),
    [categories, packs]
  );

  const filteredPacks = useMemo(() => {
    return packs.filter((pack) => {
      if (selectedCategory && pack.category !== selectedCategory) {
        return false;
      }
      if (searchQuery.trim() && !filterMatches(pack, searchQuery.trim())) {
        return false;
      }
      return true;
    });
  }, [packs, searchQuery, selectedCategory]);

  const openPack = (name: string): void => {
    setSelectedPackName(name);
    setSelectedPackDetail(null);
    setSelectedInstalledDetail(null);
    setSelectedTrust(null);
    setSelectedVersion("");
    setInstallFeedback(null);
  };

  const handleInstall = async (): Promise<void> => {
    if (!selectedPackDetail) {
      return;
    }

    setInstallPending(true);
    setInstallFeedback(null);

    try {
      const result = await installMarketplacePack(
        token,
        apiKey,
        selectedPackDetail.name,
        selectedVersion || selectedPackDetail.latest_version
      );
      const installedVersion = result.version || selectedVersion || selectedPackDetail.latest_version;

      setInstalledByPack((current) => ({
        ...current,
        [selectedPackDetail.name]: {
          name: selectedPackDetail.name,
          version: installedVersion,
          description: selectedPackDetail.description,
          author: selectedPackDetail.author,
          tags: selectedPackDetail.tags,
          category: selectedPackDetail.category,
          skills_count:
            selectedPackDetail.versions.find((item) => item.version === installedVersion)
              ?.skills_count ?? 0,
          status: "installed"
        }
      }));

      setInstallFeedback(`Installed ${result.pack_name} ${installedVersion}`);
    } catch (err) {
      setInstallFeedback(err instanceof Error ? err.message : "Install failed");
    } finally {
      setInstallPending(false);
    }
  };

  return (
    <div className="pack-marketplace-page">
      <header className="pack-marketplace-header">
        <h1>Pack Marketplace</h1>
        <p>
          Browse curated packs, inspect versions and trust posture, and install packs without
          leaving the web UI.
        </p>
      </header>

      {featuredPacks.length > 0 && (
        <section className="pack-marketplace-featured" aria-label="Featured packs">
          <div className="pack-marketplace-section-heading">
            <h2>Featured</h2>
            <span>{featuredPacks.length} highlighted pack(s)</span>
          </div>
          <div className="pack-marketplace-featured-grid">
            {featuredPacks.map((pack) => (
              <button
                key={pack.name}
                type="button"
                className="pack-marketplace-featured-card"
                onClick={() => openPack(pack.name)}
                aria-label={`Open details for ${pack.name}`}
              >
                <strong>{pack.name}</strong>
                <span>{pack.description || "No description available."}</span>
                <div className="pack-marketplace-badges">
                  <span className="marketplace-pill featured">Featured</span>
                  <span className="marketplace-pill neutral">{pack.latest_version}</span>
                </div>
              </button>
            ))}
          </div>
        </section>
      )}

      <div className="pack-marketplace-layout">
        <aside className="pack-marketplace-sidebar">
          <div className="pack-marketplace-filter-card">
            <h3>Categories</h3>
            <button
              type="button"
              className={selectedCategory === null ? "active" : ""}
              aria-pressed={selectedCategory === null}
              onClick={() => setSelectedCategory(null)}
            >
              <span>All</span>
              <span>{packs.length}</span>
            </button>
            {categoryOptions.map((category) => (
              <button
                key={category.slug}
                type="button"
                className={selectedCategory === category.slug ? "active" : ""}
                aria-pressed={selectedCategory === category.slug}
                onClick={() =>
                  setSelectedCategory((current) => (current === category.slug ? null : category.slug))
                }
                title={category.description}
              >
                <span>{category.label}</span>
                <span>{category.count}</span>
              </button>
            ))}
          </div>
        </aside>

        <main className="pack-marketplace-main">
          <div className="pack-marketplace-toolbar">
            <label className="pack-marketplace-search">
              <span className="sr-only">Search marketplace packs</span>
              <input
                type="search"
                placeholder="Search packs by name, author, category, or tag..."
                value={searchQuery}
                onChange={(event) => setSearchQuery(event.target.value)}
                aria-label="Search marketplace packs"
              />
            </label>
            <p className="pack-marketplace-count">
              {filteredPacks.length} pack{filteredPacks.length !== 1 ? "s" : ""}
            </p>
          </div>

          {loading && <p className="pack-marketplace-loading">Loading marketplace packs...</p>}
          {error && <p className="pack-marketplace-error">{error}</p>}

          {!loading && !error && filteredPacks.length === 0 && (
            <div className="pack-marketplace-empty">
              <h2>No packs match this filter</h2>
              <p>Try clearing the category filter or broadening the search terms.</p>
            </div>
          )}

          {!loading && !error && filteredPacks.length > 0 && (
            <div className="pack-marketplace-grid">
              {filteredPacks.map((pack) => {
                const curation = curationByPack[pack.name] ?? null;
                const installed = installedByPack[pack.name] ?? null;

                return (
                  <button
                    key={pack.name}
                    type="button"
                    className={`pack-marketplace-card ${
                      selectedPackName === pack.name ? "selected" : ""
                    }`}
                    aria-label={`Open details for ${pack.name}`}
                    onClick={() => openPack(pack.name)}
                  >
                    <div className="pack-marketplace-card-header">
                      <div>
                        <h3>{pack.name}</h3>
                        <p>{pack.author || "Unknown author"}</p>
                      </div>
                      <span className="marketplace-pill neutral">{pack.latest_version}</span>
                    </div>

                    <p className="pack-marketplace-card-description">
                      {pack.description || "No description available."}
                    </p>

                    <div className="pack-marketplace-badges">
                      <span className="marketplace-pill neutral">
                        {pack.category || "Uncategorized"}
                      </span>
                      <span className="marketplace-pill neutral">
                        {pack.versions_count} version{pack.versions_count !== 1 ? "s" : ""}
                      </span>
                      {installed && <span className="marketplace-pill installed">Installed</span>}
                      {curation?.featured && <span className="marketplace-pill featured">Featured</span>}
                      {curation && !curation.featured && (
                        <span className="marketplace-pill verified">
                          {formatStatus(curation.status)}
                        </span>
                      )}
                    </div>

                    {pack.tags.length > 0 && (
                      <div className="pack-marketplace-tags">
                        {pack.tags.slice(0, 4).map((tag) => (
                          <span key={tag} className="marketplace-tag">
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}
                  </button>
                );
              })}
            </div>
          )}
        </main>

        <PackDetailPanel
          pack={selectedPackDetail}
          installed={selectedInstalledDetail}
          trust={selectedTrust}
          curation={selectedPackName ? curationByPack[selectedPackName] ?? null : null}
          selectedVersion={selectedVersion}
          detailLoading={detailLoading}
          detailError={detailError}
          installPending={installPending}
          installFeedback={installFeedback}
          onVersionChange={setSelectedVersion}
          onInstall={() => void handleInstall()}
          onClose={() => setSelectedPackName(null)}
        />
      </div>
    </div>
  );
}
