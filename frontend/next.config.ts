import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Proxy API requests to FastAPI backend in development only
  async rewrites() {
    // In production, NEXT_PUBLIC_API_URL points to the Render backend
    // and the frontend calls it directly — no proxy needed.
    // In development, we proxy /api/* to localhost:8001.
    if (process.env.NODE_ENV === "production") {
      return [];
    }
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";
    return [
      {
        source: "/api/:path*",
        destination: `${apiUrl}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
