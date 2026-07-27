# Next.js Frontend Vercel Deployment Guide

This guide details how to deploy the **Next.js Frontend** of the NORAY OS to **Vercel** (vercel.com).

---

## 🚀 Step-by-Step Deployment

### 1. Project Ingestion
1. Push the repository to GitHub.
2. Sign in to your dashboard on [Vercel](https://vercel.com).
3. Click **Add New...** and select **Project**.
4. Import your GitHub repository.

### 2. Project Settings Configurations
In the Configure Project screen:
- **Framework Preset**: Next.js
- **Root Directory**: Set this to `frontend`.
- **Build Command**: `next build` (Vercel resolves this automatically).

---

## ⚙️ Environment Variables Setup

Add the following variable to link Vercel to your active backend deployment:

| Variable Name | Value | Description |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | `https://noray-backend.up.railway.app` | The public HTTPS root URL of your hosted FastAPI backend. |

---

## 🔒 CORS Config Checklist
To allow the Next.js Vercel frontend to query the FastAPI backend:
1. Copy your Vercel deployment URL (e.g. `https://noray.vercel.app`).
2. Add this domain to your backend `ALLOWED_ORIGINS` environment variable (separated by commas).
