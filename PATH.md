# A prescribed policy segment

`path_audit(A, x0, y0, x1, y1)` computes the exact duality gap along a supplied segment of independent policies. It returns the whole closed interval of parameters attaining the minimum on that segment. It does not search all policy pairs, solve for a learned trajectory or guarantee an improvement from a finite training step.

For `0 <= alpha <= 1`, the policies are

```text
x(alpha) = (1-alpha) x0 + alpha x1
y(alpha) = (1-alpha) y0 + alpha y1.
```

Both endpoints must be valid probability vectors. Convexity keeps the interpolated vectors valid. The row player maximizes its supplied payoff; the column player minimizes it. The matrix is fixed throughout this audit.

## Why the gap is piecewise affine

Every pure row payoff `r_i(alpha) = (A y(alpha))_i` and pure column payoff `c_j(alpha) = (x(alpha)^T A)_j` is affine. The joint deviation gap is

```text
g(alpha) = max_i r_i(alpha) - min_j c_j(alpha)
         = max_(i,j) [r_i(alpha) - c_j(alpha)].
```

It is therefore a convex piecewise-affine function. The expected payoff `x(alpha)^T A y(alpha)` can be quadratic. It cancels when the two unilateral deviation gains are added; minimizing that expected payoff is a different question.

The implementation records every same-side pair of payoff lines. Equal slopes are labeled `parallel` or `identical`, with no isolated crossing parameter. Other pairs retain their exact crossing, even outside `[0,1]`. The knots contain zero, one and every distinct crossing strictly inside the segment. A crossing can be inactive: it need not change a best reply or the gap slope.

Between consecutive knots, line ordering cannot change. A midpoint identifies all tied best replies throughout the open interval. Subtracting a best column line from a best row line gives that interval's gap intercept and slope. Endpoint ties are reported separately by complete direct audits at the knots. The affine formula also gives the correct value at the closed endpoints by continuity.

An affine function reaches its minimum on a closed interval at an endpoint, unless it is constant. Thus the smallest knot gap is the segment minimum. The set attaining a convex function's minimum is convex: the smallest and largest attaining knots describe the whole closed minimizing interval. If they differ, every intervening piece has slope zero. The code checks nondecreasing slopes, these zero slopes and a complete direct audit at the minimizing interval's midpoint. These are exact rational checks, not numerical tolerances.

The returned representative is that midpoint. It is a deterministic witness, not a uniquely preferred policy pair. No security LP is solved by this function. A zero gap still certifies equilibrium for the supplied matrix; a positive segment minimum does not say the whole game lacks an equilibrium.

## Developed controls

- Matching pennies, with both players moving from action zero to action one, has gap slopes `-4` and `4`, and reaches zero only at `alpha=1/2`.
- For rock-paper-scissors, both players restricted to the segment from rock to paper have minimum gap `2/3` at `alpha=2/3`. The inactive crossing at `1/3` remains in the report. The uniform equilibrium lies outside this segment.
- With `A=[[0,0],[1,-2],[-2,1],[0,0]]`, fixed row policy `[1,0,0,0]` and a column policy moving from `[1,0]` to `[0,1]`, the gap is `max(0,1-3*alpha,-2+3*alpha)`. Every parameter in `[1/3,2/3]` attains zero. Duplicate rows and the inactive crossing at `1/2` are retained.
- Frozen paths, constant matrices, one-action games, boundary minima, parallel lines and crossings outside the segment are tested separately.

The seven path tests also use 56 seeded exact cases across shapes `1x1`, `1x3`, `3x1`, `2x2`, `2x3`, `3x2` and `4x4`. An independent reference enumerates vertices of the two-dimensional reply-pair epigraph to find the minimum, then intersects the inequalities `r_i(alpha)-c_j(alpha)<=minimum` to recover the entire attaining interval. Direct raw payoff sums check nine probes per case and every exported knot. Reversal, positive affine payoff changes and negative-transpose/player exchange provide additional controls. Input/output isolation, unchanged RNG state and strict CLI failures are checked too. These are developed finite fixtures, not multi-agent training results.

## API and strict input

```python
from gamelab import path_audit

report = path_audit(
    [[0,-1,1],[1,0,-1],[-1,1,0]],
    [1,0,0], [1,0,0], [0,1,0], [0,1,0],
)
assert report['minimum_gap'] == '2/3'
assert report['minimizing_alpha_interval'] == ['2/3','2/3']
```

```bash
python -m gamelab path examples/path-input.json
python examples/verify_wheel.py
```

The JSON object must contain exactly `schema_version`, `payoffs`, `row_start`, `column_start`, `row_end` and `column_end`. The version is integer one, not a boolean. Matrix and probability validation use the existing exact parser: one to four actions per player, exact normalization, no floats, booleans or nonfinite values, at most 512-bit input rational components and 160-character strings. JSON input is capped at 200,000 bytes. Duplicate/unknown keys, malformed UTF-8 and excessive JSON nesting fail with exit two, empty stdout and an error on stderr.

The report includes the normalized endpoints, every payoff line, all pair classifications, full knot audits, affine pieces with interior ties, the minimum and its entire attaining interval, and the midpoint policies with their direct audit. Rational values are strings. Input is copied; the output does not alias it. No package dependency, network call or random draw is used.

## Scope and attribution

This is a finite exact envelope calculation for one supplied segment. The joint distribution at a parameter is `x(alpha) y(alpha)^T`, not the correlated mixture `(1-alpha)x0 y0^T + alpha x1 y1^T`. No correlated-equilibrium, general-sum, stochastic convergence, opponent-learning, empirical-policy or scalability result is claimed. Internal rational arithmetic can grow beyond the input caps.

The duality-gap identity, convexity of a finite maximum of affine functions and endpoint minimization of an affine function are standard facts. This implementation and its developed controls do not claim a new game-theoretic method. Existing fixed-matrix and interval reports and both figures remain unchanged. The installed-wheel verifier runs the whole suite outside checkout, checks all seven package origins before and after it, compares all seven complete module CLI outputs, and regenerates both figures. The package has no console entry point.
