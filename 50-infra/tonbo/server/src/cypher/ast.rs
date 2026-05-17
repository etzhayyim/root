/// Cypher query AST — mirrors packages/go/performer/graph/cypher/ast.go.
/// All types are serde-deserializable so Go clients can POST a pre-parsed AST
/// as JSON if they want to skip the Rust parser.
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct Query {
    #[serde(rename = "Match", default)]
    pub r#match: Option<MatchClause>,
    #[serde(rename = "Where", default)]
    pub r#where: Option<WhereClause>,
    #[serde(rename = "Return", default)]
    pub r#return: Option<ReturnClause>,
    #[serde(rename = "OrderBy", default)]
    pub order_by: Option<OrderByClause>,
    #[serde(rename = "Skip", default)]
    pub skip: i64,
    #[serde(rename = "Limit", default)]
    pub limit: i64,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct MatchClause {
    #[serde(rename = "Optional", default)]
    pub optional: bool,
    #[serde(rename = "Patterns", default)]
    pub patterns: Vec<PathPattern>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PathPattern {
    #[serde(rename = "Start")]
    pub start: NodePattern,
    #[serde(rename = "Steps", default)]
    pub steps: Vec<PathStep>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct NodePattern {
    #[serde(rename = "Variable", default)]
    pub variable: String,
    #[serde(rename = "Labels", default)]
    pub labels: Vec<String>,
    #[serde(rename = "Props", default)]
    pub props: HashMap<String, serde_json::Value>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PathStep {
    #[serde(rename = "Rel")]
    pub rel: RelPattern,
    #[serde(rename = "End")]
    pub end: NodePattern,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct RelPattern {
    #[serde(rename = "Variable", default)]
    pub variable: String,
    #[serde(rename = "Types", default)]
    pub types: Vec<String>,
    /// "out" | "in" | "both"
    #[serde(rename = "Direction", default = "default_out")]
    pub direction: String,
    #[serde(rename = "MinHops", default = "default_one")]
    pub min_hops: i32,
    /// -1 = unbounded
    #[serde(rename = "MaxHops", default = "default_one")]
    pub max_hops: i32,
}

fn default_out() -> String {
    "out".into()
}
fn default_one() -> i32 {
    1
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct WhereClause {
    #[serde(rename = "Predicates", default)]
    pub predicates: Vec<Predicate>,
}

/// "=" | "<>" | ">" | "<" | ">=" | "<=" | "IN" | "CONTAINS" | "STARTS WITH" | "ENDS WITH" | "HAS_LABEL"
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Predicate {
    #[serde(rename = "Variable", default)]
    pub variable: String,
    #[serde(rename = "Property", default)]
    pub property: String,
    #[serde(rename = "Op")]
    pub op: String,
    #[serde(rename = "Value")]
    pub value: PredicateValue,
}

/// Predicate value — can be a literal, a list, or a parameter reference.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(untagged)]
pub enum PredicateValue {
    Null,
    Bool(bool),
    Int(i64),
    Float(f64),
    Str(String),
    List(Vec<serde_json::Value>),
    Param { Name: String },
}

impl PredicateValue {
    pub fn resolve<'a>(
        &'a self,
        params: &'a HashMap<String, serde_json::Value>,
    ) -> Option<std::borrow::Cow<'a, serde_json::Value>> {
        match self {
            Self::Param { Name } => params
                .get(Name.as_str())
                .map(std::borrow::Cow::Borrowed),
            _ => Some(std::borrow::Cow::Owned(self.to_json())),
        }
    }

    pub fn to_json(&self) -> serde_json::Value {
        match self {
            Self::Null => serde_json::Value::Null,
            Self::Bool(b) => serde_json::json!(b),
            Self::Int(i) => serde_json::json!(i),
            Self::Float(f) => serde_json::json!(f),
            Self::Str(s) => serde_json::json!(s),
            Self::List(v) => serde_json::Value::Array(v.clone()),
            Self::Param { Name } => serde_json::json!({ "Name": Name }),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct ReturnClause {
    #[serde(rename = "Distinct", default)]
    pub distinct: bool,
    #[serde(rename = "Items", default)]
    pub items: Vec<ReturnItem>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct ReturnItem {
    #[serde(rename = "Variable", default)]
    pub variable: String,
    #[serde(rename = "Property", default)]
    pub property: String,
    #[serde(rename = "Alias", default)]
    pub alias: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct OrderByClause {
    #[serde(rename = "Items", default)]
    pub items: Vec<OrderByItem>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct OrderByItem {
    #[serde(rename = "Variable", default)]
    pub variable: String,
    #[serde(rename = "Property", default)]
    pub property: String,
    #[serde(rename = "Desc", default)]
    pub desc: bool,
}
