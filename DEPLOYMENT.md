# Deployment Guide

Follow these steps to deploy your Full-Stack FastAPI + React application to Vercel.

## Step 1: Initialize Git and Commit
First, make sure your code is committed to Git. Open your terminal in the root directory (`Fastapi`) and run:

```bash
git init
git add .
git commit -m "Initial commit"
```

## Step 2: Push to GitHub
1. Go to [GitHub](https://github.com/new) and create a new, empty repository.
2. Follow the instructions to push your local repository to GitHub. It will look like this:

```bash
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git push -u origin main
```

## Step 3: Deploy to Vercel
1. Go to [Vercel](https://vercel.com/) and log in (sign up with GitHub).
2. Click **Add New** -> **Project**.
3. Import the GitHub repository you just created.
4. **Important Settings during Import:**
   - **Framework Preset**: Leave as "Other". Vercel will use our `vercel.json` file.
   - **Root Directory**: Leave it as the root (`./`).
   - **Environment Variables**: Add your API keys from your `.env` file here:
     - `GROQ_API_KEY` = `your_key_here`
     - `GROQ_MODEL` = `llama-3.3-70b-versatile`
     - `ENVIRONMENT` = `production`
5. Click **Deploy**.

Vercel will now automatically build your React frontend and deploy your FastAPI backend using the configurations provided in `vercel.json`!

> **Note**: Your API calls from the React frontend will automatically route to the FastAPI backend through the `/api/*` routes because of the `routes` configuration in `vercel.json`. Ensure your frontend API base URL points to `/api` when deployed.
