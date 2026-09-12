# 全分支處置與唯一前置接續線

Status: DOCUMENTATION_CONSOLIDATION / NOT_BLIND_PRODUCT_MERGE
遠端盤點包含原有13條分支與本次planning分支。精確原SHA保存在SOURCE_LOCK。此表記錄各自角色，不宣稱每一條未審code已通過或所有未來merge衝突已消失。

| Branch | Pin摘要 | 處置 |
|---|---|---|
| feature/mcf-01-static-module-contract | f0c0b986 | 保留產品源碼/已接受範圍的基線；本次文件由其接續，不改此ref |
| feature/g30-wp20-live-vendor-closure | f0c0b986 | 與產品錨點同SHA，保留歷史alias，不刪branch |
| feature/baseline-debt-01-deterministic-lifecycle-cleanup | 08d00294 | 已進f0lineage的歷史產品工作；保留其bounded接受，不重開舊任務 |
| feature/g24-g30-development-completion-routing | f34e6b29 | 原default/design-read歷史；不因default就取代本次planning入口 |
| architecture/modular-core-extension-contract | a985a081 | 模組設計来源；目前產品內MCF-01/ADR-MOD-013另有後續成果，保留source而非整條覆蓋 |
| architecture/mcf-02-external-runtime-routing | b317e5d7 | external contract/target提案保存exact原件；不單憑proposal宣告implementation接受 |
| feature/mcf-02-opencode-acp-runtime | 030890b3 | 待獨立review程式候選，F001–F005修復說明入reference；產品code未合併 |
| codex/track-a-formalization | 43aa27c8 | 正式Scope/PRD/SA/SD/決議/Identity/Human契約及TA-F4 receipt已選定保存；不覆寫f0最新產品狀態 |
| codex/ta-lr-01 | fe2eb231 | Frozen REV1/Freeze/Work Packages來源；部分為稀疏文件樹，不可作完整產品base |
| codex/ta-operating-model-r2 | 21f542d6 | 舊operating model/歷史來源，保留；本次以統一execution contract作後續routing，不活化舊GOAL |
| codex/review-package-skill-r2 | a9c6b4d4 | 既有tooling/歷史來源，沒有整庫覆蓋採用；需要helper時先確認accepted範圍 |
| governance/current | 1ea8ce3d | 跨機/角色/checkpoint語意繼承，過期95/100/IMPLEMENTING不帶入current state |
| governance/flowgov-adoption-poly | 1ea8ce3d | 同治理SHA的來源alias，保留不改 |
| planning/full-delivery-design-consolidation | 本輪發布receipt | 唯一前置文件/設計/功能scope整合線；讀本branch的AGENTS及docs/37，不使用舊source routing |

## 合併的實際意義

本次採用curated documentation integration：以f0 product tree為基礎，按原blob匯入各設計來源，補完整交付規格、單一routing及scope契約。新文件commit保持一條parent chain；不偽造merge parent表示從未做過的產品整合。

這能把Codex所需文件放在同一個checkout，避免開工時在多個不一致branch切換。原branches仍保留作追溯，不等於多個active Writer。沒有刪除、不force、不重寫歷史、不默默更改default或branch protection。平台目前未因此強制所有舊Agent停止，實機ownership仍須檢查。

真正MCF code integration是後續獨立審查的受控動作，若通過才合入指定產品integration checkpoint並驗新generation/ownership接口；不能以『所有整併』為由把未接受code宣稱accepted。已整合設計與待驗收程式的狀態分別顯示。

## 避免後續衝突

新任務指定exact planning/reviewed start SHA；不得預設clone的舊default就是當前基線。單一Writer依功能包序列修改共享檔；Alembic只從當前實際head向前、API/registry/identity合約一份；新候選review不可移用舊SHA PASS。Remote若偏離預期先停止寫入，保全差異；不checkout/reset user dirty工作樹來解決。

本次新增docs/37_CURRENT_ROUTING_INDEX.md是有意義的導航整併，寫入allowlist除原AGENTS/DELIVERY_START_HERE/docs/delivery外明列此檔。舊docs/11、12、ADR與original產品source仍保持原bytes/lineage；其舊Next文字不能自動開工。
