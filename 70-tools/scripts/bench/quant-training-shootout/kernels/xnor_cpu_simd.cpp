/* Bit-packed XNOR-popcount matmul via CPU SIMD intrinsics.
 *
 * Compiles two paths, selected at compile time:
 *   - x86_64 with AVX-512 VPOPCNTDQ + AVX-512F  (Intel Ice Lake+, AMD Zen 4+)
 *     uses _mm512_popcnt_epi32 (16 popcounts per cycle on a single SIMD lane)
 *   - aarch64 with NEON                         (Apple M-class, ARM servers)
 *     uses vcntq_u8 + horizontal add (vaddvq_u8) for popcount per uint32
 *
 * Build via torch.utils.cpp_extension.load() — see xnor_cpu_simd_setup.py.
 *
 * API (PyTorch tensor):
 *   y[B,N] = xnor_popcount(x_bits[B,P], w_bits[N,P], K, alpha, beta)
 * where:
 *   x_bits, w_bits are int32 (interpreted as uint32 bit-packed signs)
 *   K is the real inner dim (before padding to multiple of 32)
 *   alpha, beta are scalar floats (per-tensor scales)
 *
 * Algorithm per output (i,j):
 *   match = sum_p popcount( ~(x_bits[i,p] ^ w_bits[j,p]) )
 *   dot_real = 2*match - K_padded - pad   (pad = K_padded - K)
 *   y[i,j]   = alpha * beta * dot_real
 */
#include <torch/extension.h>
#include <cstdint>
#include <cstring>

#if defined(__AVX512F__) && defined(__AVX512VPOPCNTDQ__)
  #include <immintrin.h>
  #define HAVE_AVX512_POPCNT 1
#endif

#if defined(__ARM_NEON)
  #include <arm_neon.h>
  #define HAVE_NEON 1
#endif

// -- per-row popcount32 sum (returns matches over P uint32 words) --------

static inline uint64_t popcount_xnor_row(const uint32_t* x, const uint32_t* w,
                                         int64_t P) {
    uint64_t acc = 0;
    int64_t p = 0;
#if HAVE_AVX512_POPCNT
    // 16 uint32 per AVX-512 reg; one VPOPCNTD does 16 popcounts in 1 cycle.
    for (; p + 16 <= P; p += 16) {
        __m512i vx = _mm512_loadu_si512((const void*)(x + p));
        __m512i vw = _mm512_loadu_si512((const void*)(w + p));
        __m512i vxnor = _mm512_xor_si512(vx, vw);
        vxnor = _mm512_andnot_si512(vxnor, _mm512_set1_epi32(-1));  // ~xor
        __m512i pc = _mm512_popcnt_epi32(vxnor);
        // Reduce 16 lanes to scalar
        acc += (uint64_t)_mm512_reduce_add_epi32(pc);
    }
#elif HAVE_NEON
    // ARM NEON: vcntq_u8 popcounts 16 bytes (8-bit each) at once; sum to uint32.
    // We accumulate over 4 uint32 (= 1 uint32x4_t) at a time.
    uint32x4_t vacc = vdupq_n_u32(0);
    for (; p + 4 <= P; p += 4) {
        uint32x4_t vx = vld1q_u32(x + p);
        uint32x4_t vw = vld1q_u32(w + p);
        uint32x4_t vxnor = vmvnq_u32(veorq_u32(vx, vw));
        // Reinterpret as bytes, popcount, then reduce per uint32 lane
        uint8x16_t bytes = vreinterpretq_u8_u32(vxnor);
        uint8x16_t pc8 = vcntq_u8(bytes);
        // Pairwise add to get per-uint32 popcount (4 lanes of 4 bytes each)
        uint16x8_t pc16 = vpaddlq_u8(pc8);
        uint32x4_t pc32 = vpaddlq_u16(pc16);
        vacc = vaddq_u32(vacc, pc32);
    }
    acc = (uint64_t)vaddvq_u32(vacc);
#endif
    // Scalar tail (and fallback if no SIMD path compiled in)
    for (; p < P; ++p) {
        acc += (uint64_t)__builtin_popcount(~(x[p] ^ w[p]));
    }
    return acc;
}


// -- the matmul ----------------------------------------------------------

at::Tensor xnor_popcount_matmul_cpu(at::Tensor x_bits, at::Tensor w_bits,
                                    int64_t K, double alpha, double beta) {
    TORCH_CHECK(x_bits.dtype() == at::kInt, "x_bits must be int32");
    TORCH_CHECK(w_bits.dtype() == at::kInt, "w_bits must be int32");
    TORCH_CHECK(x_bits.dim() == 2 && w_bits.dim() == 2, "rank 2 expected");
    TORCH_CHECK(x_bits.is_contiguous() && w_bits.is_contiguous(), "contig");
    TORCH_CHECK(x_bits.size(1) == w_bits.size(1), "packed dim mismatch");

    int64_t B = x_bits.size(0);
    int64_t N = w_bits.size(0);
    int64_t P = x_bits.size(1);
    int64_t K_padded = P * 32;
    int64_t pad = K_padded - K;

    auto y = at::empty({B, N}, x_bits.options().dtype(at::kFloat));
    const uint32_t* x = reinterpret_cast<const uint32_t*>(x_bits.data_ptr<int32_t>());
    const uint32_t* w = reinterpret_cast<const uint32_t*>(w_bits.data_ptr<int32_t>());
    float* y_ptr = y.data_ptr<float>();
    float scale = (float)(alpha * beta);

    at::parallel_for(0, B * N, 64, [&](int64_t a, int64_t b) {
        for (int64_t k = a; k < b; ++k) {
            int64_t i = k / N;
            int64_t j = k % N;
            uint64_t m = popcount_xnor_row(x + i * P, w + j * P, P);
            int64_t dot = 2 * (int64_t)m - K_padded - pad;
            y_ptr[k] = scale * (float)dot;
        }
    });
    return y;
}


// -- backend name --------------------------------------------------------

std::string xnor_cpu_backend() {
#if HAVE_AVX512_POPCNT
    return "avx512_vpopcntdq";
#elif HAVE_NEON
    return "arm_neon_vcntq";
#else
    return "scalar_builtin_popcount";
#endif
}


PYBIND11_MODULE(TORCH_EXTENSION_NAME, m) {
    m.def("xnor_popcount_matmul_cpu", &xnor_popcount_matmul_cpu,
          "Bit-packed XNOR-popcount matmul on CPU (SIMD)");
    m.def("xnor_cpu_backend", &xnor_cpu_backend,
          "Returns the compiled CPU backend name");
}
