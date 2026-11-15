"""Methods adapted from the original Financial Markets Analytics notebook.

Default numerical settings preserve the submitted experiment. Optimizers keep
its equal-weight fallback but now warn explicitly if SLSQP fails.
"""
import warnings
import numpy as np
import pandas as pd
from scipy.optimize import minimize

MONTHS_PER_YEAR = 12
WINDOW = 60
MAX_WEIGHT = 0.20
RISK_AVERSION = 2.5
TAU = 0.05
SHRINKAGE = 0.50

def optimize_min_variance(cov_matrix, max_weight=0.20):
    n_assets = cov_matrix.shape[0]
    initial_weights = np.repeat(1 / n_assets, n_assets)

    bounds = [(0, max_weight) for _ in range(n_assets)]
    constraints = {"type": "eq", "fun": lambda w: np.sum(w) - 1}

    def portfolio_variance(w):
        return w @ cov_matrix @ w

    result = minimize(
        portfolio_variance,
        initial_weights,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints
    )

    if result.success:
        return result.x
    else:
        warnings.warn(f"SLSQP failed; using equal weights: {result.message}", RuntimeWarning)
        return initial_weights

def michaud_resampled_min_variance(estimation_window, n_simulations=100, max_weight=0.20):
    window_length = estimation_window.shape[0]

    # Estimate mean and covariance from the past window
    mu_monthly = estimation_window.mean().values
    cov_monthly = estimation_window.cov().values

    simulated_weights = []

    for _ in range(n_simulations):

        # Simulate an alternative return history with the same mean and covariance
        simulated_returns = np.random.multivariate_normal(
            mean=mu_monthly,
            cov=cov_monthly,
            size=window_length
        )

        # Estimate covariance from the simulated data
        simulated_cov = np.cov(simulated_returns, rowvar=False) * MONTHS_PER_YEAR

        # Optimize the simulated sample using the same Markowitz minimum-variance rule
        weights = optimize_min_variance(
            simulated_cov,
            max_weight=max_weight
        )

        simulated_weights.append(weights)

    # Average the optimized weights across all simulations
    resampled_weights = np.mean(simulated_weights, axis=0)

    # Numerical correction: make sure weights sum to 1
    resampled_weights = resampled_weights / resampled_weights.sum()

    return resampled_weights

def optimize_max_sharpe(expected_returns, cov_matrix, max_weight=0.20, risk_free_rate=0.0):
    n_assets = len(expected_returns)
    initial_weights = np.repeat(1 / n_assets, n_assets)

    bounds = [(0, max_weight) for _ in range(n_assets)]
    constraints = {"type": "eq", "fun": lambda w: np.sum(w) - 1}

    def negative_sharpe(w):
        portfolio_return = w @ expected_returns
        portfolio_volatility = np.sqrt(w @ cov_matrix @ w)

        if portfolio_volatility == 0:
            return 1e6

        return -(portfolio_return - risk_free_rate) / portfolio_volatility

    result = minimize(
        negative_sharpe,
        initial_weights,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints
    )

    if result.success:
        return result.x
    else:
        warnings.warn(f"SLSQP failed; using equal weights: {result.message}", RuntimeWarning)
        return initial_weights

def create_dynamic_individual_bl_views(estimation_window, asset_list, Sigma, pi):
    """
    Create two dynamic Black-Litterman views using only past data.

    View 1:
    The ETF with the strongest trailing 12-month return outperforms
    the ETF with the weakest trailing 12-month return.

    View 2:
    The strongest momentum ETF receives an absolute expected-return view,
    but this view is shrunk toward the prior-implied return.
    """

    asset_list = pd.Index(asset_list)
    n_assets = len(asset_list)

    assert len(estimation_window) >= 12, "At least 12 months are needed for the momentum view."
    assert Sigma.shape == (n_assets, n_assets), "Sigma has the wrong shape."
    assert pi.shape == (n_assets,), "pi has the wrong shape."

    # Use only the last 12 months inside the rolling estimation window.
    momentum_12m = (1 + estimation_window.tail(12)).prod() - 1

    top_asset = momentum_12m.idxmax()
    bottom_asset = momentum_12m.idxmin()

    top_idx = asset_list.get_loc(top_asset)
    bottom_idx = asset_list.get_loc(bottom_asset)

    top_momentum = momentum_12m.loc[top_asset]
    bottom_momentum = momentum_12m.loc[bottom_asset]
    spread_1 = top_momentum - bottom_momentum

    # Relative view: top momentum ETF outperforms bottom momentum ETF.
    P1 = np.zeros(n_assets)
    P1[top_idx] = 1.0
    P1[bottom_idx] = -1.0

    # Use only half of the observed spread and cap it to avoid unrealistic views.
    Q1 = np.clip(0.5 * abs(spread_1), 0.01, 0.06)

    view_variance_1 = float(P1 @ Sigma @ P1.T)
    view_variance_1 = max(view_variance_1, 1e-8)

    # Larger spreads are treated as stronger signals.
    if abs(spread_1) < 0.03:
        confidence_1 = 0.60
    elif abs(spread_1) < 0.08:
        confidence_1 = 0.70
    else:
        confidence_1 = 0.80

    omega_1 = ((1 - confidence_1) / confidence_1) * view_variance_1
    omega_1 = max(float(omega_1), 1e-6)

    # Absolute view for the same strongest momentum ETF.
    P2 = np.zeros(n_assets)
    P2[top_idx] = 1.0

    mu_hist_top = estimation_window[top_asset].mean() * MONTHS_PER_YEAR
    mu_prior_top = pi[top_idx]

    # Shrink the historical estimate toward the prior because historical means are noisy.
    Q2 = SHRINKAGE * mu_hist_top + (1 - SHRINKAGE) * mu_prior_top
    Q2 = np.clip(Q2, -0.05, 0.15)

    view_variance_2 = float(P2 @ Sigma @ P2.T)
    view_variance_2 = max(view_variance_2, 1e-8)

    T_years = len(estimation_window) / MONTHS_PER_YEAR
    confidence_2 = 0.60

    omega_2 = view_variance_2 / T_years
    omega_2 = ((1 - confidence_2) / confidence_2) * omega_2
    omega_2 = max(float(omega_2), 1e-6)

    P = np.vstack([P1, P2])
    Q = np.array([Q1, Q2])
    Omega = np.diag([omega_1, omega_2])

    views_table = pd.DataFrame({
        "View name": [
            "Top momentum outperforms bottom momentum",
            "Absolute view on strongest momentum ETF"
        ],
        "View type": [
            "Relative",
            "Absolute"
        ],
        "Top asset": [
            top_asset,
            top_asset
        ],
        "Bottom asset": [
            bottom_asset,
            None
        ],
        "Top asset 12M momentum": [
            top_momentum,
            top_momentum
        ],
        "Bottom asset 12M momentum": [
            bottom_momentum,
            None
        ],
        "Momentum spread": [
            spread_1,
            None
        ],
        "Q annual view": [
            Q1,
            Q2
        ],
        "Historical annualized return": [
            None,
            mu_hist_top
        ],
        "Prior-implied return": [
            None,
            mu_prior_top
        ],
        "Shrinkage": [
            None,
            SHRINKAGE
        ],
        "Confidence": [
            confidence_1,
            confidence_2
        ],
        "View variance": [
            view_variance_1,
            view_variance_2
        ],
        "Omega value": [
            omega_1,
            omega_2
        ],
        "Explanation": [
            f"{top_asset} has the highest trailing 12-month return and {bottom_asset} has the lowest.",
            f"The expected return for {top_asset} is shrunk toward its prior-implied return."
        ]
    })


    assert P.shape == (2, n_assets), "P has the wrong shape."
    assert Q.shape == (2,), "Q has the wrong shape."
    assert Omega.shape == (2, 2), "Omega has the wrong shape."
    assert np.all(np.diag(Omega) > 0), "Omega diagonal values must be positive."

    assert np.isclose(P[0].sum(), 0.0), "Relative view row must sum to zero."
    assert np.sum(P[0] == 1.0) == 1, "Relative view must have one +1."
    assert np.sum(P[0] == -1.0) == 1, "Relative view must have one -1."

    assert np.isclose(P[1].sum(), 1.0), "Absolute view row must sum to one."
    assert np.sum(P[1] == 1.0) == 1, "Absolute view must have one +1."
    assert np.sum(P[1] != 0.0) == 1, "Absolute view must select only one ETF."

    return P, Q, Omega, views_table

def black_litterman_posterior(pi, Sigma, P, Q, Omega, tau=0.05):
    """
    Combine the prior-implied returns with the views.

    The output is:
    - mu_bl: posterior expected returns
    - Sigma_bl: posterior covariance matrix
    """

    pi = np.asarray(pi)
    Sigma = np.asarray(Sigma)
    P = np.asarray(P)
    Q = np.asarray(Q)
    Omega = np.asarray(Omega)

    n_assets = Sigma.shape[0]
    n_views = P.shape[0]

    assert tau > 0, "tau must be positive."
    assert Sigma.shape == (n_assets, n_assets), "Sigma must be square."
    assert pi.shape == (n_assets,), "pi has the wrong shape."
    assert P.shape == (n_views, n_assets), "P has the wrong shape."
    assert Q.shape == (n_views,), "Q has the wrong shape."
    assert Omega.shape == (n_views, n_views), "Omega has the wrong shape."
    assert np.all(np.diag(Omega) > 0), "Omega diagonal values must be positive."

    # The small diagonal term helps avoid numerical inversion problems.
    Sigma = Sigma + 1e-8 * np.eye(n_assets)
    tau_sigma = tau * Sigma

    inv_tau_sigma = np.linalg.pinv(tau_sigma)
    inv_omega = np.linalg.pinv(Omega)

    posterior_cov_part = np.linalg.pinv(
        inv_tau_sigma + P.T @ inv_omega @ P
    )

    mu_bl = posterior_cov_part @ (
        inv_tau_sigma @ pi + P.T @ inv_omega @ Q
    )

    Sigma_bl = Sigma + posterior_cov_part
    Sigma_bl = (Sigma_bl + Sigma_bl.T) / 2

    assert not np.isnan(mu_bl).any(), "mu_bl contains NaN values."
    assert not np.isnan(Sigma_bl).any(), "Sigma_bl contains NaN values."

    return mu_bl, Sigma_bl

def create_manual_view_matrices(asset_list, Sigma, manual_views):
    asset_list = pd.Index(asset_list)
    n_assets = len(asset_list)

    P_rows = []
    Q_values = []
    omega_values = []
    view_records = []

    for view in manual_views:
        view_type = view["type"]

        if view_type == "Disabled":
            continue

        confidence = float(view["confidence"])
        q_value = float(view["q_pct"]) / 100

        if confidence <= 0 or confidence >= 1:
            raise ValueError("Confidence must be between 0 and 1.")

        if view_type == "Absolute":
            asset = view["asset_a"]

            P_row = np.zeros(n_assets)
            P_row[asset_list.get_loc(asset)] = 1.0

            view_name = f"{asset} expected annual return"

        elif view_type == "Relative":
            long_asset = view["asset_a"]
            short_asset = view["asset_b"]

            if long_asset == short_asset:
                raise ValueError("In a relative view, Asset A and Asset B must be different.")

            P_row = np.zeros(n_assets)
            P_row[asset_list.get_loc(long_asset)] = 1.0
            P_row[asset_list.get_loc(short_asset)] = -1.0

            view_name = f"{long_asset} outperforms {short_asset}"

        view_variance = float(P_row @ Sigma @ P_row.T)
        view_variance = max(view_variance, 1e-8)

        omega_value = ((1 - confidence) / confidence) * view_variance
        omega_value = max(float(omega_value), 1e-6)

        P_rows.append(P_row)
        Q_values.append(q_value)
        omega_values.append(omega_value)

        view_records.append({
            "View Type": view_type,
            "View": view_name,
            "Annual View Q (%)": q_value * 100,
            "Confidence": confidence,
            "Omega": omega_value
        })

    if len(P_rows) == 0:
        return None, None, None, pd.DataFrame()

    P = np.vstack(P_rows)
    Q = np.array(Q_values)
    Omega = np.diag(omega_values)

    views_table = pd.DataFrame(view_records)

    return P, Q, Omega, views_table
