/* Bit-packed XNOR-popcount matmul CUDA/HIP kernel.
 *
 * On NVIDIA: compiled by nvcc; uses __popc(uint) which maps to a single
 * cycle on SM 7.0+ (POPC instruction).
 * On AMD ROCm: compiled by hipcc (PyTorch's HIPIFY converts CUDA -> HIP);
 * __popc lowers to V_BCNT_U32_B32 on RDNA/CDNA.
 *
 * Tiled implementation: each threadblock handles a TILE_B × TILE_N
 * sub-block of the output. K-dim is reduced in a loop, with packed
 * uint32 vectors loaded P-at-a-time per thread.
 *
 * API (same as the CPU version):
 *   y[B,N] = xnor_popcount(x_bits[B,P], w_bits[N,P], K, alpha, beta)
 */
#include <torch/extension.h>
#include <cuda_runtime.h>
#include <stdint.h>

#ifndef TILE_B
#define TILE_B 16
#endif
#ifndef TILE_N
#define TILE_N 16
#endif

__global__ void xnor_popcount_kernel(
    const uint32_t* __restrict__ x,  // [B, P]
    const uint32_t* __restrict__ w,  // [N, P]
    float* __restrict__ y,           // [B, N]
    int B, int N, int P, int K_padded, int pad,
    float scale
) {
    int i = blockIdx.x * TILE_B + threadIdx.x;
    int j = blockIdx.y * TILE_N + threadIdx.y;
    if (i >= B || j >= N) return;

    const uint32_t* xi = x + (size_t)i * P;
    const uint32_t* wj = w + (size_t)j * P;
    unsigned int match = 0u;
    #pragma unroll 4
    for (int p = 0; p < P; ++p) {
        match += __popc(~(xi[p] ^ wj[p]));
    }
    int dot = (int)(2u * match) - K_padded - pad;
    y[(size_t)i * N + j] = scale * (float)dot;
}


at::Tensor xnor_popcount_matmul_cuda(at::Tensor x_bits, at::Tensor w_bits,
                                     int64_t K, double alpha, double beta) {
    TORCH_CHECK(x_bits.dtype() == at::kInt, "x_bits must be int32");
    TORCH_CHECK(w_bits.dtype() == at::kInt, "w_bits must be int32");
    TORCH_CHECK(x_bits.is_cuda() && w_bits.is_cuda(), "x and w must be on cuda");
    TORCH_CHECK(x_bits.is_contiguous() && w_bits.is_contiguous(), "contig");
    TORCH_CHECK(x_bits.size(1) == w_bits.size(1), "packed dim mismatch");

    int B = (int)x_bits.size(0);
    int N = (int)w_bits.size(0);
    int P = (int)x_bits.size(1);
    int K_padded = P * 32;
    int pad = K_padded - (int)K;
    float scale = (float)(alpha * beta);

    auto y = at::empty({B, N}, x_bits.options().dtype(at::kFloat));

    dim3 threads(TILE_B, TILE_N);
    dim3 blocks((B + TILE_B - 1) / TILE_B, (N + TILE_N - 1) / TILE_N);
    xnor_popcount_kernel<<<blocks, threads>>>(
        reinterpret_cast<const uint32_t*>(x_bits.data_ptr<int32_t>()),
        reinterpret_cast<const uint32_t*>(w_bits.data_ptr<int32_t>()),
        y.data_ptr<float>(),
        B, N, P, K_padded, pad, scale
    );
    return y;
}


std::string xnor_cuda_backend() {
#ifdef __HIP_PLATFORM_AMD__
    return "hip_amd_v_bcnt";
#elif defined(__CUDACC__)
    return "cuda_nvidia_popc";
#else
    return "unknown";
#endif
}


PYBIND11_MODULE(TORCH_EXTENSION_NAME, m) {
    m.def("xnor_popcount_matmul_cuda", &xnor_popcount_matmul_cuda,
          "Bit-packed XNOR-popcount matmul (CUDA/HIP)");
    m.def("xnor_cuda_backend", &xnor_cuda_backend,
          "Returns 'cuda_nvidia_popc' or 'hip_amd_v_bcnt'");
}
