param(
    [string]$ProjectId    = "PVT_kwDOCrDQnc4BXTjM",
    [string]$WorkTypeFieldId = "PVTSSF_lADOCrDQnc4BXTjMzhShQiY"
)

# Work Type option IDs
$WT_EPIC  = "4008acda"
$WT_STORY = "b700cb58"
$WT_TASK  = "44372b67"
$WT_BUG   = "8541539f"

$mutSSF = 'mutation($pid: ID!, $iid: ID!, $fid: ID!, $oid: String!) { updateProjectV2ItemFieldValue(input: { projectId: $pid, itemId: $iid, fieldId: $fid, value: { singleSelectOptionId: $oid } }) { projectV2Item { id } } }'

# Load project item IDs
$itemsData = gh project item-list 35 --owner ITlusions --format json --limit 50 | ConvertFrom-Json
$itemMap = @{}
foreach ($item in $itemsData.items) {
    $n = $item.content.number
    if ($n) { $itemMap[[int]$n] = $item.id }
}

# Work Type classification
# Epic:  top-level theme umbrella
# Story: user/operator-visible security capability
# Task:  pure technical implementation / infrastructure / cleanup
# Bug:   code defect with incorrect or missing behaviour
$types = @{
    5  = $WT_EPIC

    # Bugs
    1  = $WT_BUG   # header-sniffing instead of real X.509 parse
    2  = $WT_BUG   # EK bypass — registration without any EK material
    4  = $WT_BUG   # EK fingerprint not cross-checked in enrollment cert
    13 = $WT_BUG   # timing oracle in admin token comparison
    17 = $WT_BUG   # ek_fingerprint validator hardcodes SHA-256 length
    18 = $WT_BUG   # ek_cert_pem field accepts empty string

    # Stories — security capabilities added for operators/auditors
    3  = $WT_STORY  # manufacturer CA chain verification
    6  = $WT_STORY  # TPM Quote + PCR policy verification
    7  = $WT_STORY  # nonce-based replay protection on /attest
    8  = $WT_STORY  # algorithm hardening ECDSA P-384 / SHA-384
    9  = $WT_STORY  # per-operator identity + dual-control
    10 = $WT_STORY  # cryptographically chained audit log
    11 = $WT_STORY  # EK-bound AES-256-GCM config encryption
    12 = $WT_STORY  # CNSA 1.0 alignment + PQC roadmap
    15 = $WT_STORY  # config token expiry enforcement
    16 = $WT_STORY  # PKCS#11 HSM for CA private key
    20 = $WT_STORY  # CRL / certificate revocation

    # Tasks — technical implementation steps, no direct user-visible behaviour
    14 = $WT_TASK   # persist ek_cert_pem in MachineRow (prerequisite for #11)
    19 = $WT_TASK   # remove/stub dead PCR fields in AttestRequest
    21 = $WT_TASK   # rate limiting on public endpoints
    22 = $WT_TASK   # migrate from SQLite to PostgreSQL
}

$labels = @{ $WT_EPIC="Epic"; $WT_STORY="Story"; $WT_TASK="Task"; $WT_BUG="Bug" }
$ok = 0; $err = 0

foreach ($n in ($types.Keys | Sort-Object)) {
    $iid = $itemMap[$n]
    $oid = $types[$n]

    if (-not $iid) { Write-Host "SKIP #$n (not on board)" -ForegroundColor Yellow; continue }

    $r = gh api graphql -f query="$mutSSF" -f pid="$ProjectId" -f iid="$iid" -f fid="$WorkTypeFieldId" -f oid="$oid" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "#$n [$($labels[$oid])] OK" -ForegroundColor Green
        $ok++
    } else {
        Write-Host "#$n [$($labels[$oid])] ERR: $r" -ForegroundColor Red
        $err++
    }
}

Write-Host ""
Write-Host "Done: $ok OK, $err ERR" -ForegroundColor $(if ($err -eq 0) { "Green" } else { "Yellow" })
