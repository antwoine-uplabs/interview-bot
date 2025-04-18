#!/bin/bash
# Frontend deployment script

# Install Vercel CLI if not already installed
if ! command -v vercel &> /dev/null
then
    echo "Installing Vercel CLI..."
    npm install -g vercel
fi

# Deploy frontend to Vercel
echo "Deploying frontend to Vercel..."
vercel --prod
