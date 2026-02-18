# Security & Privacy Analysis for credentials Repository

**Analysis Date:** 2026-02-18  
**Repository:** https://github.com/sinwulok/credentials

---

## Executive Summary

This document analyzes what information can be read from the `sinwulok/credentials` repository through three main access points:
1. **GitHub Repository:** https://github.com/sinwulok/credentials
2. **GitHub Pages Site:** https://sinwulok.github.io/credentials/
3. **GitHub Deployments:** https://github.com/sinwulok/credentials/deployments/github-pages

---

## 1. What Can Be Read from the GitHub Repository

### 1.1 Public Repository Contents

The following information is **publicly accessible** to anyone visiting the repository:

#### Source Code & Configuration
- **Workflows (`.github/workflows/`)**: Complete CI/CD pipeline configurations
  - `deploy-from-private-files.yml` - Shows the deployment process
  - `generate-thumbnails-index.yml` - Thumbnail generation workflow
  - `ingest-data.yml` - Data ingestion workflow
- **Scripts (`scripts/`)**: Python scripts for data processing
  - `ingest_private_files.py` - Data ingestion logic
  - `generate_thumbnails_and_redact.py` - Thumbnail generation and redaction
- **Documentation**: 
  - `README.md` - Public-facing documentation
  - `certs/NOTES.md` - Repository structure documentation
  - `certs/EXAMPLE.md` - Example credential format

#### Repository Metadata
- Commit history and messages
- Branch names and structure
- Contributors and authorship information
- Issue and pull request history (if any)
- License information (All Rights Reserved)

#### Configuration Files
- `.gitignore` - Shows which files are excluded from version control
- `requirements.txt` - Python dependencies

### 1.2 Information NOT Publicly Accessible from Repository

The repository is designed to **protect sensitive information**:

- ❌ **Original PDF certificates** - Not stored in public repository
- ❌ **Full personal information** - Redacted from public view
- ❌ **Private credential files** - Stored in separate private repository
- ❌ **Sensitive identifiers** - Hashed or removed from public data
- ❌ **Workflow secrets** - `PRIVATE_FILES_REPO` and `PRIVATE_REPO_PAT` are encrypted

### 1.3 Architectural Security Insights

From the workflow files, we can infer:

1. **Private Repository Integration**: The system uses a separate private repository to store actual credentials
   - Environment variable: `PRIVATE_FILES_REPO` (stored as secret)
   - Access token: `PRIVATE_REPO_PAT` (stored as secret)
   - Private files are checked out during build but NOT committed to public repo

2. **Data Processing Pipeline**:
   ```
   Private Repo → Checkout → Process → Generate Thumbnails → Redact → Deploy to Pages
   ```

3. **Expected Directory Structure** (from workflows):
   - `private-files/credentials/` - Descriptive metadata (JSON/CSV/TSV)
   - `private-files/` - Original PDF files
   - `docs/assets/thumbnails/` - De-identified thumbnails (public)
   - `docs/data/` - Processed credential metadata (public)

---

## 2. What Can Be Read from GitHub Pages

### 2.1 Current State

**URL:** https://sinwulok.github.io/credentials/

#### Available Pages
- `index.html` - Main thumbnails gallery page
- `gallery.html` - Alternative thumbnail gallery view
- `styles.css` - Styling (if generated)

#### Page Functionality

**Index Page (`index.html`):**
- Loads thumbnail images from `./assets/thumbnails/`
- Reads `./assets/thumbnails/index.json` for list of files
- Displays message: "已自動產生的 PDF 縮圖（檔名為雜湊以保護原始檔名）"
  - Translation: "Automatically generated PDF thumbnails (filenames are hashed to protect original names)"
- Currently shows: "載入縮圖中…" (Loading thumbnails...)

**Gallery Page (`gallery.html`):**
- Similar functionality to index.html
- Minimal design with grid layout
- Note: "Filenames are hashed for privacy"

### 2.2 Data Accessible via GitHub Pages

Currently, the GitHub Pages site can expose:

#### If Deployment Succeeds:
- ✅ **Thumbnail images** - De-identified images of credentials
  - Files stored in `docs/assets/thumbnails/`
  - Filenames are hashed (e.g., `a1b2c3d4e5.png`)
  - Personal information should be redacted from images
- ✅ **Thumbnail index** - List of thumbnail filenames
  - File: `docs/assets/thumbnails/index.json`
  - Contains array of filenames only
- ✅ **Credential metadata** - Processed credential information
  - Files: `docs/data/credentials.json`, `credentials_index.json`, `credentials_by_id.json`
  - Contains: title, issuer, date, verification URLs, tags, etc.
  - Should NOT contain: sensitive personal data, full credential IDs

#### Current State (Empty):
- ⚠️ **No thumbnails currently deployed**
  - `assets/thumbnails/` contains only `.gitkeep`
  - No actual image files present
- ⚠️ **No credential data currently deployed**
  - No `docs/data/` directory exists yet
  - No `credentials.json` or related files

### 2.3 Privacy Controls in GitHub Pages

The deployment process includes:

1. **Filename Hashing**: Original filenames are hashed to prevent identification
2. **Redaction**: `generate_thumbnails_and_redact.py` applies redaction patterns
3. **Metadata Filtering**: Only approved fields are included in public JSON
4. **Terms of Use**: README explicitly states content is for viewing only

---

## 3. What Can Be Read from GitHub Deployments Page

### 3.1 Deployment Information

**URL:** https://github.com/sinwulok/credentials/deployments/github-pages

This page shows:

#### Deployment History
- **Deployment timestamps** - When each deployment occurred
- **Deployment status** - Success, failure, or in-progress
- **Deployment environment** - "github-pages"
- **Branch deployed** - Which branch triggered the deployment
- **Commit SHA** - Which commit was deployed
- **Workflow run links** - Links to the workflow that created the deployment

#### Metadata Visible:
- Number of deployments
- Deployment frequency
- Success/failure patterns
- Associated workflow runs

### 3.2 Information NOT Available

- ❌ **Deployment artifacts** - Actual files deployed are not directly downloadable from this page
- ❌ **Workflow secrets** - Secret values remain encrypted
- ❌ **Private repository contents** - Private files referenced in workflows are not exposed

---

## 4. Security Assessment

### 4.1 Strengths

✅ **Separation of Concerns**
- Public repository contains NO sensitive files
- Private repository keeps original certificates secure
- Build-time processing ensures redaction before publication

✅ **Privacy by Design**
- Filename hashing prevents tracking
- Redaction patterns remove personal information
- Metadata is filtered to include only public-facing information

✅ **Access Control**
- Workflow secrets properly configured
- Private repository requires authentication
- GitHub Pages only serves processed, approved content

✅ **Transparency**
- Clear terms of use in README
- Documentation explains privacy measures
- Verification links allow credential validation

### 4.2 Potential Information Leakage Risks

⚠️ **Workflow Configuration Exposure**
- **Risk**: Workflow files reveal the exact process for handling sensitive data
- **Information Leaked**: 
  - Directory structure of private repository
  - Processing pipeline details
  - Redaction patterns configuration file path
  - Existence of private repository (name is secret, but usage is visible)
- **Mitigation**: This is acceptable for transparency, but be aware adversaries understand your process

⚠️ **Commit History and Messages**
- **Risk**: Commit messages might accidentally reveal information
- **Information Leaked**: File paths, repository structure, debugging information
- **Example**: "Fix: Update path from private-files/credentials to private-files/files/credentials"
- **Mitigation**: Review commit messages for sensitive information before pushing

⚠️ **Git History**
- **Risk**: Past commits might contain sensitive information
- **Information Leaked**: Previously committed files, old configurations
- **Mitigation**: Regularly audit git history, use `git filter-branch` if needed

⚠️ **Deployment Timing**
- **Risk**: Deployment frequency and timing might reveal activity patterns
- **Information Leaked**: When credentials are being added or updated
- **Mitigation**: Accept this as normal transparency or use scheduled deployments

⚠️ **Thumbnail Filenames (Hashed)**
- **Risk**: While hashed, filenames are deterministic
- **Information Leaked**: Same file always produces same hash
- **Mitigation**: Ensure hash algorithm includes salt or use UUIDs

⚠️ **Credential Metadata**
- **Risk**: Even without full personal data, metadata can be identifying
- **Information Leaked**: Timeline of credential acquisition, issuers, credential types
- **Mitigation**: This is intentional - metadata is meant to be public

### 4.3 Recommendations

#### Immediate Actions:
1. ✅ **Audit Current State**: Verify no sensitive files in git history
2. ⚠️ **Review Commit Messages**: Check for accidental information disclosure
3. ⚠️ **Test Redaction**: Ensure redaction patterns work correctly
4. ⚠️ **Verify Hashing**: Confirm thumbnail filenames cannot be reverse-engineered

#### Ongoing Best Practices:
1. **Never commit sensitive files** to public repository
2. **Review PRs carefully** for accidental sensitive data inclusion
3. **Monitor deployment logs** for unexpected information exposure
4. **Use workflow artifacts cautiously** - set short retention periods
5. **Regularly audit** what information is publicly visible
6. **Document sensitive fields** that must never be published

---

## 5. Conclusion

### What CAN Be Read:

From the three URLs, the following information is publicly accessible:

1. **Repository Code & Configuration** (https://github.com/sinwulok/credentials)
   - Complete source code and workflows
   - Repository structure and documentation
   - Commit history and metadata
   - Processing pipeline details

2. **Public Credential Display** (https://sinwulok.github.io/credentials/)
   - De-identified thumbnail images
   - Filtered credential metadata
   - Verification links
   - Public-facing credential information

3. **Deployment Status** (https://github.com/sinwulok/credentials/deployments/github-pages)
   - Deployment history and frequency
   - Success/failure status
   - Associated commits and branches

### What CANNOT Be Read:

- ❌ Original PDF certificates
- ❌ Full personal information
- ❌ Private repository contents
- ❌ Workflow secrets and credentials
- ❌ Unredacted sensitive data

### Overall Security Posture:

**GOOD** - The repository follows security best practices by:
- Separating public and private data
- Using proper secret management
- Implementing redaction and de-identification
- Providing clear terms of use

**Areas for Improvement:**
- Audit git history for accidental disclosures
- Review commit messages for sensitive information
- Consider adding more detailed privacy documentation
- Implement additional monitoring for unexpected data exposure

---

## 6. Privacy Policy Alignment

The repository's implementation aligns with its stated privacy policy:

> "為保護個資，原始憑證（PDF 或含敏感個資的文件）不會存放在公開 repo 中。"  
> Translation: "To protect personal data, original certificates (PDFs or documents containing sensitive personal information) are not stored in this public repository."

**Verification**: ✅ Confirmed - No PDF files or sensitive documents in public repository

> "未經書面同意，嚴禁任何形式的複製、轉載、公開散佈或改作"  
> Translation: "Without written permission, any copying, redistribution, public display, reposting, or creation of derivative works is prohibited."

**Note**: This policy applies to the displayed content, but the underlying code is governed by the LICENSE file (All Rights Reserved).

---

## Appendix: Technical Details

### A. Workflow Secrets Used
- `PRIVATE_FILES_REPO`: Name of private repository (e.g., "sinwulok/private-files")
- `PRIVATE_REPO_PAT`: Personal Access Token for private repository access
- `GITHUB_TOKEN`: Automatically provided token for GitHub Actions

### B. Data Flow Diagram
```
[Private Repository]
        ↓
   [Checkout in CI]
        ↓
   [Process & Redact]
        ↓
[Generate Thumbnails]
        ↓
[Create Index Files]
        ↓
  [Deploy to Pages]
        ↓
[Public GitHub Pages Site]
```

### C. Required Fields in Credential Metadata
According to `ingest_private_files.py`:
- id, slug, type, title, issuer, issue_date
- credential_id, verification_url, thumbnail
- group_id, parent_id, group_role
- tags, visibility, order, notes

### D. File Locations
- **Public thumbnails**: `docs/assets/thumbnails/*.png`
- **Thumbnail index**: `docs/assets/thumbnails/index.json`
- **Credential data**: `docs/data/credentials.json`
- **Private source**: `private-files/credentials/*.{json,csv,tsv}` (not in public repo)
- **Private PDFs**: `private-files/*.pdf` (not in public repo)

---

**Document Version:** 1.0  
**Last Updated:** 2026-02-18  
**Prepared for:** sinwulok/credentials repository analysis
