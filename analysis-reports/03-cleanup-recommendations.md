# 🧹 Cleanup Recommendations

## Immediate Actions (Day 1-2)

### 1. Fix TypeScript Configuration
```bash
# Fix tsconfig.json
cd apps/web
cat > tsconfig.json << 'TSCONFIG'
{
  "compilerOptions": {
    "target": "ES2020",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "forceConsistentCasingInFileNames": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx"],
  "exclude": ["node_modules"]
}
TSCONFIG
```

### 2. Install Missing Dependencies
```bash
# Frontend
cd apps/web
npm install --save \
  next-auth \
  @stripe/stripe-js \
  @tanstack/react-query \
  zod \
  @radix-ui/react-toast \
  lucide-react

# Backend
cd apps/api
pip install \
  sqlalchemy \
  alembic \
  python-jose[cryptography] \
  stripe \
  redis \
  python-multipart \
  email-validator
```

### 3. Set Up Environment Variables
```bash
# Create .env.local
cat > apps/web/.env.local << 'ENV'
# Authentication
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=generate-secret-here

# Database
DATABASE_URL=postgresql://user:password@localhost/seiketsu

# Stripe
STRIPE_PUBLIC_KEY=pk_test_xxx
STRIPE_SECRET_KEY=sk_test_xxx

# API
NEXT_PUBLIC_API_URL=http://localhost:8000
ENV
```

## Week 1 Cleanup Tasks

### Day 1-2: TypeScript & Dependencies ✅
- [ ] Fix all TypeScript errors
- [ ] Update dependencies
- [ ] Configure ESLint properly
- [ ] Set up Prettier

### Day 3-4: Database & Auth 🗄️
- [ ] Design database schema
- [ ] Set up Supabase
- [ ] Implement NextAuth.js
- [ ] Create user models

### Day 5-7: Core API 🔌
- [ ] Complete FastAPI endpoints
- [ ] Add validation
- [ ] Implement error handling
- [ ] Create API tests

## Week 2 Cleanup Tasks

### Day 8-9: Payments 💳
- [ ] Integrate Stripe
- [ ] Create pricing tiers
- [ ] Implement subscriptions
- [ ] Add webhook handlers

### Day 10-11: Security 🔒
- [ ] Add rate limiting
- [ ] Implement CORS
- [ ] Add input validation
- [ ] Configure security headers

### Day 12-14: Testing 🧪
- [ ] Unit tests (Jest)
- [ ] API tests (Pytest)
- [ ] Integration tests
- [ ] E2E tests (Playwright)

## Week 3 Cleanup Tasks

### Day 15-16: Performance ⚡
- [ ] Optimize bundle size
- [ ] Add lazy loading
- [ ] Implement caching
- [ ] Configure CDN

### Day 17-18: Documentation 📚
- [ ] API documentation
- [ ] Component docs
- [ ] Deployment guide
- [ ] User manual

### Day 19-21: Production 🚀
- [ ] Deploy to Vercel
- [ ] Set up monitoring
- [ ] Configure alerts
- [ ] Performance testing

## File Cleanup Checklist

### Remove Unused Files
```bash
# Find and remove unused components
find apps/web/components -name "*.tsx" -exec grep -l "export" {} \; | \
  xargs -I {} sh -c 'grep -q "import.*from.*{}" apps/web/**/*.tsx || echo "Unused: {}"'

# Clean node_modules and reinstall
rm -rf node_modules apps/*/node_modules
npm install
```

### Organize Imports
```bash
# Use ESLint to fix imports
npx eslint --fix "apps/web/**/*.{ts,tsx}"
```

### Remove Console Logs
```bash
# Find all console.log statements
grep -r "console.log" apps/web/app apps/web/components apps/web/lib
```

## Code Quality Improvements

### 1. Add Type Safety
```typescript
// Before
const handleSubmit = (data) => { ... }

// After
interface FormData {
  email: string;
  password: string;
}
const handleSubmit = (data: FormData): Promise<void> => { ... }
```

### 2. Add Error Boundaries
```typescript
// Create error boundary component
import { ErrorBoundary } from 'react-error-boundary';

function ErrorFallback({error}: {error: Error}) {
  return (
    <div role="alert">
      <h2>Something went wrong:</h2>
      <pre>{error.message}</pre>
    </div>
  );
}
```

### 3. Implement Loading States
```typescript
// Add proper loading states
const [isLoading, setIsLoading] = useState(false);
const [error, setError] = useState<Error | null>(null);
```

## Performance Optimizations

### 1. Bundle Size Reduction
```javascript
// next.config.js
module.exports = {
  webpack: (config, { isServer }) => {
    if (!isServer) {
      config.optimization.splitChunks = {
        chunks: 'all',
        cacheGroups: {
          default: false,
          vendors: false,
          vendor: {
            name: 'vendor',
            chunks: 'all',
            test: /node_modules/
          }
        }
      };
    }
    return config;
  }
};
```

### 2. Image Optimization
```typescript
// Use Next.js Image component
import Image from 'next/image';

<Image
  src="/hero.jpg"
  alt="Hero"
  width={1200}
  height={600}
  priority
  placeholder="blur"
/>
```

### 3. Lazy Loading
```typescript
// Lazy load heavy components
import dynamic from 'next/dynamic';

const HeavyComponent = dynamic(
  () => import('./HeavyComponent'),
  { 
    loading: () => <p>Loading...</p>,
    ssr: false 
  }
);
```
