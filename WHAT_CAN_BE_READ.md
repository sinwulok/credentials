# What Can Be Read from This Repository

**Quick Answer:** This repository is designed to publicly display credential metadata while protecting sensitive personal information.

---

## 📍 Three Access Points

### 1. GitHub Repository
**URL:** https://github.com/sinwulok/credentials

**What you can see:**
- ✅ Source code and scripts
- ✅ Workflow configurations
- ✅ Documentation (README, examples)
- ✅ Commit history
- ✅ Repository structure

**What you CANNOT see:**
- ❌ Original certificate PDFs
- ❌ Full personal information
- ❌ Private repository contents
- ❌ Sensitive credentials

---

### 2. GitHub Pages Website
**URL:** https://sinwulok.github.io/credentials/

**What you can see (when deployed):**
- ✅ De-identified thumbnail images of credentials
- ✅ Credential metadata (title, issuer, date, verification links)
- ✅ Tags and categorization
- ✅ Public verification information

**Privacy protections applied:**
- 🔒 Filenames are hashed (not original names)
- 🔒 Personal information is redacted from images
- 🔒 Only approved metadata fields are published
- 🔒 Original documents are never uploaded

**Current status:**
- ⚠️ No credential data currently deployed (empty thumbnails directory)

---

### 3. GitHub Deployments Page
**URL:** https://github.com/sinwulok/credentials/deployments/github-pages

**What you can see:**
- ✅ Deployment history (dates and times)
- ✅ Deployment status (success/failure)
- ✅ Which commits were deployed
- ✅ Links to workflow runs

**What you CANNOT see:**
- ❌ Actual deployed files
- ❌ Workflow secrets
- ❌ Private repository content

---

## 🔐 Security Summary

### Public Information (By Design)
This repository **intentionally shares**:
- Credential metadata (titles, issuers, dates, verification links)
- De-identified thumbnail images
- Tags and categorization
- Public verification information

### Protected Information
This repository **protects**:
- Original certificate documents (stored in private repository)
- Full personal information (names, IDs, addresses, etc.)
- Sensitive identifiers (redacted or hashed)
- Private workflow secrets

### How It Works
```
Private Repository → CI/CD Processing → Redaction & De-identification → Public GitHub Pages
     (hidden)              (secure)              (automated)                  (visible)
```

---

## 📋 Example: What Someone Could Learn

If you visit these URLs, you could discover:

### From the Repository:
- "This person uses Python scripts to process credential data"
- "The system uses a private repository for sensitive files"
- "Thumbnails are generated and redacted automatically"
- "There's a workflow that deploys to GitHub Pages"

### From GitHub Pages (when deployed):
- "This person has credentials from [issuer name]"
- "These credentials were issued on [date]"
- "Here's a de-identified thumbnail preview"
- "You can verify these credentials at [verification URL]"

### From Deployments:
- "The site was last deployed on [date]"
- "Deployments happen when code is pushed to main branch"
- "Recent deployment was successful/failed"

### What They CANNOT Learn:
- ❌ Full name, date of birth, ID numbers
- ❌ Original document content
- ❌ How to access the private repository
- ❌ Actual credential files

---

## ⚠️ Important Notes

1. **By Design**: The public display of credential metadata is intentional. This repository exists to showcase verifiable qualifications.

2. **Privacy First**: Original documents with sensitive information are NEVER stored in the public repository.

3. **Verification Available**: Official verification links allow third parties to confirm credentials with issuing organizations.

4. **Terms of Use**: Content is for online viewing and verification only. Copying, redistribution, or reposting requires written permission.

---

## 🎯 Intended Use

This repository is designed for:
- ✅ **Professional showcase**: Display verifiable credentials to potential employers
- ✅ **Credential verification**: Allow third parties to verify qualifications
- ✅ **Portfolio display**: Present professional achievements publicly

This repository is NOT intended for:
- ❌ Storing sensitive personal documents
- ❌ Sharing full credential files
- ❌ Uncontrolled distribution of personal information

---

## 📞 Questions or Concerns?

If you have questions about what information is public or concerns about privacy:
- Review the [README.md](README.md) for terms of use
- Check [SECURITY_ANALYSIS.md](SECURITY_ANALYSIS.md) for detailed security information
- Contact: sinwulok (please include your concern and context)

---

**Last Updated:** 2026-02-18  
**Repository:** https://github.com/sinwulok/credentials
