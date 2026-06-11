//! Stable, lossless mapping between kg-projector nodeIds / edge predicates
//! and OxiGraph IRIs. See `README.md` § "IRI mapping" for the contract.

use oxigraph::model::NamedNode;
use percent_encoding::{utf8_percent_encode, AsciiSet, CONTROLS};

const STRICT: &AsciiSet = &CONTROLS
    .add(b' ')
    .add(b'"')
    .add(b'<')
    .add(b'>')
    .add(b'\\')
    .add(b'^')
    .add(b'`')
    .add(b'{')
    .add(b'|')
    .add(b'}')
    .add(b'#')
    .add(b'?')
    .add(b'/')
    .add(b'%')
    .add(b'&')
    .add(b'=')
    .add(b'+')
    .add(b';')
    .add(b'@')
    .add(b'$')
    .add(b',');

pub const NODE_PREFIX: &str = "https://etzhayyim.com/kg/n/";
pub const PREDICATE_PREFIX: &str = "https://etzhayyim.com/kg/p#";
pub const VOCAB_PREFIX: &str = "https://etzhayyim.com/kg/v#";

pub fn node_iri(node_id: &str) -> NamedNode {
    let encoded = utf8_percent_encode(node_id, STRICT).to_string();
    NamedNode::new_unchecked(format!("{NODE_PREFIX}{encoded}"))
}

pub fn predicate_iri(predicate: &str) -> NamedNode {
    let encoded = utf8_percent_encode(predicate, STRICT).to_string();
    NamedNode::new_unchecked(format!("{PREDICATE_PREFIX}{encoded}"))
}

pub fn vocab_iri(field: &str) -> NamedNode {
    NamedNode::new_unchecked(format!("{VOCAB_PREFIX}{field}"))
}
