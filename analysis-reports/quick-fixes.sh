#!/bin/bash

# Quick fixes you can run immediately

echo "🚀 Starting Quick Fixes..."

# Fix 1: TypeScript configuration
echo "📝 Fixing TypeScript configuration..."
cd apps/web
npm install --save-dev @types/node @types/react @types/react-dom

# Fix 2: Remove unused imports
echo "🧹 Cleaning unused imports..."
npx eslint --fix "**/*.{ts,tsx}"

# Fix 3: Install critical dependencies
echo "📦 Installing critical dependencies..."
npm install next-auth @tanstack/react-query zod

# Fix 4: Create basic auth setup
echo "🔐 Setting up authentication..."
mkdir -p app/api/auth/[...nextauth]
cat > app/api/auth/[...nextauth]/route.ts << 'AUTH'
import NextAuth from "next-auth";
import { authOptions } from "@/lib/auth";

const handler = NextAuth(authOptions);
export { handler as GET, handler as POST };
AUTH

# Fix 5: Create environment template
echo "🔧 Creating environment template..."
cat > .env.example << 'ENV'
# Copy to .env.local and fill in values
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=
DATABASE_URL=
STRIPE_PUBLIC_KEY=
STRIPE_SECRET_KEY=
ENV

echo "✅ Quick fixes complete!"
echo ""
echo "Next steps:"
echo "1. Copy .env.example to .env.local"
echo "2. Fill in environment variables"
echo "3. Run 'npm run dev' to test"
