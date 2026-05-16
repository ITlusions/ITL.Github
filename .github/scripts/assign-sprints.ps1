param(
    [string]$ProjectId   = "PVT_kwDOCrDQnc4BXTjM",
    [string]$SprintFieldId = "PVTSSF_lADOCrDQnc4BXTjMzhSzkBM"
)

$mutSSF = 'mutation($pid: ID!, $iid: ID!, $fid: ID!, $oid: String!) { updateProjectV2ItemFieldValue(input: { projectId: $pid, itemId: $iid, fieldId: $fid, value: { singleSelectOptionId: $oid } }) { projectV2Item { id } } }'

# --- Load Sprint option IDs ---
$fieldsQ = 'query($pid: ID!) { node(id: $pid) { ... on ProjectV2 { fields(first: 30) { nodes { ... on ProjectV2SingleSelectField { id name options { id name } } } } } } }'
$fieldsData = gh api graphql -f query="$fieldsQ" -f pid="$ProjectId" | ConvertFrom-Json
$sprintOpts = @{}
$fieldsData.data.node.fields.nodes | Where-Object { $_.name -eq "Sprint" } | ForEach-Object {
    $_.options | ForEach-Object { $sprintOpts[$_.name] = $_.id }
}

Write-Host "Sprint options: $($sprintOpts.Keys -join ', ')"

# --- Load project item IDs ---
$itemsData  = gh project item-list 35 --owner ITlusions --format json --limit 50 | ConvertFrom-Json
$itemMap    = @{}
foreach ($item in $itemsData.items) {
    $num = $item.content.number
    if ($num) { $itemMap[[int]$num] = $item.id }
}

# --- Sprint assignments ---
$assignments = @(
    # Sprint 1 — Critical/High, XS/S, no protocol changes
    @{ Issue = 1;  Sprint = "Sprint 1" },
    @{ Issue = 2;  Sprint = "Sprint 1" },
    @{ Issue = 4;  Sprint = "Sprint 1" },
    @{ Issue = 13; Sprint = "Sprint 1" },
    @{ Issue = 18; Sprint = "Sprint 1" },
    # Sprint 2 — Protocol & schema hardening
    @{ Issue = 7;  Sprint = "Sprint 2" },
    @{ Issue = 15; Sprint = "Sprint 2" },
    @{ Issue = 17; Sprint = "Sprint 2" },
    @{ Issue = 19; Sprint = "Sprint 2" },
    # Sprint 3 — Data model & infrastructure
    @{ Issue = 14; Sprint = "Sprint 3" },
    @{ Issue = 21; Sprint = "Sprint 3" },
    @{ Issue = 22; Sprint = "Sprint 3" },
    # Sprint 4 — Advanced security
    @{ Issue = 3;  Sprint = "Sprint 4" },
    @{ Issue = 10; Sprint = "Sprint 4" },
    @{ Issue = 11; Sprint = "Sprint 4" },
    # Sprint 5 — Cryptography & identity
    @{ Issue = 8;  Sprint = "Sprint 5" },
    @{ Issue = 9;  Sprint = "Sprint 5" },
    @{ Issue = 12; Sprint = "Sprint 5" },
    @{ Issue = 16; Sprint = "Sprint 5" },
    # Sprint 6 — Full remote attestation
    @{ Issue = 6;  Sprint = "Sprint 6" },
    @{ Issue = 20; Sprint = "Sprint 6" }
)

$ok = 0; $err = 0
foreach ($a in $assignments) {
    $n      = $a.Issue
    $sprint = $a.Sprint
    $iid    = $itemMap[$n]
    $oid    = $sprintOpts[$sprint]

    if (-not $iid) { Write-Host "SKIP #$n (not on board)" -ForegroundColor Yellow; continue }
    if (-not $oid) { Write-Host "SKIP #$n ($sprint option not found)" -ForegroundColor Yellow; continue }

    $r = gh api graphql -f query="$mutSSF" -f pid="$ProjectId" -f iid="$iid" -f fid="$SprintFieldId" -f oid="$oid" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "#$n -> $sprint : OK" -ForegroundColor Green
        $ok++
    } else {
        Write-Host "#$n -> $sprint : ERR $r" -ForegroundColor Red
        $err++
    }
}

Write-Host ""
Write-Host "Done: $ok OK, $err ERR" -ForegroundColor $(if ($err -eq 0) {"Green"} else {"Yellow"})
