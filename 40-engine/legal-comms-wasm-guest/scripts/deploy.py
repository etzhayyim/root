import base64, json, urllib.request

OP_DID="did:key:ze2e169933f9bcc6cb218e083b3d2a80c5a5a2b92fbf3cb41b4d5283ce3f6939f"
URL="http://localhost:8077"
WASM="40-engine/legal-comms-wasm-guest/target/wasm32-wasip1/release/chigiri_legal_comms_guest.wasm"

def c_uint(n):
    if n<24: return bytes([n])
    if n<256: return bytes([0x18,n])
    return bytes([0x19,n>>8,n&0xFF])
def text(s):
    b=s.encode()
    if len(b)<24: return bytes([0x60|len(b)])+b
    if len(b)<256: return bytes([0x78,len(b)])+b
    return bytes([0x79,len(b)>>8,len(b)&0xFF])+b
NULL=b'\xf6'
def arr_u8(data):
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
def opt(v): return text(v) if v else NULL

def act_cbor(dest_jx, klass, transport, payload, endpoint, counsel, lic, sig):
    return cmap([("destination_jurisdiction",text(dest_jx)),("artifact_class",text(klass)),
        ("transport",text(transport)),("payload_cid",text(payload)),
        ("destination_endpoint",text(endpoint)),("counsel_did",opt(counsel)),
        ("counsel_license_jurisdiction",opt(lic)),("counsel_signature_ref",opt(sig))])
def ctx_cbor(graph,args): return cmap([("graph",text(graph)),("session_cid",NULL),("args_cbor",arr_u8(args))])
def jwt():
    b=lambda o: base64.urlsafe_b64encode(json.dumps(o,separators=(',',':')).encode()).rstrip(b'=').decode()
    return b({'alg':'HS256','typ':'JWT'})+'.'+b({'sub':OP_DID,'exp':9999999999})+'.opsig'

def run(name, args, graph="etzhayyim-legal-comms"):
    wasm_b64=base64.b64encode(open(WASM,'rb').read()).decode()
    ctx_b64=base64.b64encode(ctx_cbor(graph,args)).decode()
    body=json.dumps({"program_cid":"chigiri-legal-comms-v0.1.0","program_type":"wasm-node",
        "agent_did":OP_DID,"wasm_b64":wasm_b64,"ctx_b64":ctx_b64}).encode()
    req=urllib.request.Request(URL+"/xrpc/com.etzhayyim.apps.kotoba.invoke.run",data=body,
        headers={"Content-Type":"application/json","Authorization":"Bearer "+jwt()},method="POST")
    try:
        j=json.load(urllib.request.urlopen(req,timeout=60))
        out=base64.b64decode(j.get("output_b64","")) if j.get("output_b64") else b''
        print(f"[{name}] status={j.get('status')} assert_count={j.get('assert_count')} gas={j.get('gas_used')} -> {out[:48].decode('latin1')}")
        return j
    except urllib.error.HTTPError as e:
        print(f"[{name}] HTTP {e.code}: {e.read().decode()[:160]}")

print("=== VALID: court-filing + jpn counsel + own signature -> authorized, assert_count=1 ===")
run("valid", act_cbor("jpn","court-filing","fax","bafyDoc","fax:+81","did:web:lawyer.jp","jpn","sig:counsel-own-key"))
print("=== G18: no actuation -> refused ===")
run("g18-noactuation", act_cbor("jpn","court-filing","fax","bafyDoc","fax:+81","","",""))
print("=== G18: counsel licensed in wrong jurisdiction -> refused ===")
run("g18-wrongjx", act_cbor("jpn","pleading","email","bafyDoc","x@court","did:web:lawyer.us","usa","sig"))
print("=== G18: missing own signature -> refused ===")
run("g18-nosig", act_cbor("jpn","demand-letter","postal","bafyDoc","addr","did:web:lawyer.jp","jpn",""))
