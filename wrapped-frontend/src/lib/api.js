/**
 * Returns the appropriate API base URL based on the execution context.
 * For SSR (Server-Side Rendering), it uses the internal Docker network URL.
 * For Client-Side, it uses the public URL accessible from the browser.
 */
export function getApiBaseUrl() {
  const isServer = typeof window === 'undefined';
  
  if (isServer) {
    // Internal Docker network URL (service name 'api')
    return process.env.INTERNAL_API_URL || 'http://api:8000';
  }
  
  // Public URL for the browser
  return process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
}
