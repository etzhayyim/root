/**
 * Hoge Extism Plugin — AssemblyScript Shannon entropy module.
 *
 * Pattern B: Extism PDK pattern.
 * Host-side: @extism/js-sdk createPlugin(module, { useWasi: false })
 * Plugin-side: @extism/as-pdk Host.inputString() / Host.outputString()
 *
 * ABI:
 *   plugin.call("shannonScore", text: string) → JSON string
 *   result: {"score": f64, "len": i32, "pattern": "extism"}
 *
 * WIT contract (design-time, maps to same interface as manual ABI):
 *   shannon-score: func(params: string) -> result<string, string>
 */

import { Host } from "@extism/as-pdk";

/** Extism plugins use a no-op abort; errors propagate via return codes. */
function myAbort(
  _message: string | null,
  _fileName: string | null,
  _line: u32,
  _col: u32,
): void {}


/**
 * Compute Shannon entropy of the input string.
 * Input:  raw UTF-16 text from Host.inputString()
 * Output: JSON {"score": f64, "len": i32, "pattern": "extism"}
 */
export function shannonScore(): i32 {
  const text = Host.inputString();
  const n = text.length;

  if (n === 0) {
    Host.outputString('{"score":0,"len":0,"pattern":"extism"}');
    return 0;
  }

  // Count char-code-unit frequencies (lower byte, ASCII-range works for most text)
  const freq = new Int32Array(256);
  for (let i = 0; i < n; i++) {
    freq[text.charCodeAt(i) & 0xFF]++;
  }

  // H = -Σ p · log₂(p)
  let h: f64 = 0.0;
  const fn_: f64 = f64(n);
  for (let i = 0; i < 256; i++) {
    if (freq[i] > 0) {
      const p: f64 = f64(freq[i]) / fn_;
      h -= p * (Math.log(p) / Math.LN2);
    }
  }

  Host.outputString(
    '{"score":' + h.toString() +
    ',"len":'   + n.toString() +
    ',"pattern":"extism"}'
  );
  return 0;
}
