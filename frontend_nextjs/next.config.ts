import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  devIndicators: false,

  // Allow network users for cross-origin access
  // allowedDevOrigins: ['*'],

  // Build static export for now
  // https://nextjs.org/docs/app/guides/static-exports
  output: 'export',

  // Base path for static exporting
  // basePath: '/dbca-authorisations',
};

export default nextConfig;
