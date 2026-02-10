# Vercel Backend Deployment Guide

This guide will walk you through deploying your Django backend to Vercel as a new project.

## Prerequisites

- ✅ Backend code is in `backend/School-Hiring-Portal_BE` folder
- ✅ You have a `.env` file with all credentials
- ✅ You have a GitHub account
- ✅ You have a Vercel account (sign up at https://vercel.com if needed)

---

## Step 1: Prepare Your Backend Repository

### 1.1 Navigate to Backend Directory
```bash
cd backend/School-Hiring-Portal_BE
```

### 1.2 Verify Required Files Exist
Make sure these files exist:
- ✅ `vercel.json` - Vercel configuration
- ✅ `vercel_wsgi.py` - WSGI entry point
- ✅ `requirements.txt` - Python dependencies
- ✅ `.env` - Your environment variables (keep this local, don't commit!)

---

## Step 2: Initialize Git Repository (if not already done)

```bash
# Check if git is initialized
git status

# If not initialized, run:
git init
git add .
git commit -m "Initial commit - ready for Vercel deployment"
```

---

## Step 3: Push to GitHub

### 3.1 Create a New GitHub Repository

1. Go to https://github.com/new
2. Repository name: `school-hiring-portal-backend` (or your preferred name)
3. Description: "Django Backend for School Hiring Portal"
4. Choose **Private** or **Public** (your choice)
5. **DO NOT** initialize with README, .gitignore, or license
6. Click **Create repository**

### 3.2 Push Your Code

```bash
# Add your GitHub repository as remote (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/school-hiring-portal-backend.git

# Push to GitHub
git branch -M main
git push -u origin main
```

---

## Step 4: Deploy to Vercel

### 4.1 Install Vercel CLI (if not installed)

```bash
npm install -g vercel
```

### 4.2 Login to Vercel

```bash
vercel login
```
- This will open your browser to authenticate
- Follow the prompts to login

### 4.3 Deploy Your Backend

```bash
# Make sure you're in the backend directory
cd backend/School-Hiring-Portal_BE

# Deploy to Vercel
vercel
```

**Follow the prompts:**
1. **Set up and deploy?** → Type `Y` and press Enter
2. **Which scope?** → Select your account/team
3. **Link to existing project?** → Type `N` (we're creating a new project)
4. **What's your project's name?** → Type `school-hiring-portal-backend` (or your preferred name)
5. **In which directory is your code located?** → Press Enter (current directory: `./`)
6. **Want to override the settings?** → Type `N` and press Enter

Vercel will:
- Detect Python/Django
- Install dependencies from `requirements.txt`
- Build your project
- Deploy it

**You'll get a deployment URL like:** `https://school-hiring-portal-backend-xxxxx.vercel.app`

---

## Step 5: Configure Environment Variables

### 5.1 Add Environment Variables in Vercel Dashboard

1. Go to https://vercel.com/dashboard
2. Click on your project: `school-hiring-portal-backend`
3. Go to **Settings** → **Environment Variables**
4. Add all variables from your `.env` file:

**Required Environment Variables:**
```
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-vercel-url.vercel.app,localhost

# Database (PostgreSQL)
POSTGRES_HOST=your-db-host
POSTGRES_DATABASE=your-db-name
POSTGRES_USER=your-db-user
POSTGRES_PASSWORD=your-db-password
POSTGRES_PORT=5432

# Stripe (LIVE MODE)
STRIPE_SECRET_KEY=sk_live_xxxxx
STRIPE_PUBLISHABLE_KEY=pk_live_xxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxx

# Stripe Price IDs (LIVE MODE)
SINGLE_PACKAGE_PRICE_ID=price_xxxxx
BRONZE_TEACHER_PACKAGE_PRICE_ID=price_xxxxx
SILVER_TEACHER_PACKAGE_PRICE_ID=price_xxxxx
GOLD_TEACHER_PACKAGE_PRICE_ID=price_xxxxx
TRIAL_TEACHER_PACKAGE_PRICE_ID=price_xxxxx
BRONZE_SCHOOL_PACKAGE_PRICE_ID=price_xxxxx
SILVER_SCHOOL_PACKAGE_PRICE_ID=price_xxxxx
GOLD_SCHOOL_PACKAGE_PRICE_ID=price_xxxxx

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Cloudinary (if using)
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret

# JWT Settings
JWT_SECRET_KEY=your-jwt-secret
JWT_ALGORITHM=HS256
```

**Important:**
- Set each variable for **Production**, **Preview**, and **Development** environments
- Click **Save** after adding each variable

### 5.2 Redeploy After Adding Environment Variables

```bash
vercel --prod
```

Or trigger a redeploy from Vercel dashboard:
- Go to **Deployments** tab
- Click **⋯** (three dots) on latest deployment
- Click **Redeploy**

---

## Step 6: Run Database Migrations

### 6.1 Pull Environment Variables Locally

```bash
# In your backend directory
vercel env pull .env.production
```

### 6.2 Run Migrations

```bash
# Activate virtual environment
source venv/Scripts/activate  # Windows Git Bash
# OR
venv\Scripts\activate  # Windows CMD
# OR
source venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Run migrations
python run_migrations.py
```

**OR** use the management command:
```bash
python manage.py run_migrations
```

**OR** direct migrate:
```bash
python manage.py migrate
```

---

## Step 7: Configure Stripe Webhook

### 7.1 Get Your Vercel Deployment URL

Your backend URL will be: `https://school-hiring-portal-backend-xxxxx.vercel.app`

### 7.2 Configure Webhook in Stripe Dashboard

1. Go to https://dashboard.stripe.com/webhooks
2. Click **Add endpoint**
3. **Endpoint URL:** `https://school-hiring-portal-backend-xxxxx.vercel.app/payment/webhook/`
4. **Description:** "School Hiring Portal - Production"
5. **Events to send:** Select these events:
   - `invoice.created`
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
   - `customer.subscription.deleted`
6. Click **Add endpoint**
7. **Copy the Signing secret** (starts with `whsec_`)
8. Add this to Vercel environment variables as `STRIPE_WEBHOOK_SECRET`

### 7.3 Verify Promo Codes in Stripe

Make sure these promo codes exist in your Stripe Dashboard (LIVE MODE):
- ✅ `GulfTeachers26` - 100% discount (all teacher packages)
- ✅ `GT50` - 50% discount (all teacher packages)
- ✅ `GT30` - 30% discount (Gold Teacher package only)

**To verify:**
1. Go to https://dashboard.stripe.com/coupons
2. Check that these promotion codes exist and are **active**
3. Verify discount percentages match:
   - `GulfTeachers26` → 100% off
   - `GT50` → 50% off
   - `GT30` → 30% off

---

## Step 8: Update Frontend API URL

### 8.1 Get Your Backend URL

Your backend will be deployed at: `https://school-hiring-portal-backend-xxxxx.vercel.app`

### 8.2 Update Frontend Environment Variables

In your frontend repository, update `.env` or Vercel environment variables:

```env
REACT_APP_Base_URL=https://school-hiring-portal-backend-xxxxx.vercel.app
```

**If using Vercel for frontend:**
1. Go to frontend project settings
2. Environment Variables
3. Update `REACT_APP_Base_URL` to your new backend URL
4. Redeploy frontend

---

## Step 9: Test Your Deployment

### 9.1 Test API Endpoints

```bash
# Test health check (if you have one)
curl https://school-hiring-portal-backend-xxxxx.vercel.app/api/health/

# Test package list
curl https://school-hiring-portal-backend-xxxxx.vercel.app/api/packages/
```

### 9.2 Test from Frontend

1. Open your frontend application
2. Try to login/signup
3. Browse jobs
4. Test payment flow with promo codes:
   - `GulfTeachers26` (100% - should bypass card)
   - `GT50` (50% discount)
   - `GT30` (30% - only for Gold package)

---

## Step 10: Set Up Custom Domain (Optional)

1. Go to Vercel Dashboard → Your Project → **Settings** → **Domains**
2. Add your custom domain (e.g., `api.yourdomain.com`)
3. Follow DNS configuration instructions
4. Update frontend `REACT_APP_Base_URL` to use custom domain

---

## Troubleshooting

### Issue: Build Fails
**Solution:**
- Check `requirements.txt` has all dependencies
- Verify Python version in Vercel (should auto-detect)
- Check build logs in Vercel dashboard

### Issue: Database Connection Error
**Solution:**
- Verify all database environment variables are set correctly
- Check database allows connections from Vercel IPs
- Ensure database is accessible from internet

### Issue: 500 Errors
**Solution:**
- Check Vercel function logs
- Verify all environment variables are set
- Check database migrations are run
- Verify Stripe keys are in LIVE mode

### Issue: Promo Codes Not Working
**Solution:**
- Verify promo codes exist in Stripe Dashboard (LIVE mode)
- Check promo codes are active
- Verify discount percentages match (100%, 50%, 30%)
- Check backend logs for validation errors

### Issue: Webhook Not Working
**Solution:**
- Verify webhook URL is correct: `https://your-backend.vercel.app/payment/webhook/`
- Check `STRIPE_WEBHOOK_SECRET` is set correctly
- Test webhook in Stripe Dashboard → Send test webhook

---

## Important Notes

⚠️ **Security:**
- Never commit `.env` file to Git
- Use Vercel environment variables for production
- Keep `DEBUG=False` in production
- Use strong `SECRET_KEY`

⚠️ **Database:**
- Run migrations after deployment
- Backup database before major changes
- Use PostgreSQL for production (recommended)

⚠️ **Stripe:**
- Use **LIVE** mode keys in production
- Verify all promo codes are in LIVE mode
- Test payment flow thoroughly before going live

⚠️ **Monitoring:**
- Check Vercel function logs regularly
- Set up error monitoring (Sentry, etc.)
- Monitor Stripe webhook events

---

## Quick Reference Commands

```bash
# Deploy to production
vercel --prod

# Deploy to preview
vercel

# View logs
vercel logs

# Pull environment variables
vercel env pull .env.production

# Run migrations
python run_migrations.py

# Check deployment status
vercel ls
```

---

## Next Steps

1. ✅ Backend deployed to Vercel
2. ✅ Environment variables configured
3. ✅ Database migrations run
4. ✅ Stripe webhook configured
5. ✅ Frontend updated with new backend URL
6. ✅ Test all functionality
7. ✅ Monitor logs and errors

**Your backend is now live! 🎉**
