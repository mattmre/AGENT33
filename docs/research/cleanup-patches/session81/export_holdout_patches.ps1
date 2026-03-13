$ErrorActionPreference = "Stop"

function Write-JoinedLines {
  param(
    [Parameter(Mandatory = $true)]
    [string]$Path,
    [AllowEmptyCollection()]
    [string[]]$Lines
  )

  if (-not $Lines -or $Lines.Count -eq 0) {
    if (Test-Path $Path) {
      Remove-Item $Path -Force
    }
    return
  }

  $content = ($Lines -join "`n") + "`n"
  [System.IO.File]::WriteAllText($Path, $content, [System.Text.UTF8Encoding]::new($false))
}

$repoRoot = (git rev-parse --show-toplevel).Trim()
$commonGitDir = (git rev-parse --git-common-dir).Trim()
$primaryRepoRoot = (Resolve-Path (Join-Path $commonGitDir "..")).Path
$archiveRoot = Join-Path $repoRoot "docs/research/cleanup-patches/session81"
New-Item -ItemType Directory -Force -Path $archiveRoot | Out-Null

$items = @(
  @{ Path = (Join-Path $primaryRepoRoot ".claude/worktrees/agent-a5a29d23"); Slug = "agent-a5a29d23"; Class = "keep-intact"; Note = "session59 tracks3-4 prototype" },
  @{ Path = (Join-Path $primaryRepoRoot ".claude/worktrees/agent-ab53cb8a"); Slug = "agent-ab53cb8a"; Class = "keep-intact"; Note = "session59 wave5 refinements prototype" },
  @{ Path = (Join-Path $primaryRepoRoot ".claude/worktrees/agent-ac4da72a"); Slug = "agent-ac4da72a"; Class = "keep-intact"; Note = "session59 tracks5-6 mutation-backup prototype" },
  @{ Path = (Join-Path $primaryRepoRoot ".claude/worktrees/agent-af722d5d"); Slug = "agent-af722d5d"; Class = "keep-intact"; Note = "session59 phase46 dynamic catalog prototype" }
)

$manifest = @()

foreach ($item in $items) {
  $path = $item.Path
  $slug = $item.Slug
  if (-not (Test-Path $path)) {
    Write-Warning "Skipping missing worktree path: $path"
    continue
  }
  $dir = Join-Path $archiveRoot $slug
  New-Item -ItemType Directory -Force -Path $dir | Out-Null

  $branch = git -C $path branch --show-current
  $subject = git -C $path show -s --format=%s HEAD
  $relativePath = [System.IO.Path]::GetRelativePath($primaryRepoRoot, $path).Replace("\", "/")
  $status = git -C $path status --porcelain
  $statusCount = if ($status) { @($status).Count } else { 0 }

  $committedPatch = Join-Path $dir "committed-vs-origin-main.patch"
  $committedDiff = git -C $path diff --binary --full-index origin/main...HEAD
  if ($committedDiff) {
    Write-JoinedLines -Path $committedPatch -Lines $committedDiff
    $committedBytes = (Get-Item $committedPatch).Length
  } else {
    if (Test-Path $committedPatch) {
      Remove-Item $committedPatch -Force
    }
    $committedBytes = 0
  }

  $trackedPatch = Join-Path $dir "working-tree-tracked.patch"
  $trackedDiff = git -C $path diff --binary --full-index HEAD
  if ($trackedDiff) {
    Write-JoinedLines -Path $trackedPatch -Lines $trackedDiff
    $trackedBytes = (Get-Item $trackedPatch).Length
  } else {
    if (Test-Path $trackedPatch) {
      Remove-Item $trackedPatch -Force
    }
    $trackedBytes = 0
  }

  $untrackedPatch = Join-Path $dir "working-tree-untracked.patch"
  $untrackedFiles = git -C $path ls-files --others --exclude-standard
  $untrackedCount = if ($untrackedFiles) { @($untrackedFiles).Count } else { 0 }
  if ($untrackedCount -gt 0) {
    [System.IO.File]::WriteAllText($untrackedPatch, "", [System.Text.UTF8Encoding]::new($false))
    Push-Location $path
    try {
      foreach ($rel in $untrackedFiles) {
        $patchText = git diff --no-index --binary /dev/null $rel
        if ($patchText) {
          $joined = ($patchText -join "`n") + "`n"
          [System.IO.File]::AppendAllText($untrackedPatch, $joined, [System.Text.UTF8Encoding]::new($false))
        }
      }
    }
    finally {
      Pop-Location
    }
    $untrackedBytes = (Get-Item $untrackedPatch).Length
  } else {
    if (Test-Path $untrackedPatch) {
      Remove-Item $untrackedPatch -Force
    }
    $untrackedBytes = 0
  }

  $statusPath = Join-Path $dir "status.txt"
  $statusOut = @(
    "path=$relativePath",
    "branch=$branch",
    "subject=$subject",
    "classification=$($item.Class)",
    "note=$($item.Note)",
    "status_count=$statusCount",
    "committed_patch_bytes=$committedBytes",
    "tracked_patch_bytes=$trackedBytes",
    "untracked_count=$untrackedCount",
    "untracked_patch_bytes=$untrackedBytes"
  )
  if ($statusCount -gt 0) {
    $statusOut += ""
    $statusOut += "[git-status]"
    $statusOut += $status
  }
  Set-Content -Path $statusPath -Value $statusOut

  $manifest += [pscustomobject]@{
    slug = $slug
    path = $relativePath
    branch = $branch
    classification = $item.Class
    note = $item.Note
    status_count = $statusCount
    committed_patch = if ($committedBytes -gt 0) { "committed-vs-origin-main.patch" } else { "" }
    committed_patch_bytes = $committedBytes
    tracked_patch = if ($trackedBytes -gt 0) { "working-tree-tracked.patch" } else { "" }
    tracked_patch_bytes = $trackedBytes
    untracked_count = $untrackedCount
    untracked_patch = if ($untrackedBytes -gt 0) { "working-tree-untracked.patch" } else { "" }
    untracked_patch_bytes = $untrackedBytes
  }
}

$manifest | ConvertTo-Json -Depth 3 | Set-Content -Path (Join-Path $archiveRoot "manifest.json")
$manifest | Export-Csv -NoTypeInformation -Path (Join-Path $archiveRoot "manifest.csv")
$manifest | Sort-Object slug | Format-Table slug, classification, status_count, committed_patch_bytes, tracked_patch_bytes, untracked_count, untracked_patch_bytes -AutoSize
