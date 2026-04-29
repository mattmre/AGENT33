export interface MarketplacePackSummary {
  name: string;
  description: string;
  author: string;
  tags: string[];
  category: string;
  latest_version: string;
  versions_count: number;
  sources: string[];
  trust_level?: string | null;
}

export interface MarketplacePackVersionInfo {
  version: string;
  description: string;
  author: string;
  tags: string[];
  category: string;
  skills_count: number;
  source_name: string;
  source_type: string;
  trust_level: string | null;
}

export interface MarketplacePackDetail {
  name: string;
  description: string;
  author: string;
  tags: string[];
  category: string;
  latest_version: string;
  versions: MarketplacePackVersionInfo[];
  sources: string[];
}

export interface MarketplaceCategory {
  slug: string;
  label: string;
  description: string;
  parent_slug: string;
}

export interface QualityCheck {
  name: string;
  passed: boolean;
  score: number;
  reason: string;
}

export interface QualityAssessment {
  overall_score: number;
  label: string;
  passed: boolean;
  checks?: QualityCheck[];
  assessed_at?: string;
}

export interface CurationRecord {
  pack_name: string;
  version: string;
  status: string;
  quality: QualityAssessment | null;
  badges: string[];
  featured: boolean;
  verified: boolean;
  reviewer_id: string;
  review_notes: string;
  deprecation_reason: string;
  submitted_at: string | null;
  reviewed_at: string | null;
  listed_at: string | null;
  download_count: number;
}

export interface InstalledPackSummary {
  name: string;
  version: string;
  description: string;
  author: string;
  tags: string[];
  category: string;
  skills_count: number;
  status: string;
}

export interface InstalledPackDetail extends InstalledPackSummary {
  license: string;
  loaded_skill_names: string[];
  engine_min_version: string;
  installed_at: string | null;
  source: string;
  source_reference: string;
  checksum: string;
  enabled_for_tenant: boolean;
}

export interface PackTrustPolicy {
  require_signature?: boolean;
  min_trust_level?: string | null;
  allowed_signers?: string[];
}

export interface PackTrustResponse {
  pack_name: string;
  installed_version: string;
  source: string;
  source_reference: string;
  allowed: boolean;
  reason: string;
  policy: PackTrustPolicy;
}

export interface MarketplaceInstallResponse {
  success: boolean;
  pack_name: string;
  version: string;
  skills_loaded: number;
  errors: string[];
  warnings: string[];
}
