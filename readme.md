## Test suite for strong β-reduction

We refer to reducers reducing under abstractions as *strong* reducers.
The suite tests for strong β-reduction until β-normal form and therefore
assumes reduction strategies where such normal form is found.
(e.g. normal-order, leftmost-outermost, Call-by-Name/Need)

Languages may be tested in one of two ways:

- if the language reduces strongly and lazily, translate the tests to
  the language and use it to reduce the terms directly
- if not, use a higher order (or NbE) reducer to reduce the terms

Please contribute!

### Tests

The tests are reconstructed from the handwritten test suite of the
[bruijn](https://bruijn.marvinborner.de) programming language. The suite
consists of 3466 tests; 1197 after deduplication. It comprises many
different data structures and numeric encodings. Some of the tests are
also quite long and contain redundant terms and potential for sharing.

Each line in `tests` consists of
`<bruijn term>: <term (blc)> - <nf (blc)>`. The left
[BLC](https://tromp.github.io/cl/Binary_lambda_calculus.html) term is
expected to be α-equivalent to the right BLC term after strong
β-reduction. If terms reduce to the strong βη-normal form or other terms
η-equivalent to the strong β-normal form, you may use η-conversion for
the normal form comparison. The bruijn representation is only used for
prettyprinting and debugging.

Any test reducing for more than 5s (on github ci, or my laptop) without
reaching a normal form is deemed to have not passed.

### Results

| Test              | Passed | Timeout | Failed |
|:------------------|:-------|:--------|:-------|
| Haskell HOAS      | 1197   | 0       | 0      |
| Tromp AIT/nf.c    | 1197   | 0       | 0      |
| Optiscope         | 1196   | 1       | 0      |
| HVM4              | 1122   | 7       | 69     |
| HVM3              | 1122   | 73      | 2      |
| Rebound ShiftList | 1104   | 93      | 0      |
| Freya-lang        | 1095   | 15      | 87     |
| Rebound Lazy      | 1093   | 104     | 0      |
| Rebound SkewList  | 1085   | 112     | 0      |
| HVM1              | 930    | 266     | 1      |
| Your project      | ?      | ?       | ?      |

EAL tests (subset typable in elementary affine logic, smaller than
abstract, bookkeeping-free subset of optimal reduction):

| Test       | Passed | Timeout | Failed |
|:-----------|:-------|:--------|:-------|
| HVM1       | 532    | 0       | 0      |
| HVM3       | 532    | 0       | 0      |
| HVM4       | 532    | 0       | 0      |
| optiscope  | 532    | 0       | 0      |
| freya-lang | 532    | 0       | 0      |

`uni.blc` tower of 1:

| Test              | Passed | Timeout | Failed |
|:------------------|:-------|:--------|:-------|
| Haskell HOAS      | 1197   | 0       | 0      |
| Tromp AIT/nf.c    | 1170   | 27      | 0      |
| Freya-lang        | 90     | 209     | 898    |
| Optiscope         | ?      | ?       | ?      |
| Rebound ShiftList | ?      | ?       | ?      |
| Rebound Lazy      | ?      | ?       | ?      |
| Rebound SkewList  | ?      | ?       | ?      |
| HVM1              | ?      | ?       | ?      |
| HVM3              | ?      | ?       | ?      |
| HVM4              | ?      | ?       | ?      |
| Your project      | ?      | ?       | ?      |

### Reproduction

``` bash
runhaskell haskell.hs
./tromp.py
./optiscope.py
./freya.py
stack --stack-yaml rebound/benchmark/stack.yaml runghc rebound.hs
./hvm1.py
./hvm3.py
./hvm4.py
```

for interpreter towers of size $n$:

``` bash
./towerify n > tests
```

### Effects

- fixed optiscope correctness:
  https://github.com/etiamz/optiscope/issues/5,
  https://github.com/etiamz/optiscope/issues/6,
  https://github.com/etiamz/optiscope/issues/7
- fixed nf.c correctness: https://github.com/tromp/AIT/pull/11
- counterexamples to
  [freya-lang](https://github.com/freya-lang/opteval/): [PL
  Discord](https://discord.com/channels/530598289813536771/1506067906092335117)
