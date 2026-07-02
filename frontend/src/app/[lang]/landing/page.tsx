/**
 * Landing Page — Design Brief Variations
 * URL: /{lang}/landing (e.g., /ukr/landing, /rus/landing, /en/landing)
 */

import { LandingPageDesignBrief } from '@/components/LandingPageDesignBrief';

export const metadata = {
  title: 'Monte-Shop-Price Landing — Design Variations',
  description: 'Three landing page designs for Monte-Shop-Price price comparison platform',
};

export default function LandingPage() {
  return <LandingPageDesignBrief />;
}