//! Connection-string parsing for the yata client.

use crate::error::{Result, YataError};

/// A parsed yata DSN.
///
/// Format: `yatabase://<token>@<host>[:<port>]/<database>[?<param>=<value>&...]`.
#[derive(Debug, Clone)]
pub struct Dsn {
    /// Bearer token (`sk_live_yata_*`) used as the PG password.
    pub token: String,
    /// Hostname.
    pub host: String,
    /// TCP port. Defaults to `5432`.
    pub port: u16,
    /// Database name. Provisioned via
    /// `com.etzhayyim.apps.yata.provisionDatabase` (`yata_<hash>` shape).
    pub database: String,
    /// Trailing `?key=value&...` query string (for `application_name`
    /// etc). Stored as-is for v0.1; v0.2 will expose typed accessors.
    pub query: String,
}

impl Dsn {
    /// Parse a `yatabase://...` connection string.
    pub fn parse(s: &str) -> Result<Self> {
        let rest = s
            .strip_prefix("yatabase://")
            .or_else(|| s.strip_prefix("postgres://"))
            .or_else(|| s.strip_prefix("postgresql://"))
            .ok_or_else(|| YataError::Dsn(
                "DSN must start with yatabase:// (or postgres:// / postgresql://)".into(),
            ))?;

        let (auth, after_auth) = match rest.find('@') {
            Some(i) => (&rest[..i], &rest[i + 1..]),
            None => return Err(YataError::Dsn(
                "DSN missing `@` between token and host".into(),
            )),
        };
        // Token may be `user:password` shape (compat with libpq); we
        // accept both `user:pass` (use pass) and `pass` (use as-is).
        let token = match auth.find(':') {
            Some(i) => auth[i + 1..].to_string(),
            None => auth.to_string(),
        };
        if token.is_empty() {
            return Err(YataError::Dsn("DSN token is empty".into()));
        }

        let (host_port_db, query) = match after_auth.find('?') {
            Some(i) => (&after_auth[..i], after_auth[i + 1..].to_string()),
            None => (after_auth, String::new()),
        };

        let (host_port, database) = match host_port_db.find('/') {
            Some(i) => (&host_port_db[..i], host_port_db[i + 1..].to_string()),
            None => return Err(YataError::Dsn(
                "DSN missing `/database` segment".into(),
            )),
        };
        if database.is_empty() {
            return Err(YataError::Dsn("DSN database name is empty".into()));
        }

        let (host, port) = match host_port.rfind(':') {
            Some(i) => {
                let port = host_port[i + 1..]
                    .parse::<u16>()
                    .map_err(|_| YataError::Dsn(format!("invalid DSN port: {}", &host_port[i + 1..])))?;
                (host_port[..i].to_string(), port)
            }
            None => (host_port.to_string(), 5432),
        };
        if host.is_empty() {
            return Err(YataError::Dsn("DSN host is empty".into()));
        }

        Ok(Dsn { token, host, port, database, query })
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parses_canonical_dsn() {
        let d = Dsn::parse("yatabase://sk_live_yata_abc@yatabase.etzhayyim.com/yata_xxx").unwrap();
        assert_eq!(d.token, "sk_live_yata_abc");
        assert_eq!(d.host, "yatabase.etzhayyim.com");
        assert_eq!(d.port, 5432);
        assert_eq!(d.database, "yata_xxx");
        assert_eq!(d.query, "");
    }

    #[test]
    fn parses_user_pass_with_port_and_query() {
        let d = Dsn::parse("yatabase://etzhayyim_xxx:sk_live_yata_xyz@my.host.example:5433/y_db?sslmode=require").unwrap();
        assert_eq!(d.token, "sk_live_yata_xyz");
        assert_eq!(d.host, "my.host.example");
        assert_eq!(d.port, 5433);
        assert_eq!(d.database, "y_db");
        assert_eq!(d.query, "sslmode=require");
    }

    #[test]
    fn rejects_missing_scheme() {
        assert!(Dsn::parse("sk_live_yata_x@host/db").is_err());
    }

    #[test]
    fn rejects_missing_database() {
        assert!(Dsn::parse("yatabase://t@host").is_err());
    }
}
