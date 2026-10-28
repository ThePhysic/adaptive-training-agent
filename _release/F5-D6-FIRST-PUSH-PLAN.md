# F5-D6 first-push review plan - NOT EXECUTION AUTHORIZATION

## Exact destination and local scope

- Local directory basename: future-training-portfolio-rc-f5-d3-source (the owner's
  exact approved separate curated directory, never the development repository).
- Branch: main. Current HEAD: a4306aa47fd0535c5d2ead7b7bc3e0fab78a011a.
- Existing local history: exactly two commits; no rewrite/amend is proposed.
- Intended future remote: https://github.com/ThePhysic/adaptive-training-agent.git.
- Remote repository is private and empty; no local remote is configured.
- ThePhysic/future-adaptive-training-agent is a different, preserved project.

The source-only working inventory is recorded path-by-path with SHA-256 and Git
state in the D6 review archive's generated _review/source-manifest.json and its
external sidecar source-manifest.json. That is the exact proposed source scope;
it includes prepared uncommitted licensing/notice documents. It is not a claim that
these bytes are already in HEAD. The 605 existing tracked files remain at the
accepted revision, except README's uncommitted licensing paragraph. No node_modules,
dist, private data, .git, caches, state, AGENTS.md or nine omitted documents may enter
a commit or upload. Any inventory drift requires another scope review.

## Stage 1 - separately approve the license/documentation commit

Owner/reviewer must approve the D6 source manifest, exact diff and actual upstream
notice copies. The new LICENSE and README/notice records are uncommitted; a new
third local commit is necessary to include them in the eventual first push.
No license commit was made in D6. Do not amend either existing commit or use blanket
staging. Future staging must enumerate only the D6 reviewed paths and verify each
index blob against the approved SHA-256 inventory. Refresh a separate current-source
manifest for any later changed files; do not rewrite historical D3-D5 manifests.

A future local-commit authorization must state the reviewed path list, commit
message and one-commit limit. Then verify three commits, expected parent, exact
committed file inventory and no other changes. Re-run source, license and contract
checks as appropriate before proposing the resulting new revision for upload.

## Stage 2 - separately approve source upload AND automatic hosted CI

A first push contains the complete reviewed curated history, not only the LICENSE
change. The unchanged .github/workflows/offline.yml triggers on push, pull_request
and manual dispatch. Thus permission to upload main must explicitly address the
resulting hosted run, dependency/image acquisition, possible private-repository
billable minutes/storage and the exact source revision. D6 grants none of these.
Owner checks account Actions availability/allowance/spending controls first; no
billing API or assumed free allowance is used here. [GitHub's billing documentation](https://docs.github.com/en/billing/concepts/product-billing/github-actions)
confirms private-repository usage depends on the plan allowance and may be charged
beyond it. Do not add a skip marker or weaken mandatory coverage to avoid that decision.

When those approvals exist, the intended sequence is the following, using the
reviewed third commit ID, not blindly pushing whatever HEAD later contains:

```powershell
# FUTURE ONLY: stop unless source, remote configuration, push and one automatic CI run are explicitly approved.
$approvedRoot = Join-Path $env:USERPROFILE 'future-training-portfolio-rc-f5-d3-source'
Set-Location -LiteralPath $approvedRoot
# Owner enters the separately reviewed NEW license commit, never a branch-only approval.
$approvedRevision = Read-Host 'Separately approved third-commit hash'
if ($approvedRevision -cnotmatch '^[0-9a-f]{40}$') { throw 'Invalid reviewed revision' }
$actualRoot = (git rev-parse --show-toplevel).Replace('/', [IO.Path]::DirectorySeparatorChar)
if ($LASTEXITCODE -ne 0 -or $actualRoot -ine $approvedRoot) { throw 'Wrong local repository' }
if ((git branch --show-current) -cne 'main') { throw 'Wrong branch' }
if ((git rev-parse HEAD) -cne $approvedRevision) { throw 'Unapproved HEAD' }
if ((git rev-list --count HEAD) -ne '3') { throw 'Unexpected history' }
if (git status --porcelain=v1) { throw 'Uncommitted changes' }
if (git remote) { throw 'Unexpected existing remote' }
# Independently compare the complete committed-file inventory to the approved manifest.
# Read-only gh checks must reconfirm ThePhysic and this private, still-empty destination.
gh api --hostname github.com user --jq .login
gh repo view ThePhysic/adaptive-training-agent --json nameWithOwner,visibility,isEmpty
# Configure only after that separate remote authorization:
git remote add origin https://github.com/ThePhysic/adaptive-training-agent.git
# Verify exact URL, then under the separate upload/CI authorization:
if ((git remote get-url origin) -cne 'https://github.com/ThePhysic/adaptive-training-agent.git') {
    throw 'Unexpected remote URL'
}
# Exact immutable source revision; no force, branch drift or other refs:
git push origin "${approvedRevision}:refs/heads/main"
```

No force push, mirror, --all, tag upload, template/import, dispatch or duplicate
workflow run is proposed. Stop if the repository is no longer empty/private or any
remote/ref/identity differs. Do not overwrite another user's initialization. A failed
or uncertain push is reconciled by read-only ref/run checks before any additional
operation; no automatic push/run retry is authorized.

## Hosted verification and resource envelope

The existing single Ubuntu 24.04 job has a 75-minute job bound: 45m routine, 3m
mandatory installed browser, 15m remaining integration, plus setup/release reserve.
It installs pinned Python/uv/npm dependencies and public DB/base images, exercises
local synthetic PostgreSQL and TLS, runs the isolated SDK checks and local Docker
release/restore drill. Required checks/failure propagation remain unchanged.
Read-only repository permissions and fake provider/no-export configuration must
remain; no genuine/provider/AWS secrets or deployment credentials should be supplied.

Historical local D5 measured routine 22m36.61s and native 7m29.21s. Those are Windows
measurements, not guarantees for hosted Ubuntu. The 75-minute limit is not an
approved cost cap. Private Actions usage may be billable according to the owner's
account allowance and current terms; no price or free-minutes assumption is made.
The workflow has no general artifact-upload step. Do not dispatch manually if the
approved push already starts the intended run.

After the first push verify remote main equals the separately approved revision,
private visibility, default branch, tracked-file inventory, no unintended refs,
all mandatory CI phases with zero native/browser skips, durations, frozen-artifact
guard and release/restore evidence. Review logs for disclosure. A partial or failed
run is not hosted acceptance. No local history or historical screenshots may be
rewritten to absorb hosted outputs.

## Source-only versus binary/public release

The current notices prepare React-family and Ajv text, but dist/image packaging
still needs reviewed notice inclusion and native/base-image clearance. The
[license decision register](F5-D6-LICENSING-DECISIONS.md) records exact gates.
A private source upload, a passing CI run, root MIT selection, and public visibility
are four different decisions. Public visibility additionally needs final ownership,
notice, screenshot/privacy and repository-author metadata review. No binary/image
publication or broader external service authority follows from a source push.
