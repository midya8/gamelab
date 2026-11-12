# GameLab fixed-matrix method

## Security LPs and orientation

Let `A` be an `m x n` rational matrix, `1<=m,n<=4`. The row player maximizes expected payoff; the column player minimizes it. Independent mixed strategies are probability vectors `x,y`. Define

```text
row security:    max_(x,v) v, sum x=1, x_i>=0, x^T A[:,j]-v>=0
column security: min_(y,w) w, sum y=1, y_j>=0, w-(Ay)_i>=0.
```

The second problem is implemented by maximizing negative column payoff on `-A^T`. Its `column_negative_game.value` is negative the original game's value. Its inequality/slack labels and intermediate vertices refer to this transformed game. The final certificate translates its optimum to `dual_value` in original row-payoff units.

Strong LP duality gives equal security values. This is the standard finite zero-sum minimax theorem, not a new algorithm. The certificate independently evaluates both players' representative strategies against every pure action. If `x^T A[:,j]>=v` for every column and `(Ay)_i<=v` for every row, then every mixed opponent is also covered by linearity, and `x^T A y=v`. Their nonnegative slacks and complementary products `x_i*(v-(Ay)_i)`, `y_j*((x^T A)_j-v)` are returned.

Pure security controls deliberately restrict a player to a pure action. They are not substitutes for the mixed-game value. A pure saddle `(i,j)` has `A_ij=min_k A_ik=max_l A_lj` in this orientation.

## Enumeration and completeness

The row security variables are `(x_0,...,x_(m-1),v)` in dimension `m+1`. A normalization equality is always active. Other inequalities are `m` nonnegativity constraints plus `n` payoff constraints. Every vertex has a basis containing normalization and `m` independent active inequalities. The normalization row is independent of any subset of homogeneous active inequality rows that forms a basis: its right-hand side is one, theirs zero. We try **every** `m`-subset, at most 70 per side.

For each basis, exact Gauss-Jordan elimination reports its rank, determinant, pivot columns and either the unique solution or `null` when singular. No floating tolerance is used. Singular systems are discarded as bases, not treated as proof that no equilibrium exists. A nonsingular candidate is feasible only if all inequalities have nonnegative exact slack. All violations are preserved in the report. Feasible candidates merge by the entire exact `(strategy,value)` vector, collecting all bases and all active constraints. Multiple bases at one vertex are degeneracy, not multiple equilibria.

The security polyhedron has downward rays in value but contains no line: strategy coordinates lie in a simplex and fixed strategy bounds value above. Its finite optimum exists. Every optimal-face vertex is a vertex of the security polyhedron, so exhaustive basis enumeration finds it. At the optimum the face is bounded in the simplex, hence is the convex hull of its vertices. Conversely every convex combination of exported optimal vertices satisfies every security inequality at that same value. This proves completeness of the optimal strategy set representation within the supported finite dimensions.

Nonoptimal feasible vertices are retained too, but do **not** belong in the optimal-face convex hull. Distinct optimal strategies are sorted lexicographically by rational coordinate, not rational-string spelling. Every coordinate's minimum and maximum over the optimal face is attained at an exported optimal vertex; the report gives those indices. Coordinates cannot generally be chosen independently within the ranges.

The representative averages all distinct optimal vertices. This is deterministic and permutation-equivariant under action relabeling, but is not a uniform distribution over a continuum, a maximum-entropy choice or an empirical preference. Its purpose is to make one inspectable equilibrium certificate without erasing alternatives. All row/column optimal strategies can be paired interchangeably in this zero-sum setting. This property is not imported to general-sum games.

## Strategy audit

For a valid pair, let `p=x^T A y`, `u=max_i(Ay)_i`, `l=min_j(x^T A)_j`. The report returns all action payoffs and every tie. Row unilateral gain is `u-p`; column unilateral gain is `p-l`. Both are nonnegative, and their sum is `u-l`, the saddle/duality gap.

Relative to the exact game value `v`, row security loss is `v-l` and column security loss is `u-v`. They are also nonnegative and sum to the same gap. Individual unilateral gain and security loss need not agree. We explicitly call the latter `row_exploitability` and `column_exploitability`, using a **sum** pair convention. Some literature uses a half-sum; do not compare numbers without checking that convention. Gap zero is necessary and sufficient for equilibrium of the supplied finite zero-sum matrix.

## Deterministic payoff perturbation

Let `epsilon=max_ij|B_ij-A_ij|`. For any pair, `|x^T B y-x^T A y|<=epsilon`, since the expectation is a convex combination of entry changes. Maximizing/minimizing preserves this envelope, giving `|v(B)-v(A)|<=epsilon`.

If `(x_A,y_A)` is an equilibrium of A with value `v_A`, then under B

```text
min_j (x_A^T B)_j >= v_A-epsilon
max_i (B y_A)_i <= v_A+epsilon.
```

Subtracting bounds the old pair's new gap by `2*epsilon`. Each new security loss is individually at most `2*epsilon`, using the value bound too. Summing those individual loose bounds would give four epsilon, but the shared-security argument gives the stronger pair bound of two. The report keeps all bound slacks and all entries attaining epsilon, as well as both complete game solutions. With zero epsilon, everything agrees exactly.

There is no corresponding continuity claim for strategy coordinates. The developed two-row/one-column flip shows that an arbitrarily small entry change can change the unique preferred row from one pure action to the other. Deterministic epsilon is not a confidence interval or an estimate of unknown payoff noise.

## Exact input and JSON schemas

All CLI objects require integer `schema_version:1` and exactly these additional keys:

| Mode | Required keys | Optional keys |
|---|---|---|
| `solve` | `payoffs` | none |
| `audit` | `payoffs`, `row_strategy`, `column_strategy` | none |
| `perturbation` | `original`, `changed` | none |

`demo` takes no input. `payoffs` and both perturbation matrices are rectangular list/tuple matrices, one to four rows and columns. Perturbation shapes must match. Strategies match their dimensions, contain nonnegative entries and sum exactly to one. Zero probability entries are allowed, unlike zero-weight mixtures in some other projects.

Numbers may be Python integers, rational/decimal strings or `Fraction` objects. The accepted string grammar is `-?digits` optionally followed by `/digits` or `.digits`. No exponent, sign-plus, spaces, nonfinite values, float or bool. Strings are at most 160 characters, input numerator/denominator components at most 512 bits. A denominator must be nonzero. No payoff interval bound or positive-payoff shift is assumed; negative games and rational entries are valid. Parsing copies input, does not mutate it and uses no random generator.

The CLI reads at most 200,000 bytes, decodes UTF-8 strictly and rejects duplicate keys/nonfinite JSON/unknown fields/wrong schema versions/missing keys. Errors exit two with empty stdout and an `error:` stderr line. Importable APIs raise `ValueError`. Internal exact arithmetic is not reparsed through input caps; intermediates can grow large. Output contains every basis and can be much larger than input.

`solve` returns both full security enumerations, value, representative audit, primal/dual certificate and pure controls. `audit` solves for value but returns only the chosen pair's full diagnostics rather than repeating the LP trace. `perturbation` returns both full solutions and exact transferred-pair bounds. Fractions serialize as canonical strings, including zero and one. Structural counts/indices are integers; predicates are booleans. Nothing calls external services at runtime.

## Attribution

This project implements established LP/minimax/convex-polytope facts with inspectable finite enumeration. Six consulted sources:

1. [Nashpy's zero-sum textbook](https://nashpy.readthedocs.io/en/latest/text-book/zero-sum-games.html): row-max/column-min LP formulation and minimax. GameLab does not depend on or reproduce Nashpy's implementation.
2. [MIT computational game theory lecture 2](https://people.csail.mit.edu/costis/6896sp10/lec2.pdf): duality, equilibria and optimal security strategies.
3. [CMU Sandholm lecture 4](https://www.cs.cmu.edu/~sandholm/cs15-888F25/Lecture4-LPs-Regret.pdf): LP minimax and multiple equilibria. That note uses row-min/column-max orientation; GameLab explicitly uses the opposite payoff convention.
4. [CMU Ganzfried, Opponent Exploitation](https://www.cs.cmu.edu/afs/cs/academic/class/15780-s13/www/lec/ganzfried_gt.pdf): best replies and individual security exploitability.
5. [CMU Yang, Zero-Sum Games](https://www.cs.cmu.edu/~yangp/15-451/lecture17.pdf): unique game value does not imply unique strategies.
6. [Newman, Geometry of Linear Programming](https://pagesperso.g-scop.grenoble-inp.fr/~newmana/OptApproxFall2016/OptApprox-lecture2.pdf): active independent constraints, basic feasible vertices and optimal-face geometry.

The determinant-based enumeration is intentionally tiny and exhaustive, not simplex, interior-point, a scalable game-solving engine or a new theorem. No general-sum/hidden-information/sequential game, empirical payoff model, training convergence, learned opponent, real-agent strength, statistical uncertainty or production safety is established by this audit.
