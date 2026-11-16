import numpy as np
import pandas as pd
from spc import imr, xbar_r, capability

def test_imr_constant_series():
    a=imr([5,5,5,5]); assert a['within_sigma']==0
    assert len(a['x_ooc'])==0

def test_imr_known():
    a=imr([1,2,3,4]); assert np.isclose(a['r_cl'],1)
    assert np.isclose(a['within_sigma'],1/1.128)

def test_xbar_r_known():
    f=pd.DataFrame({'subgroup':[1,1,2,2,3,3],'value':[1,3,2,4,3,5]})
    a=xbar_r(f)
    assert np.isclose(a['x_cl'],3)
    assert np.isclose(a['r_cl'],2)
    assert np.isclose(a['x_ucl'],3+1.88*2)

def test_capability_known():
    x=np.array([9,10,11]); r=capability(x,7,13,1)
    assert np.isclose(r['cp'],1)
    assert np.isclose(r['cpk'],1)
