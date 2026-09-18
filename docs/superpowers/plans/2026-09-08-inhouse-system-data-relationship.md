# In-House Manufacturing System Data Relationship Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create introductory and data-contract documentation that explains the Mock MES, QMS Lakehouse, and FDC Eventhouse integration used by the manufacturing scenario.

**Architecture:** `labs/01-inhouse-system/README.md` explains the business purpose and end-to-end integration. `labs/01-inhouse-system/data-relationship.md` owns key mappings, time-axis constraints, and the three-stage FDC investigation flow so the overview remains skimmable.

**Tech Stack:** Markdown, Mermaid diagrams, existing workshop helper documentation.

## Global Constraints

- Write participant-facing content in Korean; keep product, API, and code identifiers in their original spelling.
- Use verified Mock MES, QMS, and FDC facts only; do not invent Fabric item names or sample data.
- Keep the documents limited to the in-house manufacturing scenario and refer participants to Fabric IQ for implementation detail.
- Validate three Mermaid diagrams and all local relative Markdown links after editing.

---

### Task 1: Write the System Overview

**Files:**
- Create: `labs/01-inhouse-system/README.md`

**Interfaces:**
- Consumes: Mock MES public site capabilities; QMS and FDC helper documentation.
- Produces: A participant-facing entry point linked by `data-relationship.md` and the Fabric helper guides.

- [x] **Step 1: Write the overview document**

Include these sections in Korean:

```markdown
# 사내 제조 시스템 개요

## 이 시나리오에서 풀 문제
## 세 시스템의 역할
## 시스템 연계도
## 이 핸즈온의 목표
## 다음 단계
```

The system diagram must show Mock MES as the operational source, QMS in Fabric Lakehouse and FDC in Fabric Eventhouse as separate systems, and Foundry IQ consuming MES MCP plus a Fabric Data Agent. State that `fabriccjmenufacturing` is a verified Central US F2 Fabric Capacity, without inferring Fabric item names.

- [x] **Step 2: Run a focused structure check**

Run:

```bash
ruby -e 'path = "labs/01-inhouse-system/README.md"; text = File.read(path); required = ["```mermaid", "Mock MES", "Lakehouse", "Eventhouse", "Foundry IQ", "fabriccjmenufacturing", "data-relationship.md"]; missing = required.reject { |term| text.include?(term) }; abort("Missing: #{missing.join(", ")}") unless missing.empty?; puts "Overview structure validation passed"'
```

Expected: `Overview structure validation passed`.

### Task 2: Write the Data Relationship Guide

**Files:**
- Create: `labs/01-inhouse-system/data-relationship.md`

**Interfaces:**
- Consumes: The overview and existing Lakehouse/FDC helper documentation.
- Produces: The detailed explanation linked from the overview.

- [x] **Step 1: Write the data relationship document**

Include a system-of-record table, an entity/relationship Mermaid diagram using `lot_id`, `product_code`, `step_code`, `material_code`, `eqp_id`, and process time ranges, and a second Mermaid diagram for FDC → MES → QMS analysis. Explain that FDC deliberately has no `lot_id`, there are no database foreign keys, and QMS/FDC must be seeded against the same MES time axis.

- [x] **Step 2: Run the complete documentation check**

Run:

```bash
ruby -e 'paths = ["labs/01-inhouse-system/README.md", "labs/01-inhouse-system/data-relationship.md"]; text = paths.to_h { |path| [path, File.read(path)] }; abort("Expected 3 Mermaid diagrams") unless text.values.sum { |value| value.scan(/```mermaid/).size } == 3; required = %w[lot_id product_code step_code material_code eqp_id]; missing = required.reject { |term| text.fetch(paths.last).include?(term) }; abort("Missing data key: #{missing.join(", ")}") unless missing.empty?; links = text.values.flat_map { |value| value.scan(/\[[^\]]+\]\(([^)#]+)(?:#[^)]+)?\)/).flatten }; broken = links.reject { |link| link.start_with?("http") || File.exist?(File.expand_path(link, "labs/01-inhouse-system")) || File.exist?(File.expand_path(link, "docs/superpowers")) }; abort("Broken local links: #{broken.join(", ")}") unless broken.empty?; puts "In-house documentation validation passed"'
```

Expected: `In-house documentation validation passed`.