import unittest
import numpy as np
from asset_allocation import methods as m
from asset_allocation.cli import backtest,demo_returns,summary
import pandas as pd

class AllocationTests(unittest.TestCase):
    def test_weight_constraints(self):
        covariance=np.diag(np.linspace(.001,.03,20))
        for w in [m.optimize_min_variance(covariance),m.optimize_max_sharpe(np.linspace(.01,.08,20),covariance)]:
            self.assertAlmostEqual(w.sum(),1,places=5)
            self.assertGreaterEqual(w.min(),-1e-7)
            self.assertLessEqual(w.max(),.2000001)

    def test_future_changes_do_not_change_earlier_weights(self):
        returns=demo_returns().iloc[:64]
        original,weights,_=backtest(returns,60,2)
        changed=returns.copy()
        changed.iloc[62:]=.15
        _,changed_weights,_=backtest(changed,60,2)
        for key in weights:
            np.testing.assert_allclose(weights[key].iloc[:3],changed_weights[key].iloc[:3],atol=1e-6)
        self.assertEqual(len(original),4)

    def test_drawdown_includes_initial_capital(self):
        self.assertAlmostEqual(summary(pd.Series([-.1,.0]))['max_drawdown_pct'],-10)

    def test_views_and_posterior_are_finite(self):
        history=demo_returns().iloc[:60]
        cov=history.cov().to_numpy()*12
        prior=2.5 * cov @ np.ones(20) / 20
        P,Q,omega,_=m.create_dynamic_individual_bl_views(history,history.columns,cov,prior)
        mu,sigma=m.black_litterman_posterior(prior,cov,P,Q,omega)
        self.assertEqual(P.shape,(2,20))
        self.assertTrue(np.isfinite(mu).all())
        np.testing.assert_allclose(sigma,sigma.T)

if __name__=='__main__':unittest.main()
