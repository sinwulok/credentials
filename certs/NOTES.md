
## 結構 / Repository structure
- `README.md` — 本文件（中英混合）  
- `certs/` — 每張憑證一個 Markdown 檔，YAML frontmatter 包含 title、issuer、date、verification_url、credential_id（或其 hash）、image、tags、summary  
- `assets/thumbnails/` — 憑證縮圖（已去識別化）  
- `docs/` — (選用) GitHub Pages 靜態站點內容  
- `LICENSE` — 權利聲明（All rights reserved）

---

## 如何新增憑證 / How to add a certificate
1. 在 `certs/` 新增 Markdown 檔，參考 `certs/EXAMPLE.md` 的 frontmatter 格式。  
2. 將縮圖上傳至 `assets/thumbnails/`（勿包含完整個人資料或敏感文字）。  
3. 建議在 PR 描述中附上官方的驗證連結（verification_url）。  
4. 若憑證含敏感資訊，請勿直接上傳完整檔；改放私有儲存並僅於 README 或 cert 的 metadata 中放驗證連結或 hash。  

---
