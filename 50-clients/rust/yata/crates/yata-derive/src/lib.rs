//! `yata-derive` — proc-macros for the `yata` client.
//!
//! Derives `VertexSpec` / `EdgeSpec` (re-exported from `yata-schema`)
//! from a struct definition tagged with `#[yata(...)]` field attributes.
//!
//! ## `#[derive(Vertex)]`
//!
//! ```ignore
//! use yata::prelude::*;
//!
//! #[derive(Vertex, Debug, Clone)]
//! #[yata(label = "person")]
//! struct Person {
//!     #[yata(pk)]
//!     id: String,
//!     name: String,
//!     age: i32,
//!     #[yata(vector(dim = 768))]
//!     embedding: Vec<f32>,
//! }
//! ```
//!
//! Field attributes:
//!
//! - `#[yata(pk)]`               — mark this field as the primary key (exactly one per struct)
//! - `#[yata(vector(dim = N))]`  — mark this field as a `REAL[]` vector with declared dim
//! - `#[yata(skip)]`             — exclude this field from the table schema (transient)
//!
//! Struct attribute:
//!
//! - `#[yata(label = "name")]`   — required. Used for `vertex_<label>` table naming.
//! - `#[yata(schema = "ns")]`    — optional, defaults to `"public"`.
//!
//! ## `#[derive(Edge)]`
//!
//! ```ignore
//! #[derive(Edge, Debug, Clone)]
//! #[yata(type = "knows", from = Person, to = Person)]
//! struct Knows {
//!     #[yata(pk)]
//!     id: String,
//!     since: chrono::DateTime<chrono::Utc>,
//!     weight: f32,
//! }
//! ```
//!
//! Struct attribute:
//!
//! - `#[yata(type = "name")]`    — required. Used for `edge_<type>` table naming.
//! - `#[yata(from = T, to = U)]` — optional but recommended for type checks at the builder.

#![deny(missing_debug_implementations)]
#![warn(missing_docs)]

use proc_macro::TokenStream;
use proc_macro2::TokenStream as TokenStream2;
use quote::quote;
use syn::{parse_macro_input, DeriveInput, Data, Fields};

/// `#[derive(Vertex)]` — see crate-level docs for the field/struct attributes.
#[proc_macro_derive(Vertex, attributes(yata))]
pub fn derive_vertex(input: TokenStream) -> TokenStream {
    let input = parse_macro_input!(input as DeriveInput);
    expand_vertex(input)
        .unwrap_or_else(|e| e.to_compile_error())
        .into()
}

/// `#[derive(Edge)]` — see crate-level docs for the field/struct attributes.
#[proc_macro_derive(Edge, attributes(yata))]
pub fn derive_edge(input: TokenStream) -> TokenStream {
    let input = parse_macro_input!(input as DeriveInput);
    expand_edge(input)
        .unwrap_or_else(|e| e.to_compile_error())
        .into()
}

// ──────────────────────────────────────────────────────────────────────
// Expansion — Vertex
// ──────────────────────────────────────────────────────────────────────

fn expand_vertex(input: DeriveInput) -> syn::Result<TokenStream2> {
    let name = &input.ident;
    let label = parse_struct_label(&input.attrs, "label")?;
    let schema_name = parse_struct_string_opt(&input.attrs, "schema")?
        .unwrap_or_else(|| "public".to_string());

    let fields = struct_named_fields(&input)?;
    let mut col_decls = Vec::<TokenStream2>::new();
    let mut pk_field: Option<&syn::Ident> = None;

    for f in &fields {
        let fname = f.ident.as_ref().expect("named field");
        if has_skip(&f.attrs) {
            continue;
        }
        let is_pk = has_pk(&f.attrs);
        let vector_dim = parse_vector_dim(&f.attrs)?;
        let ty_str = column_type_for(&f.ty, vector_dim.is_some());
        let dim = vector_dim.unwrap_or(0);
        let is_vector = vector_dim.is_some();
        let fname_str = fname.to_string();
        col_decls.push(quote! {
            ::yata_schema::Column {
                name: #fname_str,
                ty: ::yata_schema::ColumnType::#ty_str,
                is_pk: #is_pk,
                is_vector: #is_vector,
                vector_dim: #dim,
            },
        });
        if is_pk {
            if pk_field.is_some() {
                return Err(syn::Error::new_spanned(
                    fname,
                    "yata: a Vertex / Edge must declare exactly one #[yata(pk)] field",
                ));
            }
            pk_field = Some(fname);
        }
    }

    let pk = pk_field.ok_or_else(|| {
        syn::Error::new_spanned(name, "yata: missing #[yata(pk)] attribute on any field")
    })?;

    Ok(quote! {
        impl ::yata_schema::VertexSpec for #name {
            const LABEL: &'static str = #label;
            const SCHEMA: &'static str = #schema_name;
            const COLUMNS: &'static [::yata_schema::Column] = &[ #( #col_decls )* ];

            fn pk(&self) -> ::std::string::String {
                ::std::string::ToString::to_string(&self.#pk)
            }

            fn into_row(self) -> ::std::result::Result<::yata_schema::Row, ::yata_schema::SchemaError> {
                ::std::result::Result::Err(::yata_schema::SchemaError::MissingColumn(
                    ::std::string::String::from(
                        "yata-derive: into_row codec is not yet implemented (P5 v0.1 skeleton)",
                    ),
                ))
            }

            fn from_row(_row: ::yata_schema::Row) -> ::std::result::Result<Self, ::yata_schema::SchemaError> {
                ::std::result::Result::Err(::yata_schema::SchemaError::MissingColumn(
                    ::std::string::String::from(
                        "yata-derive: from_row codec is not yet implemented (P5 v0.1 skeleton)",
                    ),
                ))
            }
        }
    })
}

// ──────────────────────────────────────────────────────────────────────
// Expansion — Edge
// ──────────────────────────────────────────────────────────────────────

fn expand_edge(input: DeriveInput) -> syn::Result<TokenStream2> {
    let name = &input.ident;
    let edge_type = parse_struct_label(&input.attrs, "type")?;
    let schema_name = parse_struct_string_opt(&input.attrs, "schema")?
        .unwrap_or_else(|| "public".to_string());

    let fields = struct_named_fields(&input)?;
    let mut col_decls = Vec::<TokenStream2>::new();
    let mut pk_field: Option<&syn::Ident> = None;

    for f in &fields {
        let fname = f.ident.as_ref().expect("named field");
        if has_skip(&f.attrs) {
            continue;
        }
        let is_pk = has_pk(&f.attrs);
        let vector_dim = parse_vector_dim(&f.attrs)?;
        let ty_str = column_type_for(&f.ty, vector_dim.is_some());
        let dim = vector_dim.unwrap_or(0);
        let is_vector = vector_dim.is_some();
        let fname_str = fname.to_string();
        col_decls.push(quote! {
            ::yata_schema::Column {
                name: #fname_str,
                ty: ::yata_schema::ColumnType::#ty_str,
                is_pk: #is_pk,
                is_vector: #is_vector,
                vector_dim: #dim,
            },
        });
        if is_pk {
            pk_field = Some(fname);
        }
    }

    let pk = pk_field.ok_or_else(|| {
        syn::Error::new_spanned(name, "yata: missing #[yata(pk)] attribute on any field")
    })?;

    Ok(quote! {
        impl ::yata_schema::EdgeSpec for #name {
            const EDGE_TYPE: &'static str = #edge_type;
            const SCHEMA: &'static str = #schema_name;
            const COLUMNS: &'static [::yata_schema::Column] = &[ #( #col_decls )* ];

            fn pk(&self) -> ::std::string::String {
                ::std::string::ToString::to_string(&self.#pk)
            }

            fn into_row(self) -> ::std::result::Result<::yata_schema::Row, ::yata_schema::SchemaError> {
                ::std::result::Result::Err(::yata_schema::SchemaError::MissingColumn(
                    ::std::string::String::from(
                        "yata-derive: into_row codec is not yet implemented (P5 v0.1 skeleton)",
                    ),
                ))
            }

            fn from_row(_row: ::yata_schema::Row) -> ::std::result::Result<Self, ::yata_schema::SchemaError> {
                ::std::result::Result::Err(::yata_schema::SchemaError::MissingColumn(
                    ::std::string::String::from(
                        "yata-derive: from_row codec is not yet implemented (P5 v0.1 skeleton)",
                    ),
                ))
            }
        }
    })
}

// ──────────────────────────────────────────────────────────────────────
// Attribute helpers
// ──────────────────────────────────────────────────────────────────────

fn struct_named_fields(input: &DeriveInput) -> syn::Result<Vec<&syn::Field>> {
    let Data::Struct(s) = &input.data else {
        return Err(syn::Error::new_spanned(
            &input.ident,
            "yata: #[derive(Vertex|Edge)] only supports structs",
        ));
    };
    let Fields::Named(named) = &s.fields else {
        return Err(syn::Error::new_spanned(
            &input.ident,
            "yata: #[derive(Vertex|Edge)] only supports named fields",
        ));
    };
    Ok(named.named.iter().collect())
}

fn parse_struct_label(attrs: &[syn::Attribute], key: &str) -> syn::Result<String> {
    parse_struct_string_opt(attrs, key)?.ok_or_else(|| {
        syn::Error::new(
            proc_macro2::Span::call_site(),
            format!("yata: missing #[yata({} = \"...\")] attribute", key),
        )
    })
}

fn parse_struct_string_opt(attrs: &[syn::Attribute], key: &str) -> syn::Result<Option<String>> {
    let mut out: Option<String> = None;
    for a in attrs {
        if !a.path().is_ident("yata") {
            continue;
        }
        a.parse_nested_meta(|meta| {
            if meta.path.is_ident(key) {
                let v: syn::LitStr = meta.value()?.parse()?;
                out = Some(v.value());
            }
            Ok(())
        })?;
    }
    Ok(out)
}

fn has_pk(attrs: &[syn::Attribute]) -> bool {
    for a in attrs {
        if !a.path().is_ident("yata") {
            continue;
        }
        let mut found = false;
        let _ = a.parse_nested_meta(|meta| {
            if meta.path.is_ident("pk") {
                found = true;
            }
            Ok(())
        });
        if found {
            return true;
        }
    }
    false
}

fn has_skip(attrs: &[syn::Attribute]) -> bool {
    for a in attrs {
        if !a.path().is_ident("yata") {
            continue;
        }
        let mut found = false;
        let _ = a.parse_nested_meta(|meta| {
            if meta.path.is_ident("skip") {
                found = true;
            }
            Ok(())
        });
        if found {
            return true;
        }
    }
    false
}

fn parse_vector_dim(attrs: &[syn::Attribute]) -> syn::Result<Option<usize>> {
    let mut dim: Option<usize> = None;
    for a in attrs {
        if !a.path().is_ident("yata") {
            continue;
        }
        let _ = a.parse_nested_meta(|outer| {
            if outer.path.is_ident("vector") {
                outer.parse_nested_meta(|inner| {
                    if inner.path.is_ident("dim") {
                        let v: syn::LitInt = inner.value()?.parse()?;
                        dim = Some(v.base10_parse::<usize>()?);
                    }
                    Ok(())
                })?;
            }
            Ok(())
        });
    }
    Ok(dim)
}

/// Best-effort mapping from Rust type → ColumnType variant identifier.
/// Falls back to `Varchar` when the type is unrecognised; the impl is
/// intentionally simple at the v0.1 skeleton.
fn column_type_for(ty: &syn::Type, is_vector: bool) -> syn::Ident {
    if is_vector {
        return syn::Ident::new("RealArray", proc_macro2::Span::call_site());
    }
    let ts = quote! { #ty }.to_string();
    let ident = match ts.as_str() {
        "String" | "& 'static str" | "& str" => "Varchar",
        "i32" => "Int",
        "i64" => "BigInt",
        "f32" | "f64" => "Double",
        "bool" => "Boolean",
        s if s.contains("DateTime")  => "Timestamptz",
        s if s.contains("NaiveDate") => "Date",
        s if s.contains("Vec < f32 >") || s.contains("Vec<f32>") => "RealArray",
        _ => "Varchar",
    };
    syn::Ident::new(ident, proc_macro2::Span::call_site())
}
