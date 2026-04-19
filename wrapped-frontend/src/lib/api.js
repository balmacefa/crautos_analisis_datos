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

/**
 * Robust fetcher function for use with SWR or standard fetches.
 * It catches network errors, non-200 responses, and logs them 
 * explicitly to help debug issues locally and prevent silent UI crashes.
 * 
 * @param {string} url - The URL to fetch data from.
 * @returns {Promise<any | null>} The JSON response or null on failure.
 */
export const robustFetcher = async (url) => {
  // TODO: Add logs, to know the incoming request, 2. and also create a function base od the swagger .json file from the backend
  try {
    const res = await fetch(url);
    if (!res.ok) {
      console.error(`[API Error] Failed to fetch ${url}. Status: ${res.status}`);
      return null;
    }
    return await res.json();
  } catch (err) {
    console.error(`[Network Error] Could not connect to data source at ${url}:`, err.message);
    return null; // Prevents "undefined" crashes downstream
  }
};

