## Test suite for strong β-reduction

We refer to reducers reducing under abstractions as *strong* reducers.
The suite tests for strong β-reduction until normal form and therefore
assumes reduction strategies where such normal form is found.
(e.g. normal-order, leftmost-outermost, commonly referred to as
Call-by-Need)

Languages may be tested in one of two ways:

- if the language reduces strongly and lazily, translate the tests to
  the language and use it to reduce the terms directly
- if not, use a higher order (or NbE) reducer to reduce the terms

Please contribute!

### Tests

The tests are reconstructed from the handwritten test suite of the
[bruijn](https://bruijn.marvinborner.de) programming language. Currently
the suite consists of 3466 tests. It comprises many different data
structures and numeric encodings. Some of the tests are also quite long
and contain redundant terms and potential for sharing.

Each line in `tests` consists of
`<bruijn term>: <term (blc)> - <nf (blc)>`. The left
[BLC](https://tromp.github.io/cl/Binary_lambda_calculus.html) term is
expected to be α-equivalent to the right BLC term after strong
β-reduction. The bruijn representation is only used for prettyprinting
and debugging.

Any test reducing for more than 5s without reaching a normal form is
deemed to have failed.

### Results

| Test           | Passed | Timeout | Failed |
|:---------------|:-------|:--------|:-------|
| Haskell HOAS   | 3466   | 0       | 0      |
| Optiscope      | 3465   | 1       | 0      |
| Tromp AIT/nf.c | 1935   | 5       | 1526   |
| Your project   | ?      | ?       | ?      |

### Effects

- improved optiscope: https://github.com/etiamz/optiscope/issues/5, https://github.com/etiamz/optiscope/issues/6, https://github.com/etiamz/optiscope/issues/7
