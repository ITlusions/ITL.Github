# Test registry

Generated from the `test_case` decorators in this folder. Regenerate with `tag-tests`.

## Legend

Each test has an ID in the form `TC-<AREA>-<NNN>`. `TC` is the tracking prefix, `AREA` is one of the codes below, and `NNN` numbers the tests of that area.

| Area | Name | Source files |
| --- | --- | --- |
| AUD | Exclusion audit | test_exclusion_audit.py |
| CFG | Chart .ciconfig settings | test_chart_config.py |
| COST | Pipeline cost estimate | test_pipeline_cost.py |
| CRR | Chart requirement runner | test_chart_requirements.py |
| DOC | Example page generation | test_example_docs.py |
| EXC | Chart exception files | test_chart_exceptions.py |
| HLM | Helm dependency handling | test_helm_client.py |
| KND | Kind test configuration | test_kind_config.py |
| KSC | Kubescape scanner | test_kubescape_scanner.py |
| KSR | Kubescape report reader | test_kubescape_report.py |
| LCK | Chart.lock checks | test_lock_check.py |
| REG | Test registry | test_registry.py |
| REQ | Chart requirements | test_requirements.py |
| SCL | Security CLI failure log | test_security_cli.py |
| SIG | Exception signatures | test_exception_signature.py |
| SUM | Security job summary | test_security_summary.py |
| TLC | Tool configuration | test_tool_config.py |
| TRV | Trivy scanner | test_trivy_scanner.py |

Each area has its own table below. **Title** is the behaviour the test checks, **File** is the test module and **Test** is the class and method name. **Scope** is CLI for the tests in this folder.

## Tests

### AUD - Exclusion audit

| ID | Scope | Title | File | Test |
| --- | --- | --- | --- | --- |
| TC-AUD-001 | CLI | An exclusion past its expiry date is reported as expired | test_exclusion_audit.py | ExclusionAuditTest.test_that_expired_exclusion_is_flagged_as_expired |
| TC-AUD-002 | CLI | An active exclusion expiring within thirty days is reported, and one expiring later is not | test_exclusion_audit.py | ExclusionAuditTest.test_that_exclusion_expiring_within_thirty_days_is_flagged |
| TC-AUD-003 | CLI | A Trivy exclusion whose misconfiguration no longer appears in the report is reported as stale | test_exclusion_audit.py | ExclusionAuditTest.test_that_trivy_exclusion_missing_from_unfiltered_report_is_stale |
| TC-AUD-004 | CLI | A Kubescape exclusion naming a control that the scan did not evaluate is reported as stale | test_exclusion_audit.py | ExclusionAuditTest.test_that_kubescape_exclusion_for_a_control_that_was_not_evaluated_is_stale |
| TC-AUD-005 | CLI | No stale issue is raised when the scanner report does not exist to compare against | test_exclusion_audit.py | ExclusionAuditTest.test_that_stale_check_is_skipped_when_the_scanner_report_is_missing |

### CFG - Chart .ciconfig settings

| ID | Scope | Title | File | Test |
| --- | --- | --- | --- | --- |
| TC-CFG-001 | CLI | A chart without .ciconfig leaves every setting empty so the workflow inputs apply | test_chart_config.py | ChartConfigTest.test_missing_ciconfig_writes_empty_outputs |
| TC-CFG-002 | CLI | Kind tests stay disabled for a chart whose .ciconfig does not enable them | test_chart_config.py | ChartConfigTest.test_kind_test_is_disabled_when_unset |
| TC-CFG-003 | CLI | Kind-test: true in .ciconfig is emitted as an enabled workflow output | test_chart_config.py | ChartConfigTest.test_kind_test_is_enabled_by_ciconfig |
| TC-CFG-004 | CLI | A non-boolean kind-test value fails instead of enabling tests by accident | test_chart_config.py | ChartConfigTest.test_kind_test_must_be_a_boolean |
| TC-CFG-005 | CLI | Every .ciconfig setting is emitted as a GitHub Actions output | test_chart_config.py | ChartConfigTest.test_ciconfig_settings_are_written_as_outputs |
| TC-CFG-006 | CLI | Trivy and kubescape both run for a chart whose .ciconfig does not set them | test_chart_config.py | ChartConfigTest.test_scanners_are_enabled_by_default |
| TC-CFG-007 | CLI | Trivy: false and kubescape: false in .ciconfig turn off the respective scanner | test_chart_config.py | ChartConfigTest.test_scanners_can_be_disabled_by_ciconfig |
| TC-CFG-008 | CLI | A non-boolean trivy value fails instead of silently leaving the scanner on | test_chart_config.py | ChartConfigTest.test_scanner_switch_must_be_a_boolean |
| TC-CFG-009 | CLI | A chart with trivy and kubescape both false is left out of the security-charts output | test_chart_config.py | ChartConfigTest.test_security_charts_skip_charts_with_both_scanners_off |
| TC-CFG-010 | CLI | A chart with only one scanner disabled still gets a security job | test_chart_config.py | ChartConfigTest.test_security_charts_keep_charts_with_one_scanner_on |
| TC-CFG-011 | CLI | An empty security-charts list is written when every affected chart opted out | test_chart_config.py | ChartConfigTest.test_security_charts_is_empty_when_nothing_is_scanned |
| TC-CFG-012 | CLI | A misspelled .ciconfig key fails instead of being silently ignored | test_chart_config.py | ChartConfigTest.test_unknown_key_is_rejected |
| TC-CFG-013 | CLI | Values-files must be a list of paths | test_chart_config.py | ChartConfigTest.test_values_files_must_be_a_list |

### COST - Pipeline cost estimate

| ID | Scope | Title | File | Test |
| --- | --- | --- | --- | --- |
| TC-COST-001 | CLI | The total rounds each finished job up to whole minutes and ignores skipped or running jobs | test_pipeline_cost.py | PipelineCostTest.test_that_total_bills_each_finished_job_in_whole_minutes_and_ignores_skipped_and_running_jobs |

### CRR - Chart requirement runner

| ID | Scope | Title | File | Test |
| --- | --- | --- | --- | --- |
| TC-CRR-001 | CLI | A chart meeting every shared requirement passes the runner | test_chart_requirements.py | ChartRequirementRunnerTest.test_complete_chart_passes |
| TC-CRR-002 | CLI | A chart whose README has too few words fails the runner | test_chart_requirements.py | ChartRequirementRunnerTest.test_short_readme_fails |

### DOC - Example page generation

| ID | Scope | Title | File | Test |
| --- | --- | --- | --- | --- |
| TC-DOC-001 | CLI | A chart's example page gets a dependency section with its graph before the minimal example | test_example_docs.py | ExampleDocsTest.test_inserts_dependency_section_before_the_minimal_example |
| TC-DOC-002 | CLI | Regenerating a page that is already current reports no change and keeps the file as it is | test_example_docs.py | ExampleDocsTest.test_second_run_without_changes_leaves_the_page_untouched |
| TC-DOC-003 | CLI | A new chart version replaces the old section, so the page matches the released version | test_example_docs.py | ExampleDocsTest.test_released_version_replaces_the_previous_section |
| TC-DOC-004 | CLI | The dependency table shows the version pinned in Chart.lock next to the declared one | test_example_docs.py | ExampleDocsTest.test_lock_file_shows_the_resolved_dependency_version |
| TC-DOC-005 | CLI | A chart without dependencies says so instead of showing an empty graph | test_example_docs.py | ExampleDocsTest.test_chart_without_dependencies_states_that_it_has_none |
| TC-DOC-006 | CLI | The base chart's section lists the charts that depend on it | test_example_docs.py | ExampleDocsTest.test_dependents_are_listed_as_users_of_the_chart |
| TC-DOC-007 | CLI | A chart without an example page raises instead of being skipped silently | test_example_docs.py | ExampleDocsTest.test_missing_example_page_fails_loudly |
| TC-DOC-008 | CLI | A page with neither section markers nor a minimal example heading raises | test_example_docs.py | ExampleDocsTest.test_page_without_insertion_point_fails_loudly |
| TC-DOC-009 | CLI | Check mode reports an out-of-date page and leaves the file unchanged | test_example_docs.py | ExampleDocsTest.test_check_mode_reports_change_without_writing |
| TC-DOC-010 | CLI | Custom prose around the generated section is kept when the chart version changes | test_example_docs.py | ExampleDocsTest.test_hand_written_text_outside_the_markers_survives_regeneration |
| TC-DOC-011 | CLI | A page carrying the manual marker is left exactly as written, even when the chart changed | test_example_docs.py | ExampleDocsTest.test_page_marked_as_manual_is_never_rewritten |
| TC-DOC-012 | CLI | Pages under a custom subfolder are never read or rewritten by the generator | test_example_docs.py | ExampleDocsTest.test_custom_pages_in_a_subfolder_are_not_touched |

### EXC - Chart exception files

| ID | Scope | Title | File | Test |
| --- | --- | --- | --- | --- |
| TC-EXC-001 | CLI | A chart without an exception file produces no Trivy or Kubescape exception input | test_chart_exceptions.py | ChartExceptionsTest.test_chart_without_exception_file_produces_no_inputs |
| TC-EXC-002 | CLI | The trivy section becomes a Trivy ignore file whose categories sit at the top level | test_chart_exceptions.py | ChartExceptionsTest.test_trivy_section_is_written_as_ignorefile_with_categories_at_top_level |
| TC-EXC-003 | CLI | The kubescape section becomes the JSON exception list Kubescape reads | test_chart_exceptions.py | ChartExceptionsTest.test_kubescape_section_is_written_as_json_exception_list |
| TC-EXC-004 | CLI | An exceptions.json in the chart root is used as the chart's exception file | test_chart_exceptions.py | ChartExceptionsTest.test_exception_file_in_chart_root_is_found_as_json |
| TC-EXC-005 | CLI | A chart with both a chart-root and a security-folder exception file fails instead of guessing | test_chart_exceptions.py | ChartExceptionsTest.test_two_exception_files_for_one_chart_are_rejected |
| TC-EXC-006 | CLI | The suppressed Trivy IDs can be looked up with their statement for the job summary | test_chart_exceptions.py | ChartExceptionsTest.test_trivy_statements_map_each_suppressed_id_to_its_statement |
| TC-EXC-007 | CLI | An exclusion missing its owner, expiry or request fails instead of being applied silently | test_chart_exceptions.py | ChartExceptionsTest.test_exclusion_without_owner_expiry_or_request_is_rejected |
| TC-EXC-008 | CLI | An exclusion whose expiry is not an ISO date fails the scan | test_chart_exceptions.py | ChartExceptionsTest.test_exclusion_with_invalid_expiry_date_is_rejected |
| TC-EXC-009 | CLI | An exclusion past its expiry no longer suppresses its finding and is reported as expired | test_chart_exceptions.py | ChartExceptionsTest.test_expired_exclusion_is_left_out_of_the_ignorefile_and_reported_as_expired |
| TC-EXC-010 | CLI | Every exclusion row carries its owner, expiry date and request for the job summary | test_chart_exceptions.py | ChartExceptionsTest.test_active_exclusion_reports_owner_expiry_and_request_for_the_summary |

### HLM - Helm dependency handling

| ID | Scope | Title | File | Test |
| --- | --- | --- | --- | --- |
| TC-HLM-001 | CLI | A Chart.lock in sync with Chart.yaml is used directly with helm dependency build | test_helm_client.py | HelmClientDependenciesTest.test_dependency_build_uses_lock_file_when_it_is_in_sync |
| TC-HLM-002 | CLI | A Chart.lock out of sync with Chart.yaml is regenerated with helm dependency update instead of failing | test_helm_client.py | HelmClientDependenciesTest.test_out_of_sync_lock_file_is_regenerated_with_dependency_update |
| TC-HLM-003 | CLI | A chart without Chart.lock resolves its dependencies with helm dependency update | test_helm_client.py | HelmClientDependenciesTest.test_missing_lock_file_falls_back_to_dependency_update |

### KND - Kind test configuration

| ID | Scope | Title | File | Test |
| --- | --- | --- | --- | --- |
| TC-KND-001 | CLI | Named kind-test scenarios become the matrix list of the workflow | test_kind_config.py | KindConfigTest.test_named_scenarios_are_emitted_as_matrix_output |
| TC-KND-002 | CLI | A scenario without its own values-files falls back to the chart values-files | test_kind_config.py | KindConfigTest.test_scenario_without_values_uses_chart_values_files |
| TC-KND-003 | CLI | A disabled kind-test still emits a non-empty matrix so GitHub accepts the workflow | test_kind_config.py | KindConfigTest.test_disabled_kind_test_emits_placeholder_scenario |
| TC-KND-004 | CLI | Two scenarios with the same name fail, since each name maps to one cluster | test_kind_config.py | KindConfigTest.test_duplicate_scenario_names_are_rejected |
| TC-KND-005 | CLI | Scenario names must be lowercase DNS-style labels | test_kind_config.py | KindConfigTest.test_invalid_scenario_name_is_rejected |
| TC-KND-006 | CLI | A prerequisite declares either a chart or manifests, not both or neither | test_kind_config.py | KindConfigTest.test_prerequisite_needs_exactly_one_source |
| TC-KND-007 | CLI | Kind-timeout must be a positive number of minutes | test_kind_config.py | KindConfigTest.test_kind_timeout_must_be_positive |
| TC-KND-008 | CLI | The kind plan creates the cluster, installs prerequisites, then the chart, then runs helm tests | test_kind_config.py | KindConfigTest.test_kind_scenario_plan_installs_prerequisites_before_chart |
| TC-KND-009 | CLI | The kind plan does not run helm test when the chart has no test hook | test_kind_config.py | KindConfigTest.test_helm_test_is_skipped_without_test_hooks |
| TC-KND-010 | CLI | A helm test hook in the chart templates is detected and a chart without one is not | test_kind_config.py | KindConfigTest.test_chart_with_test_hook_is_detected |
| TC-KND-011 | CLI | The dry-run plan creates and deletes the cluster under the name given on the command line | test_kind_config.py | KindConfigTest.test_kind_plan_uses_the_requested_cluster_name |
| TC-KND-012 | CLI | Kind-test --dry-run prints each planned command and does not touch the cluster | test_kind_config.py | KindConfigTest.test_dry_run_prints_plan_without_running_commands |
| TC-KND-013 | CLI | --keep-cluster and --cluster-name are available on kind-test for local debugging | test_kind_config.py | KindConfigTest.test_keep_cluster_flag_is_parsed |

### KSC - Kubescape scanner

| ID | Scope | Title | File | Test |
| --- | --- | --- | --- | --- |
| TC-KSC-001 | CLI | Kubescape runs with a high severity gate and writes its JSON report next to the chart reports | test_kubescape_scanner.py | KubescapeScannerTest.test_scan_blocks_on_high_severity_and_writes_json_report |
| TC-KSC-002 | CLI | A chart's Kubescape exception file is passed to Kubescape so its findings can be suppressed | test_kubescape_scanner.py | KubescapeScannerTest.test_scan_passes_chart_exception_file_when_present |
| TC-KSC-003 | CLI | A Kubescape exit code of 1 for failed controls does not fail the scan or record an error | test_kubescape_scanner.py | KubescapeScannerTest.test_findings_exit_code_is_not_a_scanner_failure |
| TC-KSC-004 | CLI | A Kubescape failure other than findings is recorded in the scan report and raised | test_kubescape_scanner.py | KubescapeScannerTest.test_other_exit_codes_are_recorded_and_raised |

### KSR - Kubescape report reader

| ID | Scope | Title | File | Test |
| --- | --- | --- | --- | --- |
| TC-KSR-001 | CLI | Passed controls are skipped and failed controls are listed with name and failed resource count | test_kubescape_report.py | KubescapeReportTest.test_that_only_failed_controls_are_returned_sorted_by_id |
| TC-KSR-002 | CLI | A control whose status is a plain string is read the same as a status object | test_kubescape_report.py | KubescapeReportTest.test_that_plain_string_status_is_read_as_failed |
| TC-KSR-003 | CLI | A missing report returns an empty list instead of failing the summary | test_kubescape_report.py | KubescapeReportTest.test_that_missing_report_has_no_failing_controls |

### LCK - Chart.lock checks

| ID | Scope | Title | File | Test |
| --- | --- | --- | --- | --- |
| TC-LCK-001 | CLI | A dependent whose Chart.lock pins an older local dependency version fails the check | test_lock_check.py | LockCheckTest.test_stale_lock_fails_the_check |
| TC-LCK-002 | CLI | A dependent whose Chart.lock pins the current local dependency version passes the check | test_lock_check.py | LockCheckTest.test_current_lock_passes_the_check |
| TC-LCK-003 | CLI | A dependent with local dependencies but no Chart.lock fails the check | test_lock_check.py | LockCheckTest.test_missing_lock_fails_the_check |
| TC-LCK-004 | CLI | A dependency from a remote repository is skipped because it cannot be verified offline | test_lock_check.py | LockCheckTest.test_remote_dependency_is_not_checked |
| TC-LCK-005 | CLI | Omitting the chart checks every non-ignored chart and fails on a stale dependent | test_lock_check.py | LockCheckTest.test_all_charts_are_checked_when_no_chart_is_given |

### REG - Test registry

| ID | Scope | Title | File | Test |
| --- | --- | --- | --- | --- |
| TC-REG-001 | CLI | Every tracking ID follows the TC-<AREA>-<NNN> pattern | test_registry.py | TestRegistryTest.test_every_tracked_id_has_the_expected_format |
| TC-REG-002 | CLI | Each tracking ID belongs to exactly one test across the suite | test_registry.py | TestRegistryTest.test_no_tracking_id_is_used_twice |
| TC-REG-003 | CLI | Each tracked test has a non-empty title for the registry | test_registry.py | TestRegistryTest.test_every_tracked_test_has_a_title |

### REQ - Chart requirements

| ID | Scope | Title | File | Test |
| --- | --- | --- | --- | --- |
| TC-REQ-001 | CLI | README.md with the minimum word count passes | test_requirements.py | RequirementsTest.test_chart_with_long_enough_readme_passes |
| TC-REQ-002 | CLI | README.md one word below the minimum fails | test_requirements.py | RequirementsTest.test_readme_one_word_short_fails |
| TC-REQ-003 | CLI | Missing README.md at the chart root fails | test_requirements.py | RequirementsTest.test_missing_readme_fails |
| TC-REQ-004 | CLI | README.md in a subfolder does not satisfy the requirement | test_requirements.py | RequirementsTest.test_readme_in_a_subfolder_does_not_count |
| TC-REQ-005 | CLI | Chart marked with .ciignore is excluded from the README rule | test_requirements.py | RequirementsTest.test_ignored_chart_needs_no_readme |

### SCL - Security CLI failure log

| ID | Scope | Title | File | Test |
| --- | --- | --- | --- | --- |
| TC-SCL-001 | CLI | Every failed control is logged with its ID, name and failed resource count | test_security_cli.py | SecurityCliFailureLogTest.test_that_each_failed_control_is_logged_in_plain_words |
| TC-SCL-002 | CLI | Scans other than a chart scan do not read a Kubescape report | test_security_cli.py | SecurityCliFailureLogTest.test_that_non_chart_commands_log_no_controls |
| TC-SCL-003 | CLI | A chart scan without a Kubescape report logs nothing and does not raise | test_security_cli.py | SecurityCliFailureLogTest.test_that_missing_report_logs_no_controls |

### SIG - Exception signatures

| ID | Scope | Title | File | Test |
| --- | --- | --- | --- | --- |
| TC-SIG-001 | CLI | The sigstore bundle is named after the exception file it signs | test_exception_signature.py | ExceptionSignatureVerifierTest.test_bundle_sits_next_to_the_exception_file |
| TC-SIG-002 | CLI | An exception file without a signature bundle is never loaded when verification is enabled | test_exception_signature.py | ExceptionSignatureVerifierTest.test_exception_file_without_bundle_is_rejected |
| TC-SIG-003 | CLI | Exception files load without any signature check when verification is not enabled | test_exception_signature.py | ExceptionSignatureVerifierTest.test_unsigned_exception_file_loads_when_verification_is_off |

### SUM - Security job summary

| ID | Scope | Title | File | Test |
| --- | --- | --- | --- | --- |
| TC-SUM-001 | CLI | A chart summary shows which scanners ran and passed, and which were skipped | test_security_summary.py | SecuritySummaryTest.test_that_chart_summary_reports_passed_and_skipped_scanners |
| TC-SUM-002 | CLI | Each failed control at the blocking severity is shown as a warning annotation on the run | test_security_summary.py | SecuritySummaryTest.test_that_blocking_kubescape_findings_become_warning_annotations |
| TC-SUM-003 | CLI | An exclusion that expires within thirty days is shown as a warning annotation on the run | test_security_summary.py | SecuritySummaryTest.test_that_exclusion_expiring_soon_becomes_a_warning_annotation |
| TC-SUM-004 | CLI | A failed scanner is marked as failed and its error appears in the summary | test_security_summary.py | SecuritySummaryTest.test_that_chart_summary_reports_failed_scanner_and_lists_errors |
| TC-SUM-005 | CLI | The chart summary names each failed Kubescape control with its failed resource count | test_security_summary.py | SecuritySummaryTest.test_that_chart_summary_lists_failed_kubescape_controls |
| TC-SUM-006 | CLI | Gitleaks findings appear with file and rule, and the scan exit error is hidden | test_security_summary.py | SecuritySummaryTest.test_that_secret_summary_lists_findings_without_secret_values |
| TC-SUM-007 | CLI | Each pip-audit vulnerability is listed with its package, version and fix versions | test_security_summary.py | SecuritySummaryTest.test_that_dependency_summary_lists_each_vulnerability_with_fix_versions |
| TC-SUM-008 | CLI | The default layout keeps the failing controls table and does not list exclusions | test_security_summary.py | SecuritySummaryTest.test_that_classic_layout_is_the_default_and_lists_only_failing_controls |
| TC-SUM-009 | CLI | The flat layout shows blocking, excluded and expired findings in one table | test_security_summary.py | SecuritySummaryTest.test_that_flat_layout_lists_every_finding_with_status_owner_and_request |
| TC-SUM-010 | CLI | The sections layout writes one table per status | test_security_summary.py | SecuritySummaryTest.test_that_sections_layout_separates_blocking_excluded_and_expired_findings |
| TC-SUM-011 | CLI | The counts layout shows one count per status and lists only the blocking findings | test_security_summary.py | SecuritySummaryTest.test_that_counts_layout_shows_how_many_findings_have_each_status |
| TC-SUM-012 | CLI | The expiry layout lists the earliest expiring exclusion first and counts days left | test_security_summary.py | SecuritySummaryTest.test_that_expiry_layout_sorts_exclusions_by_expiry_date_with_days_left |
| TC-SUM-013 | CLI | A layout name that is not one of the five layouts fails before anything is written | test_security_summary.py | SecuritySummaryTest.test_that_unknown_layout_name_is_rejected |
| TC-SUM-014 | CLI | The setup and repository steps do not write a job summary | test_security_summary.py | SecuritySummaryTest.test_that_steps_without_summary_write_nothing |

### TLC - Tool configuration

| ID | Scope | Title | File | Test |
| --- | --- | --- | --- | --- |
| TC-TLC-001 | CLI | The packaged config.yaml loads every tool the pipelines install | test_tool_config.py | ToolConfigTest.test_packaged_config_pins_all_tools |
| TC-TLC-002 | CLI | A well-formed tools mapping yields one Download per tool | test_tool_config.py | ToolConfigTest.test_valid_entry_is_returned_as_download |
| TC-TLC-003 | CLI | Config.yaml rejects any top-level key other than tools | test_tool_config.py | ToolConfigTest.test_unknown_top_level_key_is_rejected |
| TC-TLC-004 | CLI | Config.yaml without a tools mapping is rejected | test_tool_config.py | ToolConfigTest.test_missing_tools_key_is_rejected |
| TC-TLC-005 | CLI | Each tool needs both url and sha256 | test_tool_config.py | ToolConfigTest.test_entry_missing_a_key_is_rejected |
| TC-TLC-006 | CLI | Tool downloads must use https | test_tool_config.py | ToolConfigTest.test_http_url_is_rejected |
| TC-TLC-007 | CLI | A sha256 that is not 64 lowercase hexadecimal characters is rejected | test_tool_config.py | ToolConfigTest.test_short_digest_is_rejected |
| TC-TLC-008 | CLI | The sha256 must be written in lowercase hexadecimal | test_tool_config.py | ToolConfigTest.test_uppercase_digest_is_rejected |

### TRV - Trivy scanner

| ID | Scope | Title | File | Test |
| --- | --- | --- | --- | --- |
| TC-TRV-001 | CLI | Every CRITICAL and HIGH CVE is written with its package, versions and title, critical first | test_trivy_scanner.py | TrivyVulnerabilityReportTest.test_report_lists_critical_before_high_cves_with_details |
| TC-TRV-002 | CLI | The CVE table with severity, CVE, package and fixed version appears in the job summary | test_trivy_scanner.py | TrivyVulnerabilityReportTest.test_cve_table_is_added_to_job_summary |
| TC-TRV-003 | CLI | An image without scan output yields an empty CVE report and no job summary table | test_trivy_scanner.py | TrivyVulnerabilityReportTest.test_missing_reports_produce_empty_report_and_no_table |
