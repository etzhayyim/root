/**
 * @fileoverview Supabase client configuration
 * @see https://supabase.com/docs/reference/javascript/introduction
 *
 * @context
 * {
 *   "@context": "https://schema.org",
 *   "@type": "SoftwareApplication",
 *   "name": "Supabase Client",
 *   "description": "Supabase client for database and realtime operations",
 *   "applicationCategory": "Database"
 * }
 */

import { createClient } from "@supabase/supabase-js"
import type { Database } from "./types"

if (!process.env.SUPABASE_URL) {
  throw new Error("SUPABASE_URL environment variable is not set")
}

if (!process.env.SUPABASE_ANON_KEY) {
  throw new Error("SUPABASE_ANON_KEY environment variable is not set")
}

/**
 * Supabase client for client-side operations (uses anon key)
 */
export const supabase = createClient<Database>(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_ANON_KEY,
  {
    auth: {
      persistSession: false,
    },
  }
)

/**
 * Supabase client for server-side operations (uses service role key)
 * Use this for admin operations that bypass RLS
 */
export const supabaseAdmin = createClient<Database>(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.SUPABASE_ANON_KEY,
  {
    auth: {
      persistSession: false,
    },
  }
)

