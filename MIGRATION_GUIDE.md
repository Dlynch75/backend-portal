# Database Migration Guide

This guide explains how to run database migrations on your production Vercel deployment.

## Option 1: Using Vercel CLI (Recommended)

### Step 1: Install Vercel CLI
```bash
npm install -g vercel
```

### Step 2: Login to Vercel
```bash
vercel login
```

### Step 3: Link to your project
```bash
cd backend/School-Hiring-Portal_BE
vercel link
```
- Select your existing project: `school-hiring-portal-be`
- Select the scope (your team/account)

### Step 4: Pull environment variables
```bash
vercel env pull .env.production
```
This downloads all your production environment variables to `.env.production`

### Step 5: Run migrations
```bash
# Activate virtual environment (if not already active)
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

## Option 2: Using Django Management Command

After setting up environment variables (Step 4 above):

```bash
python manage.py run_migrations
```

## Option 3: Direct Migration Command

After setting up environment variables (Step 4 above):

```bash
python manage.py migrate
```

## Option 4: One-time Vercel Function (Alternative)

If you prefer to run migrations via a Vercel serverless function, you can create an API endpoint that runs migrations once. **⚠️ WARNING: Remove this endpoint after use for security!**

## Verification

After running migrations, verify the changes:

1. Check that the `currency` field exists in `JobPosting` table
2. Verify all other migrations are applied

## Troubleshooting

### Database Connection Error
- Ensure `.env.production` has correct database credentials
- Check that your database allows connections from Vercel's IP addresses
- Verify `POSTGRES_HOST`, `POSTGRES_DATABASE`, `POSTGRES_USER`, `POSTGRES_PASSWORD` are correct

### Migration Already Applied
- If you see "No migrations to apply", that's fine - it means migrations are already up to date

### Permission Errors
- Ensure your database user has permissions to alter tables
- Check that the database user can create/modify tables

## Important Notes

- ⚠️ **Always backup your database before running migrations in production**
- ⚠️ **Test migrations on a staging environment first if possible**
- ⚠️ **Migrations are idempotent - safe to run multiple times**
