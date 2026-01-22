# Layout Pipeline: Mathematical Formulation

This document provides the complete mathematical formulation of the layout algorithms implemented in PyPotteryLayout. For a more accessible overview, see the main supplementary materials.

---

## 1. Adaptive Grid Layout

The system positions artifacts in a predefined matrix of $m$ rows and $n$ columns:

$$
Grid_{layout} = \{(i,j) : 1 \leq i \leq m, 1 \leq j \leq n\}
$$

where each cell $(i,j)$ can host an artifact with dimensions $(w_{ij}, h_{ij})$ scaled by factor $s \in (0,1]$.

### Oversized Artifact Management

The system implements fallback logic for artifacts exceeding grid constraints. Given an artifact $I_k$ with dimensions $(w_k, h_k)$ and available cell width $W_{available}$:

$$
\text{If } w_k > W_{available} \implies I_k \text{ occupies dedicated row } i
$$

$$
\text{with centered positioning: } x_k = \frac{W_{page} - w_k}{2}
$$

---

## 2. Optimized Layout (2D Bin Packing)

The system solves the NP-hard two-dimensional packing problem using the **rectpack** algorithm. Given a set of $N$ images $\{I_1, I_2, \ldots, I_N\}$ with dimensions $(w_i, h_i)$, the algorithm minimizes unused space $W$:

$$
\min W = \sum_{k=1}^{P} \left( W_{page} \cdot H_{page} - \sum_{i \in Page_k} (w_i \cdot h_i) \right)
$$

where:
- $P$ = total number of pages generated
- $Page_k$ = set of artifacts allocated to the $k$-th page
- $(W_{page}, H_{page})$ = page dimensions in pixels
- $m_{px}$ = standardized margins

---

## 3. Two-Level Hierarchical Sorting System

The system implements hierarchical sorting according to multiple structured criteria:

$$
Sort(I) = \text{Sort}_{primary}(\text{Sort}_{secondary}(I))
$$

where $I = \{I_1, I_2, \ldots, I_N\}$ represents the complete set of artifacts.

### Sorting Operators

**Alphabetical ordering**:
$$I_i \prec I_j \iff name(I_i) < name(I_j) \quad \text{(lexicographic)}$$

**Natural numeric ordering**: extraction and comparison of numeric sequences embedded in filenames.

**Stochastic ordering**: $Sort_{random}(I)$ for controlled randomization.

### Hierarchical Composition

Given a key function $key: I \to K$ that extracts the sorting value from each artifact:

$$
I_{sorted} = \bigcup_{k \in K_{primary}} \text{Sort}_{secondary}\left(\{I_i : key_{primary}(I_i) = k\}\right)
$$

### Metadata Structure

The system loads metadata from tabular files structured as:

$$
M = \{(filename_i, \{field_1: value_1, \ldots, field_m: value_m\})\}
$$

Available fields automatically become usable as sorting criteria.

---

## 4. Metric Calibration and Scale

Scale bar length is computed as:

$$
L_{scale} = n_{cm} \cdot \rho_{px/cm} \cdot s
$$

where:
- $n_{cm}$ = target length in centimeters
- $\rho_{px/cm}$ = resolution density (pixels per centimeter)
- $s$ = scale factor applied to images

The bar is segmented into $n$ alternating sections (white/black):

$$
w_{segment} = \frac{L_{scale}}{n_{cm}}
$$

---

## 5. Page Composition

### Available Space Calculation

$$
W_{available} = W_{page} - 2 \cdot m_{px}
$$

$$
H_{available} = H_{page} - 2 \cdot m_{px}
$$

with internal spacing between elements: $sp_{px}$

### Automatic Vertical Centering

For grid layouts, content is vertically centered when $H_{content} < H_{available}$:

$$
y_{start} = m_{px} + \frac{H_{available} - H_{content}}{2}
$$

where total content height is:

$$
H_{content} = \sum_{i=1}^{m} h_{row_i} + (m-1) \cdot sp_{px}
$$
