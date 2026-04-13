/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    typedRoutes: false
  },
  async rewrites() {
    const internalApiOrigin = (process.env.INTERNAL_API_ORIGIN ?? "http://backend:8000").replace(/\/$/, "");

    return [
      {
        source: "/api/v1/:path*",
        destination: `${internalApiOrigin}/api/v1/:path*`
      }
    ];
  }
};

module.exports = nextConfig;
