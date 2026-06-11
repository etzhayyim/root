type MockSCAPContent = {
  id: string
  type: "OVAL" | "XCCDF" | "CPE"
  title: string
  cves: string[]
  cpes: string[]
  lastUpdated: string
}

export const mockAllContent: MockSCAPContent[] = [
  {
    id: "oval:org.mitre.oval:def:1000",
    type: "OVAL",
    title: "Microsoft Windows 10 Version 22H2 is vulnerable",
    cves: ["CVE-2023-36025"],
    cpes: ["cpe:/o:microsoft:'windows10':22h2"],
    lastUpdated: "2023-11-15",
  },
  {
    id: "xccdfGov.nist.content_benchmark_USGCB-Windows-10",
    type: "XCCDF",
    title: "USGCB for Windows 10",
    cves: [],
    cpes: ["cpe:/o:microsoft:windows10"],
    lastUpdated: "2022-08-01",
  },
  {
    id: "cpe:/a:apache:'httpServer':2.4.54",
    type: "CPE",
    title: "Apache HTTP Server 2.4.54",
    cves: ["CVE-2022-37436", "CVE-2022-36760"],
    cpes: [],
    lastUpdated: "2023-01-20",
  },
  {
    id: "oval:org.cisecurity:def:8000",
    type: "OVAL",
    title: "CIS Ubuntu Linux 20.04 LTS Benchmark v1.1.0",
    cves: [],
    cpes: ["cpe:/o:canonical:'ubuntuLinux':20.04"],
    lastUpdated: "2023-05-10",
  },
  {
    id: "oval:com.redhat.rhsa:def:20233392",
    type: "OVAL",
    title: "Important: curl security update",
    cves: ["CVE-2023-28321", "CVE-2023-28322"],
    cpes: ["cpe:/o:redhat:'enterpriseLinux':8"],
    lastUpdated: "2023-07-22",
  },
  {
    id: "xccdfOrg.ssgproject.contentProfileOspp",
    type: "XCCDF",
    title: "SCAP Security Guide for RHEL 8 - OSPP Profile",
    cves: [],
    cpes: ["cpe:/o:redhat:'enterpriseLinux':8"],
    lastUpdated: "2023-09-01",
  },
]

export const mockRecentActivity = mockAllContent.slice(0, 4)

// SCAP Data Sources Configuration with Real Update Frequencies
export const SCAP_DATA_SOURCES = {
  // High-frequency sources (Critical security updates)
  NVD: {
    name: 'NIST NVD',
    updateFrequency: '4h', // NVD updates multiple times daily
    priority: 'high',
    description: 'NIST National Vulnerability Database - CVE data'
  },

  // Medium-frequency sources
  MITRE_OVAL: {
    name: 'MITRE OVAL',
    updateFrequency: '12h', // OVAL definitions update 1-2 times daily
    priority: 'medium',
    description: 'MITRE OVAL vulnerability definitions'
  },

  OPENSCAP: {
    name: 'OpenSCAP',
    updateFrequency: '24h', // Daily updates from GitHub
    priority: 'medium',
    description: 'OpenSCAP Security Guide from ComplianceAsCode'
  },

  // Low-frequency sources
  DISA_STIG: {
    name: 'DISA STIG',
    updateFrequency: '168h', // Weekly updates (7 days * 24h)
    priority: 'low',
    description: 'DISA Security Technical Implementation Guides'
  },

  // Emergency updates
  EMERGENCY: {
    name: 'Emergency Update',
    updateFrequency: '1h', // For critical zero-day vulnerabilities
    priority: 'critical',
    description: 'Emergency SCAP updates for critical vulnerabilities'
  }
} as const

// Workflow DevKit Schedule Configuration
// Use sleep() directive in workflows for scheduled execution
export const WORKFLOW_SCHEDULE_CONFIG = {
  // Production schedules based on SCAP update frequencies
  PRODUCTION: {
    NVD_FETCH_HOURS: 4,        // Every 4 hours
    OVAL_FETCH_HOURS: 12,      // Every 12 hours
    OPENSCAP_FETCH_HOURS: 24,  // Every 24 hours
    STIG_FETCH_HOURS: 168,     // Every 7 days (168 hours)
    EMERGENCY_HOURS: 1,        // Every 1 hour for critical updates
    INTEGRATED_FETCH_HOURS: 6, // Comprehensive update every 6 hours
  },

  // Development schedules (faster for testing)
  DEVELOPMENT: {
    NVD_FETCH_HOURS: 0.5,      // Every 30 minutes
    OVAL_FETCH_HOURS: 1,       // Every 1 hour
    OPENSCAP_FETCH_HOURS: 2,   // Every 2 hours
    STIG_FETCH_HOURS: 4,       // Every 4 hours
    EMERGENCY_HOURS: 0.25,     // Every 15 minutes
    INTEGRATED_FETCH_HOURS: 0.75, // Every 45 minutes
  }
} as const

// Database Retention Configuration
// All data is stored in PostgreSQL via Diesel ORM (Rust GraphQL service)
// Retention policies can be configured at the database level

// SCAP Processing Configuration
export const SCAP_PROCESSING_CONFIG = {
  // Rate limits to respect external APIs
  NVD_RATE_LIMIT_MS: 2000,       // 2 seconds between NVD API calls
  GITHUB_RATE_LIMIT_MS: 1000,    // 1 second between GitHub API calls
  DISA_RATE_LIMIT_MS: 5000,      // 5 seconds between DISA requests

  // Batch sizes for processing
  CVE_BATCH_SIZE: 100,
  OVAL_BATCH_SIZE: 50,
  STIG_BATCH_SIZE: 25,

  // Timeout configurations
  FETCH_TIMEOUT_MS: 300000,      // 5 minutes
  PROCESS_TIMEOUT_MS: 600000,    // 10 minutes

  // Retry configuration
  MAX_RETRIES: 3,
  RETRY_BACKOFF_MS: 5000,

  // Priority thresholds
  HIGH_PRIORITY_CVSS_THRESHOLD: 7.0,
  CRITICAL_PRIORITY_CVSS_THRESHOLD: 9.0
} as const
