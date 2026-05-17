// gmm — Lightweight Gaussian Mixture Model (k-means + soft assignment).
// No external dependencies (no gonum). Used by gftd coverage infer discover.
//
// Algorithm:
//   1. k-means++ initialization
//   2. Lloyd's iteration (hard assignment) to find centroids
//   3. Soft assignment via Gaussian posterior (diagonal covariance)
//
// Design: 90-docs/260416-coverage-infer-statistical-entity-resolution.md
package main

import (
	"fmt"
	"math"
	"math/rand"
	"sort"
)

// GMMCluster represents a discovered cluster with centroid and members.
type GMMCluster struct {
	ID          int       `json:"id"`
	Centroid    []float64 `json:"centroid"`
	MemberCount int       `json:"memberCount"`
	Variance    float64   `json:"variance"`     // avg variance across dims
	Members     []int     `json:"-"`            // indices into input data
}

// GMMResult holds the full clustering output.
type GMMResult struct {
	K           int          `json:"k"`
	Clusters    []GMMCluster `json:"clusters"`
	Assignments []int        `json:"assignments"` // input index → cluster ID
	Iterations  int          `json:"iterations"`
	Inertia     float64      `json:"inertia"`     // sum of squared distances to centroids
}

// GMMOptions configures the clustering.
type GMMOptions struct {
	K           int     // number of clusters
	MaxIter     int     // max iterations (default 100)
	Tolerance   float64 // convergence threshold (default 1e-6)
	Seed        int64   // random seed (0 = time-based)
}

// RunGMM performs k-means clustering with soft assignment on the input data.
// data is a flat slice of row-major feature vectors: data[i*dims..(i+1)*dims].
// Returns GMMResult with cluster assignments and centroids.
func RunGMM(data [][]float64, opts GMMOptions) (*GMMResult, error) {
	n := len(data)
	if n == 0 {
		return nil, fmt.Errorf("empty input data")
	}
	dims := len(data[0])
	if dims == 0 {
		return nil, fmt.Errorf("zero-dimensional features")
	}

	k := opts.K
	if k <= 0 {
		// Auto-select k using elbow heuristic: sqrt(n/2)
		k = int(math.Sqrt(float64(n) / 2.0))
		if k < 2 {
			k = 2
		}
		if k > n {
			k = n
		}
	}
	if k > n {
		k = n
	}

	maxIter := opts.MaxIter
	if maxIter <= 0 {
		maxIter = 100
	}
	tol := opts.Tolerance
	if tol <= 0 {
		tol = 1e-6
	}

	rng := rand.New(rand.NewSource(opts.Seed))
	if opts.Seed == 0 {
		rng = rand.New(rand.NewSource(rand.Int63()))
	}

	// k-means++ initialization
	centroids := kmeansppInit(data, k, dims, rng)

	assignments := make([]int, n)
	var iterations int
	var inertia float64

	for iter := 0; iter < maxIter; iter++ {
		iterations = iter + 1

		// E-step: assign each point to nearest centroid
		newInertia := 0.0
		for i, point := range data {
			bestK := 0
			bestDist := math.MaxFloat64
			for c := 0; c < k; c++ {
				d := sqDist(point, centroids[c])
				if d < bestDist {
					bestDist = d
					bestK = c
				}
			}
			assignments[i] = bestK
			newInertia += bestDist
		}

		// Check convergence
		if iter > 0 && math.Abs(inertia-newInertia) < tol {
			inertia = newInertia
			break
		}
		inertia = newInertia

		// M-step: recompute centroids
		counts := make([]int, k)
		newCentroids := make([][]float64, k)
		for c := 0; c < k; c++ {
			newCentroids[c] = make([]float64, dims)
		}
		for i, point := range data {
			c := assignments[i]
			counts[c]++
			for d := 0; d < dims; d++ {
				newCentroids[c][d] += point[d]
			}
		}
		for c := 0; c < k; c++ {
			if counts[c] > 0 {
				for d := 0; d < dims; d++ {
					newCentroids[c][d] /= float64(counts[c])
				}
			}
			// Keep old centroid if cluster is empty
		}
		centroids = newCentroids
	}

	// Build cluster results
	clusters := make([]GMMCluster, k)
	for c := 0; c < k; c++ {
		clusters[c] = GMMCluster{
			ID:       c,
			Centroid: centroids[c],
			Members:  make([]int, 0),
		}
	}
	for i, c := range assignments {
		clusters[c].Members = append(clusters[c].Members, i)
		clusters[c].MemberCount++
	}

	// Compute per-cluster variance
	for c := 0; c < k; c++ {
		if clusters[c].MemberCount <= 1 {
			clusters[c].Variance = 0
			continue
		}
		totalVar := 0.0
		for _, idx := range clusters[c].Members {
			totalVar += sqDist(data[idx], centroids[c])
		}
		clusters[c].Variance = totalVar / float64(clusters[c].MemberCount)
	}

	// Sort clusters by member count descending
	sort.Slice(clusters, func(i, j int) bool {
		return clusters[i].MemberCount > clusters[j].MemberCount
	})
	// Re-index IDs after sort
	idMap := make(map[int]int) // old ID → new ID
	for newID := range clusters {
		idMap[clusters[newID].ID] = newID
		clusters[newID].ID = newID
	}
	for i := range assignments {
		assignments[i] = idMap[assignments[i]]
	}

	return &GMMResult{
		K:           k,
		Clusters:    clusters,
		Assignments: assignments,
		Iterations:  iterations,
		Inertia:     inertia,
	}, nil
}

// SoftAssign computes Gaussian posterior probability of a point belonging to each cluster.
// Returns probabilities[clusterID] summing to 1.0.
func SoftAssign(point []float64, result *GMMResult) []float64 {
	k := len(result.Clusters)
	logProbs := make([]float64, k)
	maxLog := -math.MaxFloat64

	for c := 0; c < k; c++ {
		cl := result.Clusters[c]
		variance := cl.Variance
		if variance < 1e-10 {
			variance = 1e-10
		}
		d := sqDist(point, cl.Centroid)
		// Log of Gaussian density (up to normalization constant)
		logP := -d/(2.0*variance) + math.Log(float64(cl.MemberCount))
		logProbs[c] = logP
		if logP > maxLog {
			maxLog = logP
		}
	}

	// Log-sum-exp for numerical stability
	sumExp := 0.0
	probs := make([]float64, k)
	for c := 0; c < k; c++ {
		probs[c] = math.Exp(logProbs[c] - maxLog)
		sumExp += probs[c]
	}
	if sumExp > 0 {
		for c := 0; c < k; c++ {
			probs[c] /= sumExp
		}
	}
	return probs
}

// kmeansppInit selects initial centroids using k-means++ algorithm.
func kmeansppInit(data [][]float64, k, dims int, rng *rand.Rand) [][]float64 {
	n := len(data)
	centroids := make([][]float64, 0, k)

	// First centroid: random
	first := rng.Intn(n)
	c0 := make([]float64, dims)
	copy(c0, data[first])
	centroids = append(centroids, c0)

	// Remaining centroids: probability proportional to D(x)^2
	dists := make([]float64, n)
	for i := 1; i < k; i++ {
		totalDist := 0.0
		for j, point := range data {
			minDist := math.MaxFloat64
			for _, c := range centroids {
				d := sqDist(point, c)
				if d < minDist {
					minDist = d
				}
			}
			dists[j] = minDist
			totalDist += minDist
		}

		if totalDist <= 0 {
			// All points identical; pick random
			idx := rng.Intn(n)
			cn := make([]float64, dims)
			copy(cn, data[idx])
			centroids = append(centroids, cn)
			continue
		}

		// Weighted random selection
		target := rng.Float64() * totalDist
		cumul := 0.0
		chosen := n - 1
		for j := 0; j < n; j++ {
			cumul += dists[j]
			if cumul >= target {
				chosen = j
				break
			}
		}
		cn := make([]float64, dims)
		copy(cn, data[chosen])
		centroids = append(centroids, cn)
	}

	return centroids
}

// sqDist computes squared Euclidean distance between two vectors.
func sqDist(a, b []float64) float64 {
	d := 0.0
	for i := range a {
		if i < len(b) {
			diff := a[i] - b[i]
			d += diff * diff
		}
	}
	return d
}

// AutoSelectK uses the elbow method to suggest an optimal k.
// Runs k-means for k=2..maxK and returns the k with largest inertia drop ratio.
func AutoSelectK(data [][]float64, maxK int, seed int64) int {
	if len(data) < 4 {
		return gmmMin(2, len(data))
	}
	if maxK <= 0 {
		maxK = int(math.Sqrt(float64(len(data))))
		if maxK < 3 {
			maxK = 3
		}
		if maxK > 20 {
			maxK = 20
		}
	}
	if maxK > len(data) {
		maxK = len(data)
	}

	inertias := make([]float64, maxK+1)
	for k := 2; k <= maxK; k++ {
		result, err := RunGMM(data, GMMOptions{K: k, Seed: seed})
		if err != nil {
			continue
		}
		inertias[k] = result.Inertia
	}

	// Find largest proportional drop
	bestK := 2
	bestDrop := 0.0
	for k := 3; k <= maxK; k++ {
		if inertias[k-1] <= 0 {
			continue
		}
		drop := (inertias[k-1] - inertias[k]) / inertias[k-1]
		prevDrop := 0.0
		if k > 3 && inertias[k-2] > 0 {
			prevDrop = (inertias[k-2] - inertias[k-1]) / inertias[k-2]
		}
		// Elbow = where the drop ratio decreases most
		elbowScore := prevDrop - drop
		if elbowScore > bestDrop {
			bestDrop = elbowScore
			bestK = k - 1
		}
	}
	return bestK
}

func gmmMin(a, b int) int {
	if a < b {
		return a
	}
	return b
}
