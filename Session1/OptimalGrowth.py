# === Optimal growth model (economic block) solved by direct optimization ===
import numpy as np
from dataclasses import dataclass
from scipy.optimize import minimize
from tqdm import trange
from numba import njit
import copy
import math
import pandas as pd

# --------------------
# 1) Parameters
# --------------------
@dataclass
class Params:
    # horizon / step
    Delta    : int   = 1         # Time step in years
    t0       : int   = 1      # Start year of simulation (fixed)
    tT       : int   = 100      # End year of simulation
    nT       : int   = None      # Number of periods (computed from t0, tT, Delta)


    # technology & shares
    alpha   : float = 0.30    # capital share in Cobb–Douglas
    A0      : float = 1.0        # initial productivity level
    gA      : float = 0.015*0      # productivity growth per year (approx)
    deltaA  : float = 0.005     # TFP growth decline rate
    L0      : float = 1.0        # initial population (scale arbitrary)
    Linf    : float = 10500     # Asymptotic population (millions)
    lg       : float = 0.134/5*0     # Population growth rate parameter

    # capital dynamics
    delta: float = 0.06    # depreciation rate per year
    K0: float = 3.0        # initial capital stock (in output units)

    # preferences (CRRA)
    rho: float = 0.015     # pure rate of time preference
    gamma: float = 2.0     # CRRA (1 / IES)

    tolx     : float = 1e-12      # tolerance on argument
    toly     : float = 1e-3      # tolerance on objective


    # Variable names
    col = ['time', 'K', 'Y', 'I', 'C', 's', 'A', 'L']

    # additional definition
    def __post_init__(self):
        self.nY = len(self.col)
        self.nT = (self.tT + self.Delta - self.t0)//self.Delta
        # Create column-index attributes automatically.
        for i, name in enumerate(self.col):
            setattr(self, f"i_{name}", i)

# --------------------
# 2) Exogenous paths & init
# --------------------
def init_states(p: Params):
    # create simulation matrix
    sim                 = np.full((p.nT, p.nY), np.nan)
    # State: capital
    sim[0, p.i_K] = p.K0
    sim[0, p.i_A] = p.A0
    sim[0, p.i_L] = p.L0
    sim[0, p.i_time] = p.t0
    # set exogenous variables
    for t in range(1, p.nT):
        ## Time and exogenous drivers
        i = t + 1  # DICE index starts at t=1 while Python arrays are 0-based
        # Calendar year: time(t) = t0 + Δ * (i - 1)
        sim[t, p.i_time] = p.t0 + p.Delta * (i - 1)
        # Total factor productivity: A(t) = A(t-1) / [ 1 − g_A * exp(−δ_A * Δ * (i−1)) ]
        sim[t, p.i_A] = sim[t-1, p.i_A] / (1.0 - p.gA * math.exp(-p.deltaA * p.Delta * (i - 1)))
        # Population: L(t) = L(t-1) * [ L_inf / L(t-1) ]^(ℓ_g)
        sim[t, p.i_L] = sim[t-1, p.i_L] * (p.Linf / sim[t-1, p.i_L]) ** p.lg


    # Initial guess for saving path (flat)
    sim[:, p.i_s] = 0.24
    return sim

# --------------------
# 3) Transition (economy only)
# --------------------
@njit(cache=True, fastmath=True)
def update_path_numba(sim,
                      t0, t1,
                      # column indices (ints)
                      i_time, i_K, i_Y, i_I, i_C, i_s, i_A, i_L,
                      # scalars (float64)
                      alpha, delta, Delta
                       ):

    for t in range(t0, t1):
        K = sim[t, i_K]; A = sim[t, i_A]; L = sim[t, i_L]
        Y = A * (K ** alpha) * (L ** (1.0 - alpha))
        s = min(1.0, max(0.0, sim[t, i_s]))
        I = s * Y; C = (1.0 - s) * Y
        sim[t, i_Y] = Y; sim[t, i_I] = I; sim[t, i_C] = C
        if t < sim.shape[0] - 1:
            sim[t+1, i_K] = (1.0 - delta) ** Delta * K + Delta * I
    return sim

def mat_to_df(mat,p: Params) -> pd.DataFrame:
    df = pd.DataFrame(mat, columns=p.col);
    return df


def obj_fun( x: np.ndarray, sim: np.ndarray, timevec: np.ndarray, p: Params, control_id) -> float:
    """
    Objective function (to MINIMIZE) for the planner problem.
   """

    # Control reshaped (N*T)x1 into a matrix TxN
    nT = len(timevec)

    x_matrix = np.column_stack([x[i*nT:(i+1)*nT] for i in range(len(control_id))])
    # Feed into current simulations
    work = sim.copy()  # Avoid mutating the input simulation.
    work[np.ix_(timevec,control_id)] = x_matrix;
    # update path
    work = update_path(work,timevec,p)


    # calculate welfare
    eps   = 1e-12  # Avoid division by zero and log(0).
    disc  = (1.0/(1.0 + p.rho)) ** (np.arange(len(timevec)) * p.Delta)
    C     = work[timevec, p.i_C]
    L_lag = work[np.array(timevec) - 1, p.i_L]
    util  = L_lag * ( (np.power(np.maximum(1000.0*C /L_lag, eps), 1.0 - p.gamma) - 1.0) / (1.0 - p.gamma) )
    W     = - np.sum(disc * util)
    return W

def run_optimal_policy( sim: np.ndarray, timevec: np.ndarray, p: Params,the_bounds: np.ndarray, control_id: np.ndarray) -> np.ndarray:

    # Ensure control_id is a list
    if isinstance(control_id, int):
        control_id = [control_id]

    # Ensure the_bounds is also a list of tuples
    if isinstance(the_bounds, tuple):
        the_bounds = [the_bounds]

    # determine the size of the window for the social planner
    disc = 1
    Tplanner = 1
    while disc > p.toly :
        Tplanner = Tplanner+1
        disc     = disc*np.power(1/(1+p.rho),p.Delta)

    # make a local copy
    popt = copy.deepcopy(p)
    # copy all baseline values from p
    for k, v in p.__dict__.items():
        setattr(popt, k, v)
    # extend the horizon
    popt.nT = p.nT + Tplanner
    # initialize a new path with correct exogenous values
    path_opt = init_states(popt)
     # copy back the endogenous history you already simulated
    path_opt[:p.nT, :] = sim
    path_opt = update_path(path_opt, np.arange(0, p.nT), p)

    # Bounds follow the same ordering as x0.
    bounds = []
    for ci, bnd in zip(control_id, the_bounds):
        bounds.extend([bnd] * Tplanner)

    for ix in trange(1, p.nT, desc="Optimizing"):
        idx = ix + np.arange(0, Tplanner)
        x0 = np.hstack([path_opt[idx, ci] for ci in control_id])
        res = minimize( fun=obj_fun, x0=x0, args=(path_opt, idx, p, control_id), method="L-BFGS-B",bounds=bounds,options={"maxiter": 2000, "maxfun": 200000, "ftol":  popt.tolx})
        if len(control_id) == 1:
            path_opt[idx,control_id]    = res.x
        else:
            nT = len(idx)
            x_matrix = np.column_stack([res.x[i*nT:(i+1)*nT] for i in range(len(control_id))])
            path_opt[np.ix_(idx,control_id)]    = x_matrix
        # updating variables based on new control
        path_opt = update_path(path_opt,idx,p)

    # Remove last Tplanner rows
    path_opt = path_opt[:-Tplanner, :]

    return path_opt



def update_path(sim: np.ndarray, timevec: np.ndarray, p) -> np.ndarray:
    """
    Drop-in replacement for your update_path using Numba inside.
    Assumes all columns (A, L, theta1, mu, s, sigma, E_land, F_EX, etc.)
    are already populated in sim for the needed rows.
    """
    # convenience
    t0 = int(timevec[0])
    t1 = int(timevec[-1]) + 1  # end-exclusive for numba loop

    sim = update_path_numba(sim,
                            t0, t1,
                            # indices
                            p.i_time, p.i_K, p.i_Y, p.i_I, p.i_C, p.i_s, p.i_A, p.i_L,
                            # scalars (float64)
                            float(p.alpha),  float(p.delta),  float(p.Delta) )

    return sim



# --------------------
# 6) Example run & quick plots
# --------------------
if __name__ == "__main__":
    import matplotlib.pyplot as plt

    # Baseline
    p = Params()
    #
    sim = init_states(p)
    timevec = range(1,p.nT)

    the_bounds   = (0, 1);
    control_id   = [p.i_s];
    sim_opt      = run_optimal_policy(sim, timevec, p, the_bounds, control_id);


    years = sim_opt[:, p.i_time].copy()
    fig, axes = plt.subplots(2, 2, figsize=(10, 6))

    axes[0,0].plot(years, sim_opt[:, p.i_s], lw=2)
    axes[0,0].set_title("Optimal saving rate $s_t$")
    axes[0,0].set_xlabel("t"); axes[0,0].set_ylabel("share"); axes[0,0].grid(True)

    axes[0,1].plot(years, sim_opt[:, p.i_K], lw=2)
    axes[0,1].set_title("Capital $K_t$")
    axes[0,1].set_xlabel("t"); axes[0,1].set_ylabel("level"); axes[0,1].grid(True)

    axes[1,0].plot(years, sim_opt[:, p.i_Y], lw=2, label="Y")
    axes[1,0].plot(years, sim_opt[:, p.i_C], lw=2, label="C")
    axes[1,0].plot(years, sim_opt[:, p.i_I], lw=2, label="I")
    axes[1,0].set_title("Output split: $Y_t=C_t+I_t$")
    axes[1,0].set_xlabel("t"); axes[1,0].grid(True); axes[1,0].legend()

    # welfare (print)
    #print("Optimal welfare:", welfare(sim_opt, p))
    #print("First/last saving:", sim_opt[0, p.i_s], sim_opt[-1, p.i_s])

    # per-capita consumption
    c = sim_opt[:, p.i_C] / sim_opt[:, p.i_L]
    axes[1,1].plot(years, c, lw=2)
    axes[1,1].set_title("Per-capita consumption $c_t$")
    axes[1,1].set_xlabel("t"); axes[1,1].grid(True)

    fig.tight_layout()
    plt.show()
