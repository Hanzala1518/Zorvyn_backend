import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Silence the multi-lockfile workspace root warning
  turbopack: {
    root: __dirname,
  },
  // On Vercel: NEXT_PUBLIC_API_URL="" and BACKEND_URL=https://your-app.onrender.com
  // All /api/* calls from the browser hit the Next.js server which proxies to Render.
  // This eliminates CORS entirely in production because requests are same-origin.
  // Locally: set NEXT_PUBLIC_API_URL=http://localhost:8000 to bypass the proxy.
  async rewrites() {
    const backendUrl = process.env.BACKEND_URL || "http://localhost:8000";
    return [
      {
        source: "/api/:path*",
        destination: `${backendUrl}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
