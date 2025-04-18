# Interview Evaluator Frontend

## Frontend Deployment Guide

### Option 1: Deploy via Vercel Dashboard

1. Log in to your Vercel dashboard
2. Click "Add New" → "Project"
3. Select your GitHub repository
4. Configure the project:
   - Root Directory: `frontend` (important!)
   - Framework Preset: Vite
   - Build Command: `npm run build`
   - Output Directory: `dist`
5. Under Environment Variables, add:
   - `VITE_SUPABASE_URL`: Your Supabase project URL
   - `VITE_SUPABASE_ANON_KEY`: Your public Supabase anon key
   - `VITE_API_URL`: Your deployed API URL (e.g., https://interview-bot-gamma.vercel.app)
6. Click "Deploy"

### Option 2: Deploy via CLI

1. Install Vercel CLI if not already installed:
   ```
   npm install -g vercel
   ```

2. Make sure you're in the frontend directory:
   ```
   cd /path/to/resume/frontend
   ```

3. Run the deployment command:
   ```
   vercel --prod
   ```

4. Follow the prompts:
   - When asked to set up and deploy, select "Yes"
   - When asked about the scope, select your user or team
   - When asked about linking to existing project, select "No"
   - Configure project settings:
     - Want to override settings? Select "Yes"
     - Set the directory to `.` (current directory)
     - Build command: `npm run build`
     - Output directory: `dist`
     - Development command: `npm run dev`
   - Add environment variables from the .env file if prompted

## Local Development

1. Install dependencies:
   ```
   npm install
   ```

2. Run development server:
   ```
   npm run dev
   ```

3. Build for production:
   ```
   npm run build
   ```
