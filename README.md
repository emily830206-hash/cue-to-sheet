# CueToSheet

這個工具會把 cue CSV 轉成可貼到 Google Sheet 的兩列資料。

## 如何產出分享檔

1. 到 GitHub repo 的 `Actions`。
2. 點選 `Build CueToSheet apps`。
3. 點 `Run workflow`。
4. 等流程跑完後，進入最新一次 workflow run。
5. 在 `Artifacts` 下載需要的版本。

## 下載哪個版本

- Windows 同事：下載 `CueToSheet_Windows`，解壓縮後雙擊 `start_cue_tool.exe`。
- Mac M1/M2/M3/M4 同事：下載 `CueToSheet_Mac_AppleSilicon`，解壓縮後打開 `CueToSheet.app`。
- Intel Mac 同事：下載 `CueToSheet_Mac_Intel`，解壓縮後打開 `CueToSheet.app`。

## macOS 安全性提醒

這是內部自製工具，沒有 Apple Developer 簽章。Mac 第一次開啟時可能會被系統擋下。

可請同事用右鍵點 `CueToSheet.app`，選擇「打開」，再按確認。

如果 macOS 顯示 app 已損毀或無法打開，可請同事打開「終端機」，執行以下指令後再開一次：

```bash
xattr -dr com.apple.quarantine /Applications/CueToSheet.app
```

如果 app 是放在下載資料夾，請把 `/Applications/CueToSheet.app` 改成實際位置，例如：

```bash
xattr -dr com.apple.quarantine ~/Downloads/CueToSheet.app
```

## 日期格式

日期區間會輸出為 `mmdd-mmdd`，例如 `0701-0715`。
