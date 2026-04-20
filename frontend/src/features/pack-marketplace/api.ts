import { getRuntimeConfig } from "../../lib/api";
import type {
  CurationRecord,
  InstalledPackDetail,
  InstalledPackSummary,
  MarketplaceCategory,
  MarketplaceInstallResponse,
  MarketplacePackDetail,
  MarketplacePackSummary,
  PackTrustResponse
} from "./types";

function baseUrl(): string {
  return getRuntimeConfig().API_BASE_URL;
}

function headers(token: string | null, apiKey: string | null): Record<string, string> {
  const result: Record<string, string> = { Accept: "application/json" };
  if (token) {
    result.Authorization = `Bearer ${token}`;
  }
  if (apiKey) {
    result["X-API-Key"] = apiKey;
  }
  return result;
}

async function parseJson<T>(response: Response, message: string): Promise<T> {
  if (!response.ok) {
    throw new Error(`${message}: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export async function fetchMarketplacePacks(
  token: string | null,
  apiKey: string | null
): Promise<MarketplacePackSummary[]> {
  const response = await fetch(`${baseUrl()}/v1/marketplace/packs`, {
    headers: headers(token, apiKey)
  });
  const data = await parseJson<{ packs: MarketplacePackSummary[] }>(
    response,
    "Marketplace list failed"
  );
  return data.packs;
}

export async function fetchMarketplacePackDetail(
  token: string | null,
  apiKey: string | null,
  name: string
): Promise<MarketplacePackDetail> {
  const response = await fetch(`${baseUrl()}/v1/marketplace/packs/${encodeURIComponent(name)}`, {
    headers: headers(token, apiKey)
  });
  return parseJson<MarketplacePackDetail>(response, "Marketplace detail failed");
}

export async function fetchMarketplaceCategories(
  token: string | null,
  apiKey: string | null
): Promise<MarketplaceCategory[]> {
  const response = await fetch(`${baseUrl()}/v1/marketplace/categories`, {
    headers: headers(token, apiKey)
  });
  const data = await parseJson<{ categories: MarketplaceCategory[] }>(
    response,
    "Marketplace categories failed"
  );
  return data.categories;
}

export async function fetchFeaturedRecords(
  token: string | null,
  apiKey: string | null
): Promise<CurationRecord[]> {
  const response = await fetch(`${baseUrl()}/v1/marketplace/featured`, {
    headers: headers(token, apiKey)
  });
  const data = await parseJson<{ records: CurationRecord[] }>(response, "Featured packs failed");
  return data.records;
}

export async function fetchCurationRecords(
  token: string | null,
  apiKey: string | null
): Promise<CurationRecord[]> {
  const response = await fetch(`${baseUrl()}/v1/marketplace/curation`, {
    headers: headers(token, apiKey)
  });
  const data = await parseJson<{ records: CurationRecord[] }>(response, "Curation list failed");
  return data.records;
}

export async function fetchInstalledPacks(
  token: string | null,
  apiKey: string | null
): Promise<InstalledPackSummary[]> {
  const response = await fetch(`${baseUrl()}/v1/packs`, {
    headers: headers(token, apiKey)
  });
  const data = await parseJson<{ packs: InstalledPackSummary[] }>(response, "Installed packs failed");
  return data.packs;
}

export async function fetchInstalledPackDetail(
  token: string | null,
  apiKey: string | null,
  name: string
): Promise<InstalledPackDetail> {
  const response = await fetch(`${baseUrl()}/v1/packs/${encodeURIComponent(name)}`, {
    headers: headers(token, apiKey)
  });
  return parseJson<InstalledPackDetail>(response, "Installed pack detail failed");
}

export async function fetchPackTrust(
  token: string | null,
  apiKey: string | null,
  name: string
): Promise<PackTrustResponse> {
  const response = await fetch(`${baseUrl()}/v1/packs/${encodeURIComponent(name)}/trust`, {
    headers: headers(token, apiKey)
  });
  return parseJson<PackTrustResponse>(response, "Pack trust failed");
}

export async function installMarketplacePack(
  token: string | null,
  apiKey: string | null,
  name: string,
  version: string
): Promise<MarketplaceInstallResponse> {
  const response = await fetch(`${baseUrl()}/v1/marketplace/install`, {
    method: "POST",
    headers: { ...headers(token, apiKey), "Content-Type": "application/json" },
    body: JSON.stringify({ name, version })
  });
  return parseJson<MarketplaceInstallResponse>(response, "Marketplace install failed");
}
