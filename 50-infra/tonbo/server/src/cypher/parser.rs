/// Cypher parser — recursive descent, ported from packages/go/performer/graph/cypher/parser.go.
use std::collections::HashMap;

use super::ast::*;

// ── Lexer ─────────────────────────────────────────────────────────────────────

#[derive(Debug, Clone, PartialEq)]
pub enum TokenKind {
    Ident,    // keywords and bare names
    Str,      // 'single-quoted'
    Int,      // 42
    Float,    // 3.14
    Colon,    // :
    Dot,      // .
    Comma,    // ,
    Dollar,   // $
    Star,     // *
    Pipe,     // |
    LParen,   // (
    RParen,   // )
    LBracket, // [
    RBracket, // ]
    LBrace,   // {
    RBrace,   // }
    Arrow,    // ->  or  <-
    Dash,     // -
    Lt,       // <
    Gt,       // >
    Eq,       // =
    Neq,      // <>
    Gte,      // >=
    Lte,      // <=
    DotDot,   // ..
    Eof,
}

#[derive(Debug, Clone)]
pub struct Token {
    pub kind: TokenKind,
    pub raw: String,
}

pub struct Lexer {
    src: Vec<char>,
    pos: usize,
}

impl Lexer {
    pub fn new(src: &str) -> Self {
        Self {
            src: src.chars().collect(),
            pos: 0,
        }
    }

    fn peek(&self) -> Option<char> {
        self.src.get(self.pos).copied()
    }

    fn advance(&mut self) -> Option<char> {
        let c = self.src.get(self.pos).copied();
        self.pos += 1;
        c
    }

    fn skip_ws(&mut self) {
        while matches!(self.peek(), Some(c) if c.is_whitespace()) {
            self.advance();
        }
    }

    pub fn tokenize(mut self) -> Vec<Token> {
        let mut tokens = Vec::new();
        loop {
            self.skip_ws();
            let Some(c) = self.peek() else {
                tokens.push(Token { kind: TokenKind::Eof, raw: String::new() });
                break;
            };
            match c {
                '(' => { self.advance(); tokens.push(tok(TokenKind::LParen, "(")); }
                ')' => { self.advance(); tokens.push(tok(TokenKind::RParen, ")")); }
                '[' => { self.advance(); tokens.push(tok(TokenKind::LBracket, "[")); }
                ']' => { self.advance(); tokens.push(tok(TokenKind::RBracket, "]")); }
                '{' => { self.advance(); tokens.push(tok(TokenKind::LBrace, "{")); }
                '}' => { self.advance(); tokens.push(tok(TokenKind::RBrace, "}")); }
                ',' => { self.advance(); tokens.push(tok(TokenKind::Comma, ",")); }
                '$' => { self.advance(); tokens.push(tok(TokenKind::Dollar, "$")); }
                '*' => { self.advance(); tokens.push(tok(TokenKind::Star, "*")); }
                '|' => { self.advance(); tokens.push(tok(TokenKind::Pipe, "|")); }
                ':' => { self.advance(); tokens.push(tok(TokenKind::Colon, ":")); }
                '.' => {
                    self.advance();
                    if self.peek() == Some('.') {
                        self.advance();
                        tokens.push(tok(TokenKind::DotDot, ".."));
                    } else {
                        tokens.push(tok(TokenKind::Dot, "."));
                    }
                }
                '=' => { self.advance(); tokens.push(tok(TokenKind::Eq, "=")); }
                '<' => {
                    self.advance();
                    if self.peek() == Some('>') {
                        self.advance();
                        tokens.push(tok(TokenKind::Neq, "<>"));
                    } else if self.peek() == Some('=') {
                        self.advance();
                        tokens.push(tok(TokenKind::Lte, "<="));
                    } else if self.peek() == Some('-') {
                        self.advance();
                        tokens.push(tok(TokenKind::Arrow, "<-"));
                    } else {
                        tokens.push(tok(TokenKind::Lt, "<"));
                    }
                }
                '>' => {
                    self.advance();
                    if self.peek() == Some('=') {
                        self.advance();
                        tokens.push(tok(TokenKind::Gte, ">="));
                    } else {
                        tokens.push(tok(TokenKind::Gt, ">"));
                    }
                }
                '-' => {
                    self.advance();
                    if self.peek() == Some('>') {
                        self.advance();
                        tokens.push(tok(TokenKind::Arrow, "->"));
                    } else {
                        tokens.push(tok(TokenKind::Dash, "-"));
                    }
                }
                '\'' => {
                    self.advance();
                    let mut s = String::new();
                    loop {
                        match self.advance() {
                            Some('\'') => break,
                            Some('\\') => {
                                if let Some(e) = self.advance() {
                                    s.push(e);
                                }
                            }
                            Some(ch) => s.push(ch),
                            None => break,
                        }
                    }
                    tokens.push(tok(TokenKind::Str, &s));
                }
                c if c == '-' || c.is_ascii_digit() => {
                    let mut n = String::new();
                    if c == '-' {
                        n.push(c);
                        self.advance();
                    }
                    while matches!(self.peek(), Some(d) if d.is_ascii_digit()) {
                        n.push(self.advance().unwrap());
                    }
                    // Only treat as float if '.' is followed by a digit (not '..' range)
                    if self.peek() == Some('.')
                        && self.src.get(self.pos + 1).copied().map(|c| c.is_ascii_digit()).unwrap_or(false)
                    {
                        n.push(self.advance().unwrap());
                        while matches!(self.peek(), Some(d) if d.is_ascii_digit()) {
                            n.push(self.advance().unwrap());
                        }
                        tokens.push(tok(TokenKind::Float, &n));
                    } else {
                        tokens.push(tok(TokenKind::Int, &n));
                    }
                }
                c if c.is_ascii_digit() => {
                    let mut n = String::new();
                    while matches!(self.peek(), Some(d) if d.is_ascii_digit()) {
                        n.push(self.advance().unwrap());
                    }
                    if self.peek() == Some('.')
                        && self.src.get(self.pos + 1).copied().map(|c| c.is_ascii_digit()).unwrap_or(false)
                    {
                        n.push(self.advance().unwrap());
                        while matches!(self.peek(), Some(d) if d.is_ascii_digit()) {
                            n.push(self.advance().unwrap());
                        }
                        tokens.push(tok(TokenKind::Float, &n));
                    } else {
                        tokens.push(tok(TokenKind::Int, &n));
                    }
                }
                c if c.is_alphabetic() || c == '_' => {
                    let mut id = String::new();
                    while matches!(self.peek(), Some(ch) if ch.is_alphanumeric() || ch == '_') {
                        id.push(self.advance().unwrap());
                    }
                    tokens.push(tok(TokenKind::Ident, &id));
                }
                _ => { self.advance(); } // skip unknown
            }
        }
        tokens
    }
}

fn tok(kind: TokenKind, raw: &str) -> Token {
    Token { kind, raw: raw.to_string() }
}

// ── Parser ────────────────────────────────────────────────────────────────────

pub struct Parser {
    tokens: Vec<Token>,
    pos: usize,
}

impl Parser {
    pub fn new(tokens: Vec<Token>) -> Self {
        Self { tokens, pos: 0 }
    }

    fn peek(&self) -> &Token {
        self.tokens.get(self.pos).unwrap_or(self.tokens.last().unwrap())
    }

    fn peek_at(&self, offset: usize) -> &Token {
        self.tokens
            .get(self.pos + offset)
            .unwrap_or(self.tokens.last().unwrap())
    }

    fn advance(&mut self) -> &Token {
        let t = &self.tokens[self.pos.min(self.tokens.len() - 1)];
        if self.pos < self.tokens.len() - 1 {
            self.pos += 1;
        }
        t
    }

    fn is_keyword(&self, kw: &str) -> bool {
        self.peek().kind == TokenKind::Ident
            && self.peek().raw.to_uppercase() == kw
    }

    fn consume_keyword(&mut self, kw: &str) -> Result<(), String> {
        if self.is_keyword(kw) {
            self.advance();
            Ok(())
        } else {
            Err(format!("expected keyword {kw}, got {:?}", self.peek().raw))
        }
    }

    fn consume(&mut self, kind: TokenKind) -> Result<String, String> {
        if self.peek().kind == kind {
            let raw = self.advance().raw.clone();
            Ok(raw)
        } else {
            Err(format!("expected {:?}, got {:?}", kind, self.peek().raw))
        }
    }

    // ── public entry point ──────────────────────────────────────────────────

    pub fn parse_query(&mut self) -> Result<Query, String> {
        // Detect OPTIONAL before MATCH so "OPTIONAL MATCH ..." is handled correctly.
        let optional = if self.is_keyword("OPTIONAL") {
            self.advance();
            true
        } else {
            false
        };
        self.consume_keyword("MATCH")?;

        // Parse patterns directly (OPTIONAL already consumed above).
        let mut patterns = vec![self.parse_path_pattern()?];
        while self.peek().kind == TokenKind::Comma {
            self.advance();
            patterns.push(self.parse_path_pattern()?);
        }
        let r#match = MatchClause { optional, patterns };

        let r#where = if self.is_keyword("WHERE") {
            self.advance();
            Some(self.parse_where_clause()?)
        } else {
            None
        };

        let r#return = if self.is_keyword("RETURN") {
            self.advance();
            Some(self.parse_return_clause()?)
        } else {
            None
        };

        let order_by = if self.is_keyword("ORDER") {
            self.advance();
            self.consume_keyword("BY")?;
            Some(self.parse_order_by_clause()?)
        } else {
            None
        };

        let skip = if self.is_keyword("SKIP") {
            self.advance();
            let s = self.consume(TokenKind::Int)?;
            s.parse::<i64>().map_err(|e| e.to_string())?
        } else {
            0
        };

        let limit = if self.is_keyword("LIMIT") {
            self.advance();
            let s = self.consume(TokenKind::Int)?;
            s.parse::<i64>().map_err(|e| e.to_string())?
        } else {
            0
        };

        Ok(Query { r#match: Some(r#match), r#where, r#return, order_by, skip, limit })
    }

    // ── path pattern ────────────────────────────────────────────────────────

    fn parse_path_pattern(&mut self) -> Result<PathPattern, String> {
        let start = self.parse_node_pattern()?;
        let mut steps = Vec::new();
        while self.peek().kind == TokenKind::Dash
            || self.peek().kind == TokenKind::Arrow
            || (self.peek().kind == TokenKind::Lt && self.peek_at(1).kind == TokenKind::Dash)
        {
            steps.push(self.parse_path_step()?);
        }
        Ok(PathPattern { start, steps })
    }

    fn parse_node_pattern(&mut self) -> Result<NodePattern, String> {
        self.consume(TokenKind::LParen)?;
        let variable = if self.peek().kind == TokenKind::Ident
            && !matches!(self.peek().raw.to_uppercase().as_str(), "WHERE" | "RETURN" | "MATCH")
        {
            let raw = self.peek().raw.clone();
            // could be variable OR label after ':'
            if self.peek_at(1).kind == TokenKind::Colon
                || self.peek_at(1).kind == TokenKind::RParen
                || self.peek_at(1).kind == TokenKind::LBrace
            {
                self.advance();
                raw
            } else {
                String::new()
            }
        } else {
            String::new()
        };

        let mut labels = Vec::new();
        while self.peek().kind == TokenKind::Colon {
            self.advance();
            let lbl = self.consume(TokenKind::Ident)?;
            labels.push(lbl);
            // allow multi-part CURIE label like caseintel:CriminalCase
            while self.peek().kind == TokenKind::Colon
                && self.peek_at(1).kind == TokenKind::Ident
            {
                self.advance();
                let part = self.consume(TokenKind::Ident)?;
                if let Some(last) = labels.last_mut() {
                    last.push(':');
                    last.push_str(&part);
                }
            }
        }

        let props = if self.peek().kind == TokenKind::LBrace {
            self.parse_inline_props()?
        } else {
            HashMap::new()
        };

        self.consume(TokenKind::RParen)?;
        Ok(NodePattern { variable, labels, props })
    }

    fn parse_inline_props(&mut self) -> Result<HashMap<String, serde_json::Value>, String> {
        self.consume(TokenKind::LBrace)?;
        let mut props = HashMap::new();
        while self.peek().kind != TokenKind::RBrace && self.peek().kind != TokenKind::Eof {
            let key = self.consume(TokenKind::Ident)?;
            self.consume(TokenKind::Colon)?;
            let val = self.parse_literal()?;
            props.insert(key, val);
            if self.peek().kind == TokenKind::Comma {
                self.advance();
            }
        }
        self.consume(TokenKind::RBrace)?;
        Ok(props)
    }

    fn parse_path_step(&mut self) -> Result<PathStep, String> {
        let rel = self.parse_rel_pattern()?;
        let end = self.parse_node_pattern()?;
        Ok(PathStep { rel, end })
    }

    fn parse_rel_pattern(&mut self) -> Result<RelPattern, String> {
        // direction start: '-' or '<-'
        let dir_start = if self.peek().kind == TokenKind::Arrow && self.peek().raw == "<-" {
            self.advance();
            "in"
        } else {
            self.consume(TokenKind::Dash)?;
            "start"
        };

        // optional [...]
        let (variable, types, min_hops, max_hops) =
            if self.peek().kind == TokenKind::LBracket {
                self.advance();
                let var = if self.peek().kind == TokenKind::Ident {
                    let v = self.advance().raw.clone();
                    v
                } else {
                    String::new()
                };
                // var-length: [*1..3] or [*..3] or [*]
                let (min_h, max_h) = if self.peek().kind == TokenKind::Star {
                    self.advance();
                    self.parse_hop_range()?
                } else {
                    (1, 1)
                };
                // types: [:pred|pred2]
                let mut tys = Vec::new();
                if self.peek().kind == TokenKind::Colon {
                    self.advance();
                    tys.push(self.parse_rel_type()?);
                    while self.peek().kind == TokenKind::Pipe {
                        self.advance();
                        tys.push(self.parse_rel_type()?);
                    }
                }
                self.consume(TokenKind::RBracket)?;
                (var, tys, min_h, max_h)
            } else {
                (String::new(), Vec::new(), 1, 1)
            };

        // direction end: '->' or '-'
        let direction = if self.peek().kind == TokenKind::Arrow && self.peek().raw == "->" {
            self.advance();
            if dir_start == "in" { "both" } else { "out" }.to_string()
        } else if self.peek().kind == TokenKind::Dash {
            self.advance();
            if dir_start == "in" { "in" } else { "both" }.to_string()
        } else {
            if dir_start == "in" { "in" } else { "out" }.to_string()
        };

        Ok(RelPattern { variable, types, direction, min_hops: min_hops, max_hops: max_hops })
    }

    fn parse_rel_type(&mut self) -> Result<String, String> {
        let mut t = self.consume(TokenKind::Ident)?;
        while self.peek().kind == TokenKind::Colon && self.peek_at(1).kind == TokenKind::Ident {
            self.advance();
            let part = self.consume(TokenKind::Ident)?;
            t.push(':');
            t.push_str(&part);
        }
        Ok(t)
    }

    fn parse_hop_range(&mut self) -> Result<(i32, i32), String> {
        // after '*': integer? '..' integer?
        let min = if self.peek().kind == TokenKind::Int {
            let s = self.advance().raw.clone();
            s.parse::<i32>().map_err(|e| e.to_string())?
        } else {
            1
        };
        if self.peek().kind == TokenKind::DotDot {
            self.advance();
            let max = if self.peek().kind == TokenKind::Int {
                let s = self.advance().raw.clone();
                s.parse::<i32>().map_err(|e| e.to_string())?
            } else {
                -1 // unbounded
            };
            Ok((min, max))
        } else {
            Ok((min, min))
        }
    }

    // ── WHERE ───────────────────────────────────────────────────────────────

    fn parse_where_clause(&mut self) -> Result<WhereClause, String> {
        let mut preds = vec![self.parse_predicate()?];
        while self.is_keyword("AND") {
            self.advance();
            preds.push(self.parse_predicate()?);
        }
        Ok(WhereClause { predicates: preds })
    }

    fn parse_predicate(&mut self) -> Result<Predicate, String> {
        let var = self.consume(TokenKind::Ident)?;

        // HAS_LABEL: n:Label
        if self.peek().kind == TokenKind::Colon {
            self.advance();
            let mut lbl = self.consume(TokenKind::Ident)?;
            while self.peek().kind == TokenKind::Colon && self.peek_at(1).kind == TokenKind::Ident {
                self.advance();
                let p = self.consume(TokenKind::Ident)?;
                lbl.push(':');
                lbl.push_str(&p);
            }
            return Ok(Predicate {
                variable: var,
                property: String::new(),
                op: "HAS_LABEL".into(),
                value: PredicateValue::Str(lbl),
            });
        }

        self.consume(TokenKind::Dot)?;
        let prop = self.consume(TokenKind::Ident)?;

        // IS NULL / IS NOT NULL
        if self.is_keyword("IS") {
            self.advance();
            let op = if self.is_keyword("NOT") {
                self.advance();
                self.consume_keyword("NULL")?;
                "IS NOT NULL"
            } else {
                self.consume_keyword("NULL")?;
                "IS NULL"
            };
            return Ok(Predicate {
                variable: var,
                property: prop,
                op: op.into(),
                value: PredicateValue::Null,
            });
        }

        let op = self.parse_op()?;
        let value = if op == "IN" {
            self.parse_list_value()?
        } else {
            self.parse_value_or_param()?
        };

        Ok(Predicate { variable: var, property: prop, op, value })
    }

    fn parse_op(&mut self) -> Result<String, String> {
        let op = match self.peek().kind {
            TokenKind::Eq    => { self.advance(); "=".into() }
            TokenKind::Neq   => { self.advance(); "<>".into() }
            TokenKind::Gt    => { self.advance(); ">".into() }
            TokenKind::Lt    => { self.advance(); "<".into() }
            TokenKind::Gte   => { self.advance(); ">=".into() }
            TokenKind::Lte   => { self.advance(); "<=".into() }
            TokenKind::Ident => {
                let upper = self.peek().raw.to_uppercase();
                match upper.as_str() {
                    "IN" => { self.advance(); "IN".into() }
                    "CONTAINS" => { self.advance(); "CONTAINS".into() }
                    "STARTS" => {
                        self.advance();
                        self.consume_keyword("WITH")?;
                        "STARTS WITH".into()
                    }
                    "ENDS" => {
                        self.advance();
                        self.consume_keyword("WITH")?;
                        "ENDS WITH".into()
                    }
                    other => return Err(format!("unknown operator: {other}")),
                }
            }
            _ => return Err(format!("expected operator, got {:?}", self.peek().raw)),
        };
        Ok(op)
    }

    fn parse_value_or_param(&mut self) -> Result<PredicateValue, String> {
        if self.peek().kind == TokenKind::Dollar {
            self.advance();
            let name = self.consume(TokenKind::Ident)?;
            return Ok(PredicateValue::Param { Name: name });
        }
        let v = self.parse_literal()?;
        Ok(PredicateValue::from_json(v))
    }

    fn parse_list_value(&mut self) -> Result<PredicateValue, String> {
        self.consume(TokenKind::LBracket)?;
        let mut items = Vec::new();
        while self.peek().kind != TokenKind::RBracket && self.peek().kind != TokenKind::Eof {
            items.push(self.parse_literal()?);
            if self.peek().kind == TokenKind::Comma {
                self.advance();
            }
        }
        self.consume(TokenKind::RBracket)?;
        Ok(PredicateValue::List(items))
    }

    // ── RETURN ──────────────────────────────────────────────────────────────

    fn parse_return_clause(&mut self) -> Result<ReturnClause, String> {
        let distinct = if self.is_keyword("DISTINCT") {
            self.advance();
            true
        } else {
            false
        };
        let mut items = vec![self.parse_return_item()?];
        while self.peek().kind == TokenKind::Comma {
            self.advance();
            items.push(self.parse_return_item()?);
        }
        Ok(ReturnClause { distinct, items })
    }

    fn parse_return_item(&mut self) -> Result<ReturnItem, String> {
        let variable = self.consume(TokenKind::Ident)?;
        let property = if self.peek().kind == TokenKind::Dot {
            self.advance();
            self.consume(TokenKind::Ident)?
        } else {
            String::new()
        };
        let alias = if self.is_keyword("AS") {
            self.advance();
            self.consume(TokenKind::Ident)?
        } else {
            String::new()
        };
        Ok(ReturnItem { variable, property, alias })
    }

    // ── ORDER BY ────────────────────────────────────────────────────────────

    fn parse_order_by_clause(&mut self) -> Result<OrderByClause, String> {
        let mut items = vec![self.parse_order_by_item()?];
        while self.peek().kind == TokenKind::Comma {
            self.advance();
            items.push(self.parse_order_by_item()?);
        }
        Ok(OrderByClause { items })
    }

    fn parse_order_by_item(&mut self) -> Result<OrderByItem, String> {
        let variable = self.consume(TokenKind::Ident)?;
        let property = if self.peek().kind == TokenKind::Dot {
            self.advance();
            self.consume(TokenKind::Ident)?
        } else {
            String::new()
        };
        let desc = if self.is_keyword("DESC") {
            self.advance();
            true
        } else {
            if self.is_keyword("ASC") { self.advance(); }
            false
        };
        Ok(OrderByItem { variable, property, desc })
    }

    // ── literals ────────────────────────────────────────────────────────────

    fn parse_literal(&mut self) -> Result<serde_json::Value, String> {
        match self.peek().kind.clone() {
            TokenKind::Str => {
                let s = self.advance().raw.clone();
                Ok(serde_json::Value::String(s))
            }
            TokenKind::Int => {
                let s = self.advance().raw.clone();
                let n: i64 = s.parse().map_err(|e: std::num::ParseIntError| e.to_string())?;
                Ok(serde_json::json!(n))
            }
            TokenKind::Float => {
                let s = self.advance().raw.clone();
                let f: f64 = s.parse().map_err(|e: std::num::ParseFloatError| e.to_string())?;
                Ok(serde_json::json!(f))
            }
            TokenKind::Dash => {
                // negative number
                self.advance();
                match self.peek().kind.clone() {
                    TokenKind::Int => {
                        let s = self.advance().raw.clone();
                        let n: i64 = s.parse().map_err(|e: std::num::ParseIntError| e.to_string())?;
                        Ok(serde_json::json!(-n))
                    }
                    TokenKind::Float => {
                        let s = self.advance().raw.clone();
                        let f: f64 = s.parse().map_err(|e: std::num::ParseFloatError| e.to_string())?;
                        Ok(serde_json::json!(-f))
                    }
                    _ => Err(format!("expected number after '-', got {:?}", self.peek().raw)),
                }
            }
            TokenKind::Ident => {
                let upper = self.peek().raw.to_uppercase();
                match upper.as_str() {
                    "TRUE"  => { self.advance(); Ok(serde_json::Value::Bool(true)) }
                    "FALSE" => { self.advance(); Ok(serde_json::Value::Bool(false)) }
                    "NULL"  => { self.advance(); Ok(serde_json::Value::Null) }
                    _ => Err(format!("unexpected identifier {:?} as literal", self.peek().raw)),
                }
            }
            _ => Err(format!("expected literal, got {:?}", self.peek().raw)),
        }
    }
}

impl PredicateValue {
    pub fn from_json(v: serde_json::Value) -> Self {
        match v {
            serde_json::Value::Null => Self::Null,
            serde_json::Value::Bool(b) => Self::Bool(b),
            serde_json::Value::Number(n) => {
                if let Some(i) = n.as_i64() { Self::Int(i) }
                else { Self::Float(n.as_f64().unwrap_or(0.0)) }
            }
            serde_json::Value::String(s) => Self::Str(s),
            serde_json::Value::Array(a) => Self::List(a),
            _ => Self::Null,
        }
    }
}

// ── public entry point ────────────────────────────────────────────────────────

pub fn parse(cypher: &str) -> Result<Query, String> {
    let tokens = Lexer::new(cypher).tokenize();
    Parser::new(tokens).parse_query()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parse_simple_match() {
        let q = parse("MATCH (n:schema:LegalCase) WHERE n.label = 'foo' RETURN n LIMIT 10").unwrap();
        let m = q.r#match.unwrap();
        assert_eq!(m.patterns[0].start.labels, ["schema:LegalCase"]);
        let w = q.r#where.unwrap();
        assert_eq!(w.predicates[0].property, "label");
        assert_eq!(q.limit, 10);
    }

    #[test]
    fn parse_edge_pattern() {
        let q = parse("MATCH (n)-[:pred]->(m) RETURN n, m").unwrap();
        let step = &q.r#match.unwrap().patterns[0].steps[0];
        assert_eq!(step.rel.types, ["pred"]);
        assert_eq!(step.rel.direction, "out");
    }

    #[test]
    fn parse_bfs() {
        let q = parse("MATCH (n)-[*1..3]->(m) RETURN m").unwrap();
        let rel = &q.r#match.unwrap().patterns[0].steps[0].rel;
        assert_eq!(rel.min_hops, 1);
        assert_eq!(rel.max_hops, 3);
    }

    #[test]
    fn parse_order_by() {
        let q = parse("MATCH (n) RETURN n ORDER BY n.yabai_score DESC").unwrap();
        let ob = q.order_by.unwrap();
        assert_eq!(ob.items[0].property, "yabai_score");
        assert!(ob.items[0].desc);
    }

    #[test]
    fn parse_optional_match() {
        let q = parse("OPTIONAL MATCH (n:Person) RETURN n").unwrap();
        let m = q.r#match.unwrap();
        assert!(m.optional, "expected optional=true");
        assert_eq!(m.patterns[0].start.labels, ["Person"]);
    }

    #[test]
    fn parse_multi_variable_return() {
        let q = parse("MATCH (n)-[:knows]->(m) RETURN n, m").unwrap();
        let ret = q.r#return.unwrap();
        assert_eq!(ret.items.len(), 2);
        assert_eq!(ret.items[0].variable, "n");
        assert_eq!(ret.items[1].variable, "m");
    }

    #[test]
    fn parse_multi_type_rel() {
        let q = parse("MATCH (n)-[:knows|worksAt]->(m) RETURN m").unwrap();
        let rel = &q.r#match.unwrap().patterns[0].steps[0].rel;
        assert_eq!(rel.types, ["knows", "worksAt"]);
        assert_eq!(rel.direction, "out");
    }
}
