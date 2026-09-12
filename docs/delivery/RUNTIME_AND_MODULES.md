# Runtime、模組化與真實整合設計

Status: DESIGN_DRAFT。原定Codex/OpenCode深度Runtime、Local endpoints與Web層都保留；MCF-02第一個external target及其限制不能被偷換成完整產品完成。

## 1. Reuse而非重造

Static ModuleManifest/ModuleRegistry→RuntimeModuleBridge→既有RuntimeProfile/RuntimeRegistry→Run-owned immutable RuntimeBindingSnapshot→RuntimeAdapter→RunSupervisor。Core不分散vendor if/else。Module只供metadata/factory/capability；不能自宣告VERIFIED/CERTIFIED或產生Human approval。

RUNTIME/TOOL/SURFACE/INTEGRATION名詞只有實作contract與evidence存在才可標support；descriptor vocabulary不是完整plugin功能。MEMORY、remote install、hot reload等仍依原future範圍，不藉此新建plugin平台。

## 2. Target evidence profile

每target保存：provider/runtime/adapter identity與版本、executable/content digest、protocol/contract版本、auth ownership、實際config來源與resolved fingerprint、model identity可見性、capability宣告、conformance結果、host/browser、fixture/live、證據時間及scope。

Codex/OpenCode既有deterministic adapters保留，不以改名或maturity旗標升成live。聲稱深度支援需真實create/submit/cwd/change/status/result/error/cancel/timeout/cleanup/artifacts/version及可用resume範圍證據。NATIVE不支援可為NONE或有證據的MANAGED，但不能假resume。

Local LM Studio/Ollama/Generic compatible按Endpoint+Model宣告能力。Server接受同步HTTP後，本地停止等待不能證明遠端運算已取消；cleanup/cancel不確定如實報告。Web另走MV3/confirmed send/fallback，不當成official API或native Runtime捷徑。

## 3. MCF-02候選整合

`030890b3...`列待獨立審查，不由本次文件改寫為accepted。F001–F005包含Run-scoped staging/envelope、effective config、scoped Core policy、disabled permission callback、quiescence後Core-owned artifact import。實作/修復報告與測試數只是候選材料。

開發群先比較候選對新generation/lineage/ownership/Candidate設計的影響。能重用且已通獨立檢核的部分引用exact SHA；不重做，亦不整條無條件merge。

MCF proposal的PRIMARY為OpenCode ACP、BACKUP為Gemini CLI ACP；第一個slice不同时做兩個production targets。這不刪除完整初版的Codex深度目標。是否啟用backup或增target需要同一執行契約明列的target gate，不由名字推斷授權。

## 4. Envelope / staging sequence

每Run建立新的staging與isolated config scope；只投影已批准context與files。不得默認使用Human project root、parent/global home、plugins/MCP/remote skills。用bound executable檢查版本與實際resolved config來源，與Core-approved期望/permissions/egress一致才可launch。

含未知字段/來源、binary hash變化、scope替換、implicit provider/model或permissive expansion都not-ready；resolver raw輸出只在受控memory內解析，不進Evidence。環境未支持平台的managed sources則明確unsupported，不假等價。

Binding在副作用前commit；envelope與actual Run/Task/Project/destination关联，不把profile級shared準備物重用到不同Run。Core policy允許其本身允許的route；APPROVAL_REQUIRED不能因附policy ref而變ALLOW，更不變Human-approved。

## 5. 寫入能力與可用性Gate

deny-all fixture可證明拒絕邊界，不能證明真實bug fix可完成。要啟用必要工具/檔案修改，必須先確認runtime是否有受控file/process mediation、workspace scope、plugin/config閉包及可驗的permission決定。若需擴張原MCF信任/公開契約，先architecture/security change control；不得直接把全部permission設allow。

可行性試驗在專用synthetic repo與明列測試auth/egress範圍執行，不碰Human repo。須同時證明：允許scope內真改碼成功、scope外/未批准tool拒絕、cancel/timeout停止owned工作、輸出可由Core接收且不泄secret。永遠拒絕所有操作與放行所有操作都不是完成。

## 6. Artifact lifecycle與失敗

Supervisor證明owned工作quiescent後，Core對output檔案做containment、大小/內容hash、必要重讀與symlink/替換防護，建立自己的不可變copy，再寫metadata及Candidate snapshot。Staging不是長期artifact store，後續staging變動不影響已發布內容。

Raw runtime成功文字不是Verified evidence；合法Finding/Artifact/Evidence payload須經redaction與normalization。Malformed stream、unsupported request、stale session、mixed request/response ID、cleanup failure、process崩潰、partial output都fail closed，不能默默換target或重綁既有Run。

## 7. 模組替換驗收

在同一Core task/workflow contract下使用至少兩個已核准的runtime註冊，替換不需修改Core vendor branch，不改歷史binding/Run/Candidate身份。對duplicate ID、unknown version/capability、unavailable factory、policy拒絕、配置drift、module故障做負例。能力/maturity依每個target的實際evidence，不把一個target的PASS擴張到所有模組。
