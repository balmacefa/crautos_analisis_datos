import { Api } from './api-client';

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
  const start = Date.now();
  const timestamp = new Date().toISOString();
  
  console.log(`%c[API Request] %cGET %c${url} %c@ ${timestamp}`, 
    'color: #3b82f6; font-weight: bold', 
    'color: #10b981; font-weight: bold', 
    'color: #94a3b8', 
    'color: #64748b; font-size: 10px');

  try {
    const res = await fetch(url);
    const duration = Date.now() - start;

    if (!res.ok) {
      console.error(`%c[API Error] %cFailed to fetch %c${url} %cStatus: ${res.status} (%c${duration}ms)`,
        'color: #ef4444; font-weight: bold',
        'color: #fca5a5',
        'color: #94a3b8',
        'color: #f87171; font-weight: bold',
        'color: #64748b');
      return null;
    }

    const data = await res.json();
    
    console.log(`%c[API Success] %c${url} %c(${duration}ms)`,
      'color: #10b981; font-weight: bold',
      'color: #94a3b8',
      'color: #64748b');

    return data;
  } catch (err) {
    const duration = Date.now() - start;
    console.error(`%c[Network Error] %cCould not connect to %c${url} %c@ ${err.message} (%c${duration}ms)`,
      'color: #ef4444; font-weight: bold',
      'color: #f87171',
      'color: #94a3b8',
      'color: #ef4444',
      'color: #64748b');
    return null; // Prevents "undefined" crashes downstream
  }
};

/**
 * Centrally initialized API client based on the auto-generated Swagger spec.
 * This provides named functions and type-hinting for all backend endpoints.
 */
export const api = new Api({
  baseUrl: getApiBaseUrl(),
  customFetch: robustFetcher // This ensures the generated client also uses our robust logging fetcher
});


