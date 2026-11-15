"""Portable command-line reproduction of the original rolling experiment."""
import argparse
import json
import re
from pathlib import Path
import numpy as np
import pandas as pd
from . import methods as m

TICKERS = ['SPY','QQQ','IWM','VGK','EFA','EEM','EWJ','SHY','IEF','TLT','AGG','LQD','HYG','EMB','TIP','GLD','DBC','VNQ','BIL','SHV']
EQUITIES = TICKERS[:7]
BONDS = ['SHY','IEF','TLT','AGG','LQD','BIL','SHV']


def load_returns(path):
    levels = pd.read_excel(path, sheet_name='Price History', header=15)
    def ticker(column):
        match = re.search(r'\(([A-Z]+)-US\)', str(column))
        return match.group(1) if match else column
    levels = levels.rename(columns=ticker)
    levels['Date'] = pd.to_datetime(levels['Date'], errors='raise')
    levels = levels.set_index('Date').sort_index().loc['2008-01-01':'2026-05-31', TICKERS]
    if levels.index.has_duplicates or levels.isna().any().any() or (levels <= 0).any().any():
        raise ValueError('Expected unique dates and complete positive total-return levels.')
    if levels.index.to_period('M').has_duplicates:
        raise ValueError('Expected one observation per month.')
    months = levels.index.to_period('M').astype(int)
    if len(months) < 2 or not np.all(np.diff(months) == 1):
        raise ValueError('Expected consecutive monthly observations.')
    return levels.pct_change(fill_method=None).iloc[1:]


def demo_returns():
    rng = np.random.default_rng(42)
    market = rng.normal(.004, .018, (96, 1))
    values = market + rng.normal(.001, .015, (96, 20))
    return pd.DataFrame(values, index=pd.date_range('2018-01-31', periods=96, freq='ME'), columns=TICKERS)


def summary(series):
    annual = series.mean() * 12
    volatility = series.std() * np.sqrt(12)
    wealth = (1 + series).cumprod()
    # Include starting wealth so a first-month loss is counted as a drawdown.
    peaks = wealth.cummax().clip(lower=1)
    return pd.Series({'annual_arithmetic_return_pct':annual*100,
                      'annual_volatility_pct':volatility*100,
                      'sharpe_zero_rf':annual/volatility if volatility else np.nan,
                      'max_drawdown_pct':(wealth/peaks-1).min()*100})


def backtest(returns, window=60, simulations=100, seed=42, max_weight=.2):
    if window < 12 or len(returns) <= window:
        raise ValueError('Need a window of at least 12 months and at least one test observation.')
    if not np.isfinite(returns.to_numpy()).all() or (returns <= -1).any().any():
        raise ValueError('Invalid returns.')
    np.random.seed(seed)
    names = ['Markowitz Min Variance','Michaud Resampled','Markowitz Max Sharpe','Black-Litterman']
    histories = {name:[] for name in names}
    realized = {name:[] for name in names}
    views_history=[]
    for i in range(window, len(returns)):
        history = returns.iloc[i-window:i]
        future = returns.iloc[i].to_numpy()
        covariance = history.cov().to_numpy()*12
        means = history.mean().to_numpy()*12
        stable_cov = covariance + 1e-8*np.eye(len(TICKERS))
        prior = m.RISK_AVERSION * stable_cov @ np.repeat(1/len(TICKERS),len(TICKERS))
        P,Q,omega,views = m.create_dynamic_individual_bl_views(history, returns.columns, stable_cov, prior)
        posterior, posterior_cov = m.black_litterman_posterior(prior,stable_cov,P,Q,omega,tau=.05)
        weights = [m.optimize_min_variance(covariance,max_weight),
                   m.michaud_resampled_min_variance(history,simulations,max_weight),
                   m.optimize_max_sharpe(means,covariance,max_weight),
                   m.optimize_max_sharpe(posterior,posterior_cov,max_weight)]
        for name,w in zip(names,weights):
            if not np.isclose(w.sum(),1,atol=1e-5) or w.min() < -1e-7 or w.max() > max_weight+1e-7:
                raise RuntimeError('Optimizer produced infeasible weights.')
            histories[name].append(w)
            realized[name].append(float(w @ future))
        views.insert(0,'Date',returns.index[i])
        views_history.append(views)
    index = returns.index[window:]
    result = pd.DataFrame(realized,index=index)
    result.insert(0,'60/40',(.6*returns[EQUITIES].mean(axis=1)+.4*returns[BONDS].mean(axis=1)).loc[index])
    result.insert(0,'Equal Weight',returns.mean(axis=1).loc[index])
    weights = {name:pd.DataFrame(values,index=index,columns=TICKERS) for name,values in histories.items()}
    return result,weights,pd.concat(views_history,ignore_index=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    inputs=parser.add_mutually_exclusive_group(required=True)
    inputs.add_argument('--data',type=Path,help='Licensed FactSet Excel workbook')
    inputs.add_argument('--demo',action='store_true',help='Synthetic smoke experiment, not empirical evidence')
    parser.add_argument('--output',type=Path,default=Path('outputs/run'))
    parser.add_argument('--window',type=int,default=60)
    parser.add_argument('--simulations',type=int,default=100)
    parser.add_argument('--seed',type=int,default=42)
    args=parser.parse_args()
    if args.simulations < 1:
        parser.error('--simulations must be positive')
    returns=demo_returns() if args.demo else load_returns(args.data)
    if args.output.exists() and any(args.output.iterdir()):
        parser.error('Output folder is not empty; use a new output directory.')
    results,weights,views=backtest(returns,args.window,args.simulations,args.seed)
    args.output.mkdir(parents=True,exist_ok=True)
    results.to_csv(args.output/'monthly_returns.csv',index_label='date')
    statistics=results.apply(summary).T
    statistics.to_csv(args.output/'summary.csv',index_label='strategy')
    for name,frame in weights.items():
        frame.to_csv(args.output/(name.lower().replace(' ','_')+'_weights.csv'),index_label='date')
    views.to_csv(args.output/'black_litterman_views.csv',index=False)
    metadata={'data_kind':'synthetic_demo' if args.demo else 'licensed_factset',
              'seed':args.seed,'window_months':args.window,'michaud_simulations':args.simulations,
              'test_start':str(results.index.min().date()),'test_end':str(results.index.max().date()),
              'test_months':len(results),'transaction_costs_included':False,'risk_free_rate':0}
    (args.output/'run.json').write_text(json.dumps(metadata,indent=2)+'\n')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.family':'DejaVu Sans','axes.spines.top':False,'axes.spines.right':False})
    ax=((1+results).cumprod()).plot(figsize=(11,6),linewidth=1.8)
    ax.set(title='Synthetic demonstration' if args.demo else 'Rolling out-of-sample asset allocation',ylabel='Growth of 1',xlabel='')
    ax.figure.tight_layout()
    ax.figure.savefig(args.output/'wealth.png',dpi=160)
    plt.close(ax.figure)
    print(statistics.round(3).to_string())
    print(f'Artifacts: {args.output}')


if __name__=='__main__':
    main()
