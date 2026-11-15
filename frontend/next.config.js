/** @type {import('next').NextConfig} */
const createNextIntlPlugin = require('next-intl/plugin');

const withNextIntl = createNextIntlPlugin();

const nextConfig = {
  reactStrictMode: true,
  // Production is served under http://<server>/insta-data - set
  // NEXT_BASE_PATH=/insta-data in that server's frontend/.env.production
  // (read at build time) instead of editing this file there.
  basePath: process.env.NEXT_BASE_PATH || undefined,
  swcMinify: true,
  compiler: {
    removeConsole: process.env.NODE_ENV === 'production',
  },
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: '**',
      },
    ],
  },
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
    NEXT_PUBLIC_APP_NAME: process.env.NEXT_PUBLIC_APP_NAME || 'Insta-Data',
  },
};

module.exports = withNextIntl(nextConfig);