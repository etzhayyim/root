import base64, json, urllib.request, sys

OP_DID="did:key:ze2e169933f9bcc6cb218e083b3d2a80c5a5a2b92fbf3cb41b4d5283ce3f6939f"
URL="http://localhost:8077"
WASM="40-engine/legal-aid-wasm-guest/target/wasm32-wasip1/release/chigiri_legal_aid_guest.wasm"

# ── minimal CBOR encoder ──
def c_uint(n):
    if n<24: return bytes([n])
    if n<256: return bytes([0x18,n])
    if n<65536: return bytes([0x19,n>>8,n&0xFF])
    raise ValueError(n)
def text(s):
    b=s.encode();
    if len(b)<24: return bytes([0x60|len(b)])+b
    if len(b)<256: return bytes([0x78,len(b)])+b
    return bytes([0x79,len(b)>>8,len(b)&0xFF])+b
def boolean(v): return b'\xf5' if v else b'\xf4'
NULL=b'\xf6'
def arr_u8(data):  # CBOR array of u8 ints (matches serde Vec<u8>)
    n=len(data)
    if n<24: head=bytes([0x80|n])
    elif n<256: head=bytes([0x98,n])
    elif n<65536: head=bytes([0x99,n>>8,n&0xFF])
    else: head=bytes([0x9a,(n>>24)&0xFF,(n>>16)&0xFF,(n>>8)&0xFF,n&0xFF])
    return head + b''.join(c_uint(x) for x in data)
def cmap(pairs):
    out=bytes([0xA0|len(pairs)])
    for k,v in pairs: out+=text(k)+v
    return out

def intake_cbor(adherent,jx,lane,zero,counsel_did,counsel_lic):
    pairs=[("adherent_did",text(adherent)),("jurisdiction",text(jx)),("lane",text(lane)),
           ("zero_compensation",boolean(zero)),
           ("supervising_counsel_did", text(counsel_did) if counsel_did else NULL),
           ("counsel_license_jurisdiction", text(counsel_lic) if counsel_lic else NULL)]
    return cmap(pairs)

def ctx_cbor(graph,args):
    return cmap([("graph",text(graph)),("session_cid",NULL),("args_cbor",arr_u8(args))])

def jwt():
    b=lambda o: base64.urlsafe_b64encode(json.dumps(o,separators=(',',':')).encode()).rstrip(b'=').decode()
    return b({'alg':'HS256','typ':'JWT'})+'.'+b({'sub':OP_DID,'exp':9999999999})+'.opsig'

def run(name, args_cbor, graph="etzhayyim-legal-aid"):
    wasm_b64=base64.b64encode(open(WASM,'rb').read()).decode()
    ctx_b64=base64.b64encode(ctx_cbor(graph,args_cbor)).decode()
    body=json.dumps({"program_cid":"chigiri-legal-aid-v0.1.0","program_type":"wasm-node",
        "agent_did":OP_DID,"wasm_b64":wasm_b64,"ctx_b64":ctx_b64}).encode()
    req=urllib.request.Request(URL+"/xrpc/com.etzhayyim.apps.kotoba.invoke.run",data=body,
        headers={"Content-Type":"application/json","Authorization":"Bearer "+jwt()},method="POST")
    try:
        j=json.load(urllib.request.urlopen(req,timeout=60))
        out=base64.b64decode(j.get("output_b64","")) if j.get("output_b64") else b''
        print(f"[{name}] status={j.get('status')} assert_count={j.get('assert_count')} gas={j.get('gas_used')} journal={len(j.get('journal_cids',[]))}")
        print(f"         output(cbor {len(out)}B) head={out[:60].hex()}")
        return j
    except urllib.error.HTTPError as e:
        print(f"[{name}] HTTP {e.code}: {e.read().decode()[:200]}")

print("=== VALID intake (jpn + jpn counsel + zero-comp) -> expect assert_count=1 ===")
run("valid", intake_cbor("did:web:adherent","jpn","advice",True,"did:web:lawyer.jp","jpn"))
print("=== G15 violation (zero_compensation=false) -> expect rejected, assert_count=0 ===")
run("g15", intake_cbor("did:web:adherent","jpn","advice",False,"did:web:lawyer.jp","jpn"))
print("=== G16 violation (Austria verify-required) -> expect rejected ===")
run("g16-aut", intake_cbor("did:web:adherent","aut","advice",True,"did:web:lawyer.at","aut"))
print("=== G16 violation (no counsel) -> expect rejected ===")
run("g16-nocounsel", intake_cbor("did:web:adherent","jpn","advice",True,"",""))
