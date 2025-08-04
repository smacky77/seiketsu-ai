'use client';

import { useEffect } from 'react';
import { setupStagewise } from '@/lib/stagewise-toolbar';

export function ToolbarProvider() {
  useEffect(() => {
    setupStagewise();
  }, []);

  return null;
}