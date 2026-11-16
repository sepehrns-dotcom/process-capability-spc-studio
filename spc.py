"""Pure SPC calculation functions, independent of the dashboard."""
import numpy as np
import pandas as pd

CONSTANTS = {
    2: (1.880, 0, 3.267, 1.128),
    3: (1.023, 0, 2.574, 1.693),
    4: (0.729, 0, 2.282, 2.059),
    5: (0.577, 0, 2.114, 2.326),
    6: (0.483, 0, 2.004, 2.534),
    7: (0.419, 0.076, 1.924, 2.704),
    8: (0.373, 0.136, 1.864, 2.847),
    9: (0.337, 0.184, 1.816, 2.970),
    10: (0.308, 0.223, 1.777, 3.078),
}

def capability(values, lsl, usl, within_sigma):
    x = np.asarray(values, dtype=float)
    x = x[np.isfinite(x)]
    if len(x) < 2 or lsl >= usl:
        raise ValueError('Need at least two measurements and LSL < USL.')
    mean = float(x.mean())
    overall = float(x.std(ddof=1))
    def ratio(numerator, denom):
        return float(numerator / denom) if denom > 0 else np.nan
    return dict(mean=mean, overall_sigma=overall, within_sigma=within_sigma,
                cp=ratio(usl-lsl, 6*within_sigma),
                cpk=min(ratio(usl-mean, 3*within_sigma), ratio(mean-lsl, 3*within_sigma)),
                pp=ratio(usl-lsl, 6*overall),
                ppk=min(ratio(usl-mean, 3*overall), ratio(mean-lsl, 3*overall)),
                n=len(x), below=int((x<lsl).sum()), above=int((x>usl).sum()))

def imr(values):
    x = np.asarray(values, dtype=float)
    if len(x) < 3 or not np.isfinite(x).all():
        raise ValueError('I-MR needs at least 3 finite measurements.')
    mr = np.abs(np.diff(x))
    mean, mrbar = float(x.mean()), float(mr.mean())
    sigma = mrbar / 1.128
    return dict(kind='I-MR', x=x, r=mr, x_cl=mean, x_ucl=mean+2.66*mrbar,
                x_lcl=mean-2.66*mrbar, r_cl=mrbar, r_ucl=3.267*mrbar,
                r_lcl=0.0, within_sigma=sigma,
                x_ooc=np.where((x>mean+2.66*mrbar)|(x<mean-2.66*mrbar))[0],
                r_ooc=np.where(mr>3.267*mrbar)[0])

def xbar_r(frame):
    if 'subgroup' not in frame:
        raise ValueError('Xbar-R requires a subgroup column.')
    groups = [g['value'].to_numpy(dtype=float) for _,g in frame.groupby('subgroup', sort=False)]
    if len(groups) < 2:
        raise ValueError('Xbar-R requires at least two subgroups.')
    sizes = {len(g) for g in groups}
    if len(sizes)!=1 or next(iter(sizes)) not in CONSTANTS:
        raise ValueError('Xbar-R requires equal subgroup sizes from 2 to 10.')
    n=next(iter(sizes))
    a2,d3,d4,d2=CONSTANTS[n]
    means=np.array([g.mean() for g in groups]); ranges=np.array([np.ptp(g) for g in groups])
    grand=float(means.mean()); rbar=float(ranges.mean())
    xu=grand+a2*rbar; xl=grand-a2*rbar; ru=d4*rbar; rl=d3*rbar
    return dict(kind='Xbar-R', x=means, r=ranges, x_cl=grand, x_ucl=xu, x_lcl=xl,
                r_cl=rbar, r_ucl=ru, r_lcl=rl, within_sigma=rbar/d2,
                x_ooc=np.where((means>xu)|(means<xl))[0],
                r_ooc=np.where((ranges>ru)|(ranges<rl))[0], subgroup_size=n)
