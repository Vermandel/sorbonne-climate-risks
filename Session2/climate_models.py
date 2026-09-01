from __future__ import annotations
import math
from dataclasses import dataclass
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from typing import Callable, Optional


# -------------------- Parameters --------------------
@dataclass
class Params:
    # Time grid
    Delta    : int   = 5         # Time step in years
    t0       : int   = 2015      # Start year of simulation (fixed)
    tT       : int   = 2100      # End year of simulation
    nT       : int   = None      # Number of periods (computed from t0, tT, Delta)
    # Climate block parameters
    F2XCO2   : float = 3.3613    # Forcing for doubling CO2 (W/m²)
    T2XCO2   : float = 3.1       # Equilibrium climate sensitivity (°C per doubling CO2)
    xi       : float = 3/11      # Carbon cycle parameter (emissions to atmosphere fraction)
    mat      : float = 588       # Preindustrial atmospheric carbon mass (GtC)
    mup      : float = 360       # Preindustrial upper-ocean carbon mass (GtC)
    mlo      : float = 1720      # Preindustrial lower-ocean carbon mass (GtC)
    b12      : float = 0.024     # Carbon transfer rate atmosphere → upper ocean
    b23      : float = 0.0014    # Carbon transfer rate upper ocean → lower ocean
    c1       : float = 0.0201    # Climate system parameter (heat exchange)
    c3       : float = 0.0176    # Climate system parameter (feedback term)
    c4       : float = 0.005     # Climate system parameter (deep ocean heat exchange)
    T_AT0    : float = 0.85      # Initial atmospheric temperature anomaly (°C)
    T_LO0    : float = 0.007     # Initial lower-ocean temperature anomaly (°C)
    M_AT0    : float = 851       # Initial atmospheric carbon mass (GtC)
    M_UP0    : float = 460       # Initial upper-ocean carbon mass (GtC)
    M_LO0    : float = 1740      # Initial lower-ocean carbon mass (GtC)
    mch4     : float = 722       # Preindustrial methane ppb
    M_CH40   : float = 1860      # Modern methane concentration (ppb)
    alpha_ch4 : float = 0.036    # Forcing coefficient (W/m² per sqrt(ppb))
    delta_ch4 : float = 1/9      # Decay rate ~ 10 years lifetime

    # Variable names
    col = ['time', 'E','F','T_AT','T_LO','M_AT','M_UP','M_LO','E_CH4','M_CH4']

    # additional definition
    def __post_init__(self):
        self.nT = (self.tT + self.Delta - self.t0)//self.Delta
        self.nY = len(self.col)
        # Create column-index attributes automatically.
        for i, name in enumerate(self.col):
            setattr(self, f"i_{name}", i)

def init_states(p: Params):
    # create simulation matrix
    sim                 = np.full((p.nT, p.nY), np.nan)
    sim[:,p.i_E]       = 0
    sim[:,p.i_E_CH4]   = 0
    # set state variables value in 2015
    sim[0, p.i_time]   = p.t0                                      # Initial year
    sim[0, p.i_T_AT]   = p.T_AT0                                   # Initial atmospheric temperature anomaly (°C)
    sim[0, p.i_T_LO]   = p.T_LO0                                   # Initial lower-ocean temperature anomaly (°C)
    sim[0, p.i_M_AT]   = p.M_AT0                                   # Initial atmospheric CO₂ concentration (GtC)
    sim[0, p.i_M_UP]   = p.M_UP0                                   # Initial upper-ocean CO₂ concentration (GtC)
    sim[0, p.i_M_LO]   = p.M_LO0                                   # Initial lower-ocean CO₂ concentration (GtC)
    sim[0, p.i_M_CH4]  = p.M_CH40                                   # Initial lower-ocean CO₂ concentration (GtC)
    # set exogenous variables
    for t in range(1, p.nT):
        ## Time and exogenous drivers
        i = t + 1  # DICE index starts at t=1 while Python arrays are 0-based

        # Calendar year: time(t) = t0 + Δ * (i - 1)
        sim[t, p.i_time] = p.t0 + p.Delta * (i - 1)


    return sim

def update_path(sim, p: Params, t_start, t_end) -> np.ndarray:
    ln2 = np.log(2.0)
    t0 = np.where(sim[:,p.i_time] == t_start)[0][0]
    tT = np.where(sim[:,p.i_time] == t_end)[0][0]

    for t in range(t0, tT):

        # F(t) = F2XCO2 * log2(M_AT(t−1)/mat) + F_EX(t)
        sim[t, p.i_F] = p.F2XCO2 * (np.log(sim[t-1, p.i_M_AT] / p.mat) / ln2)  + p.alpha_ch4 * (np.sqrt(sim[t-1, p.i_M_CH4]) - np.sqrt(p.mch4))

        # M_AT(t)      = (1 − Δ·b₁₂)·M_AT(t−1) + Δ·b₁₂·(M_AT₀ / M_UP₀)·M_UP(t−1) + ξ·E(t)
        sim[t, p.i_M_AT] = (1.0 - p.Delta * p.b12) * sim[t-1, p.i_M_AT] + p.Delta * p.b12 * (p.mat / p.mup) * sim[t-1, p.i_M_UP] + p.xi * sim[t-1, p.i_E]
        # M_UP(t)      = Δ·b₁₂·M_AT(t−1) + (1 − Δ·b₁₂·(M_AT₀ / M_UP₀) − Δ·b₂₃)·M_UP(t−1) + Δ·b₂₃·(M_UP₀ / M_LO₀)·M_LO(t−1)
        sim[t, p.i_M_UP] = p.Delta * p.b12 * sim[t-1, p.i_M_AT] + (1.0 - p.Delta * p.b12 * (p.mat / p.mup) - p.Delta * p.b23) * sim[t-1, p.i_M_UP] + p.Delta * p.b23 * (p.mup / p.mlo) * sim[t-1, p.i_M_LO]
        # M_LO(t)      = Δ·b₂₃·M_UP(t−1) + (1 − Δ·b₂₃·(M_UP₀ / M_LO₀))·M_LO(t−1)
        sim[t, p.i_M_LO] = p.Delta * p.b23 * sim[t-1, p.i_M_UP] + (1.0 - p.Delta * p.b23 * (p.mup / p.mlo)) * sim[t-1, p.i_M_LO]

        # Methane stock update
        sim[t, p.i_M_CH4] = sim[t-1, p.i_M_CH4] \
                            - p.Delta * p.delta_ch4 * (sim[t-1, p.i_M_CH4] - p.mch4) \
                            + p.Delta * sim[t-1, p.i_E_CH4]

        # Temperatures
        # T_AT(t)      = T_AT(t−1) + Δ*c1*F(t) − Δ*c1*(F2XCO2/T2XCO2)*T_AT(t−1) − Δ*c1*c3*(T_AT(t−1) − T_LO(t−1))
        sim[t, p.i_T_AT] = sim[t-1, p.i_T_AT] + p.Delta * p.c1 * sim[t, p.i_F] - p.Delta * p.c1 * (p.F2XCO2 / p.T2XCO2) * sim[t-1, p.i_T_AT] - p.Delta * p.c1 * p.c3 * (sim[t-1, p.i_T_AT] - sim[t-1, p.i_T_LO])
        #  T_LO(t) = T_LO(t−1) + Δ·c₄·(T_AT(t−1) − T_LO(t−1))
        sim[t, p.i_T_LO] = sim[t-1, p.i_T_LO] + p.Delta * p.c4 * (sim[t-1, p.i_T_AT] - sim[t-1, p.i_T_LO])


    return sim

def mat_to_df(mat,p: Params) -> pd.DataFrame:
    df = pd.DataFrame(mat, columns=p.col);
    return df


if __name__ == "__main__":


    p       = Params()

    # Time definitions
    p.Delta = 1         # Annual Data
    p.t0    = 1749      #
    p.tT    = 2020
    p.nT    = (p.tT + p.Delta - p.t0)//p.Delta # update number of periods

    # Initialize to pre-industrial carbon
    p.M_AT0 = p.mat
    p.M_UP0 = p.mup
    p.M_LO0 = p.mlo
    # No Temperatures anomalies
    p.T_AT0 = 0
    p.T_LO0 = 0

    path = init_states(p)
    path = update_path(path,p,1750,2020)

    df = mat_to_df(path,p)

    plt.plot(df["time"], df["T_AT"], label="Atmospheric Temperature")
    plt.legend()
    plt.show()
