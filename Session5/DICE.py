from __future__ import annotations
import math
from dataclasses import dataclass
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import minimize
from tqdm import trange


# -------------------- Parameters --------------------
@dataclass
class Params:
    # Time grid
    Delta    : int   = 5         # Time step in years
    t0       : int   = 2015      # Start year of simulation (fixed)
    tT       : int   = 2100      # End year of simulation
    nT       : int   = None      # Number of periods (computed from t0, tT, Delta)
    # Social preferences
    rho      : float = 0.015     # Social rate of time preference
    gamma    : float = 1.45      # Intertemporal elasticity of substitution parameter
    deltaK   : float = 0.1       # Depreciation rate of capital (per year)
    alpha    : float = 0.30      # Capital share in production
    # Technology
    A0       : float = 5.115     # Initial total factor productivity
    gA       : float = 0.076     # Initial TFP growth rate
    deltaA   : float = 0.005     # TFP growth decline rate
    # Initial capital
    k0       : float = 220.0     # Initial capital stock
    # Population
    lg       : float = 0.134     # Population growth rate parameter
    Linf     : float = 10500     # Asymptotic population (millions)
    L0       : float = 7403      # Initial population (millions)
    # Decoupling (emissions intensity)
    gsig     : float = 0.0152    # Initial decline rate of emissions intensity
    deltasig : float = 0.00      # Asymptotic change in decline rate
    sigma0   : float = 0.3503    # Initial emissions intensity (tCO₂ / output)
    # Abatement cost parameters
    pb       : float = 550       # Initial backstop technology cost (USD per tCO₂)
    theta2   : float = 2.6       # Abatement cost exponent
    deltapb  : float = 0.025     # Decline rate of backstop cost
    # Climate damage function
    a2       : float = 0.00236   # Quadratic damage coefficient
    a3       : float = 2         # Exponent on temperature in damage function
    a4       : float = 0         # Coefficient second term
    a5       : float = 0         # Exponent second term
    a6       : float = 0         # Activation threshold second term
    # Climate block parameters
    F2XCO2   : float = 3.3613    # Forcing for doubling CO₂ (W/m²)
    T2XCO2   : float = 3.1       # Equilibrium climate sensitivity (°C per doubling CO₂)
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
    # Exogenous forcing (non-CO₂)
    f1       : float = 1.00      # Final non-CO₂ forcing (W/m²)
    f0       : float = 0.50      # Initial non-CO₂ forcing (W/m²)
    tf       : float = 17.0      # Years to reach final forcing
    # Exogenous land-use emissions
    EL0      : float = 2.6       # Initial land-use emissions (GtC/year)
    deltaEL  : float = 0.115     # Decline rate of land-use emissions
    # Numerical options
    s_lower  : float = 0.0       # Lower bound on saving rate
    s_upper  : float = 1.0       # Upper bound on saving rate
    tolx     : float = 1e-10      # tolerance on argument 
    toly     : float = 1e-3      # tolerance on objective
       
    # Variable names
    col = ['time', 'A', 's', 'Y',  'Q', 'C', 'K','L','sigma', 'theta1','mu','E','F','T_AT','T_LO','E_land','F_EX','M_AT','M_UP','M_LO','Tax']
    
    # additional definition
    def __post_init__(self):
        self.nT = (self.tT + self.Delta - self.t0)//self.Delta
        self.nY = len(self.col)
        # mapping indices automatiques
        for i, name in enumerate(self.col):
            setattr(self, f"i_{name}", i)

def init_states(p: Params):
    # create simulation matrix
    sim                 = np.full((p.nT, p.nY), np.nan)
    sim[1:,p.i_s]     = 0.25
    sim[1:,p.i_mu]    = 0
    # set state variables value in 2015
    sim[0, p.i_time]   = p.t0                                      # Initial year
    sim[0, p.i_A]      = p.A0                                      # Initial total factor productivity
    sim[0, p.i_K]      = p.k0                                      # Initial capital stock
    sim[0, p.i_L]      = p.L0                                      # Initial population
    sim[0, p.i_sigma]  = p.sigma0                                  # Initial emissions intensity
    sim[0, p.i_theta1] = p.pb / (1000 * p.theta2) * p.sigma0        # Initial abatement cost coefficient
    sim[0, p.i_T_AT]   = p.T_AT0                                   # Initial atmospheric temperature anomaly (°C)
    sim[0, p.i_T_LO]   = p.T_LO0                                   # Initial lower-ocean temperature anomaly (°C)
    sim[0, p.i_M_AT]   = p.M_AT0                                   # Initial atmospheric CO₂ concentration (GtC)
    sim[0, p.i_M_UP]   = p.M_UP0                                   # Initial upper-ocean CO₂ concentration (GtC)
    sim[0, p.i_M_LO]   = p.M_LO0                                   # Initial lower-ocean CO₂ concentration (GtC)
    # set exogenous variables
    for t in range(1, p.nT):
        ## Time and exogenous drivers
        i = t + 1  # DICE index starts at t=1 while Python arrays are 0-based
        # Calendar year: time(t) = t0 + Δ * (i - 1)
        sim[t, p.i_time] = p.t0 + p.Delta * (i - 1)
        # Total factor productivity: A(t) = A(t-1) / [ 1 − g_A * exp(−δ_A * Δ * (i−1)) ]
        base = 1.0 - p.gA * math.exp(-p.deltaA * p.Delta * (i - 1))
        sim[t, p.i_A] = sim[t-1, p.i_A] / (base ** (p.Delta / 5.0))
        # Population: L(t) = L(t-1) * [ L_inf / L(t-1) ]^(ℓ_g)
        lg_eff = 1.0 - (1.0 - p.lg) ** (p.Delta / 5.0)
        sim[t, p.i_L] = sim[t-1, p.i_L] * (p.Linf / sim[t-1, p.i_L]) ** lg_eff
        # Emissions intensity (σ): σ(t) = σ(t-1) * exp[ −g_σ * ( (1 − δ_σ)^(Δ * t) ) * Δ ]
        sim[t, p.i_sigma]  = sim[t-1, p.i_sigma] * math.exp( - p.gsig * ((1.0 - p.deltasig) ** (p.Delta * (t))) * p.Delta )
        # Abatement cost coefficient (θ₁): θ₁(t) = (p_b / (1000 * θ₂)) * (1 − δ_pb)^(i−1) * σ(t-1)
        sim[t, p.i_theta1] = (p.pb / (1000.0 * p.theta2)) * ((1.0 - p.deltapb) ** (p.Delta/5 * (i-1)))  * sim[t, p.i_sigma]
        # Land-use emissions: E_land(t) = E_L0 * (1 − δ_EL)^(i−1)
        sim[t, p.i_E_land]  = p.EL0 * ((1.0 - p.deltaEL) ** (p.Delta/5 * (i-1)))
        # Exogenous forcing increment: increment = [(f₁ − f₀) * (i−1)] / t_f
        increment = ((p.f1 - p.f0) * p.Delta/5 * (i-1)) / p.tf
        # Exogenous forcing: F_EX(t) = f₀ + min(increment, f₁ − f₀)
        sim[t, p.i_F_EX] = p.f0 + min(increment, p.f1 - p.f0)

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
    work = sim.copy()  # éviter l’effet de bord
    work[np.ix_(timevec,control_id)] = x_matrix;
    # update path
    work = update_path(work,timevec,p)

    
    # calculate welfare
    eps   = 1e-12  # pour éviter divisions/log(0)
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
    popt = Params()
    # copy all baseline values from p
    for k, v in p.__dict__.items():
        setattr(popt, k, v)
    # extend the horizon
    popt.nT = p.nT + Tplanner 
    # initialize a new path with correct exogenous values
    path_opt = init_states(popt)
     # copy back the endogenous history you already simulated
    path_opt[:p.nT, :] = sim   

    # bounds : même ordre que x0
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





from numba import njit


@njit(cache=True, fastmath=True)
def update_path_numba(sim,
                      t_start, t_end,
                      # column indices (ints)
                      i_A, i_L, i_theta1, i_mu, i_s, i_sigma, i_E_land, i_F_EX,
                      i_Y, i_Q, i_C, i_K, i_E, i_Tax,
                      i_F, i_M_AT, i_M_UP, i_M_LO, i_T_AT, i_T_LO, 
                      # scalars (float64)
                      Delta, alpha, a2, a3, a4, a5, a6, theta2, deltaK, xi, F2XCO2, T2XCO2,
                      b12, b23, c1, c3, c4,
                      mat, mup, mlo):
    """
    In-place update of one full DICE step, for t in [t_start, t_end).
    Matches the user's Python version (without external user_damage_fn).
    """
    ln2 = np.log(2.0)
    k_decay = (1.0 - deltaK)**Delta
    
    verbo = 0
    for t in range(t_start, t_end):
        # --- Economic block ---
        # Y(t) = A(t) * K(t-1)^alpha * (L(t)/1000)^(1-alpha)
        L_t = sim[t, i_L]
        A_t = sim[t, i_A]
        Y_t = A_t * (sim[t-1, i_K] ** alpha) * ((L_t / 1000.0) ** (1.0 - alpha))
        sim[t, i_Y] = Y_t
        if verbo : print("t =", t, "Y_t =", Y_t) 
        
        # damages: a2 * T_AT^(a3)  (DICE-style)
        T_tm1 = sim[t-1, i_T_AT]
        damages = a2 * (T_tm1 ** a3)
        # threshold-activated term
        if T_tm1 >  a6:
            damages += a4 * (T_tm1 ** a5)
        if verbo : print("t =", t, "damages =", damages) 

        # Q = Δ * [1 − θ1 * μ^θ2] / [1 + damages] * Y
        mu_t = sim[t, i_mu]
        theta1_t = sim[t, i_theta1]
        Q_t = Delta * (1.0 - theta1_t * (mu_t ** theta2)) / (1.0 + damages) * Y_t
        sim[t, i_Q] = Q_t
        if verbo : print("t =", t, "Q_t =", Q_t) 
        
        # C(t) = (1 − s) * Q
        s_t = sim[t, i_s]
        C_t = (1.0 - s_t) * Q_t
        sim[t, i_C] = C_t
        if verbo : print("t =", t, "C_t =", C_t) 
        
  
        
        # K(t) = (1 − δ_K)^(Δ) * K(t−1) + s * Q
        K_t = k_decay * sim[t-1, i_K] + s_t * Q_t
        sim[t, i_K] = K_t
        if verbo : print("t =", t, "K_t =", K_t) 
        
        # E(t) = Δ * [ σ(t) * (1 − μ) * Y(t) + E_land(t) ]
        sigma_t = sim[t, i_sigma]
        Eland_t = sim[t, i_E_land]
        E_t     = Delta * (sigma_t * (1.0 - mu_t) * Y_t + Eland_t)
        sim[t, i_E] = E_t
        if verbo : print("t =", t, "E_t =", E_t) 
        
        
        # Carbon tax: 1000*xi*theta2*theta1/sigma * mu^(theta2-1)
        # (protect against division by ~0)
        denom = sim[t, i_sigma]
        if denom <= 0.0:
            tax_t = 0.0
        else:
            # handle mu^(theta2-1) at mu=0
            pow_term = 0.0 if (mu_t == 0.0 and theta2 < 1.0) else (mu_t ** (theta2 - 1.0))
            tax_t = 1000.0 * xi * theta2 * theta1_t / denom * pow_term
        sim[t, i_Tax] = tax_t

        # --- Climate block ---
        # F(t) = F2XCO2 * log2(M_AT(t−1)/mat) + F_EX(t)
        MAT_tm1 = sim[t-1, i_M_AT]
        F_t = F2XCO2 * (np.log(MAT_tm1 / mat) / ln2) + sim[t, i_F_EX]
        sim[t, i_F] = F_t

        # Carbon boxes
        MUP_tm1 = sim[t-1, i_M_UP]
        MLO_tm1 = sim[t-1, i_M_LO]
        # M_AT(t) = (1 − Δ·b₁₂)·M_AT(t−1) + Δ·b₁₂·(M_AT₀ / M_UP₀)·M_UP(t−1) + ξ·E(t)
        MAT_t = (1.0 - Delta * b12) * MAT_tm1 + Delta * b12 * (mat / mup) * MUP_tm1 + xi * E_t
        # M_UP(t) = Δ·b₁₂·M_AT(t−1) + (1 − Δ·b₁₂·(M_AT₀ / M_UP₀) − Δ·b₂₃)·M_UP(t−1) + Δ·b₂₃·(M_UP₀ / M_LO₀)·M_LO(t−1)
        MUP_t = Delta * b12 * MAT_tm1 + (1.0 - Delta * b12 * (mat / mup) - Delta * b23) * MUP_tm1 + Delta * b23 * (mup / mlo) * MLO_tm1
        # M_LO(t) = Δ·b₂₃·M_UP(t−1) + (1 − Δ·b₂₃·(M_UP₀ / M_LO₀))·M_LO(t−1) 
        MLO_t = Delta * b23 * MUP_tm1 + (1.0 - Delta * b23 * (mup / mlo)) * MLO_tm1
        sim[t, i_M_AT] = MAT_t
        sim[t, i_M_UP] = MUP_t
        sim[t, i_M_LO] = MLO_t

        # Temperatures
        TLO_tm1 = sim[t-1, i_T_LO]
        # T_AT(t) = T_AT(t−1) + Δ*c1*F(t) − Δ*c1*(F2XCO2/T2XCO2)*T_AT(t−1) − Δ*c1*c3*(T_AT(t−1) − T_LO(t−1))
        TAT_t = T_tm1 + Delta * c1 * F_t - Delta * c1 * (F2XCO2 / T2XCO2) * T_tm1 - Delta * c1 * c3 * (T_tm1 - TLO_tm1)
        #  T_LO(t) = T_LO(t−1) + Δ·c₄·(T_AT(t−1) − T_LO(t−1))
        TLO_t = TLO_tm1 + Delta * c4 * (T_tm1 - TLO_tm1)
        sim[t, i_T_AT] = TAT_t
        sim[t, i_T_LO] = TLO_t

    return sim


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
                            p.i_A, p.i_L, p.i_theta1, p.i_mu, p.i_s, p.i_sigma, p.i_E_land, p.i_F_EX,
                            p.i_Y, p.i_Q, p.i_C, p.i_K, p.i_E, p.i_Tax,
                            p.i_F, p.i_M_AT, p.i_M_UP, p.i_M_LO, p.i_T_AT, p.i_T_LO,
                            # scalars
                            float(p.Delta), float(p.alpha), float(p.a2), float(p.a3), float(p.a4), float(p.a5), float(p.a6), float(p.theta2),
                            float(p.deltaK), float(p.xi), float(p.F2XCO2), float(p.T2XCO2),
                            float(p.b12), float(p.b23), float(p.c1), float(p.c3), float(p.c4),
                            float(p.mat), float(p.mup), float(p.mlo))
    return sim



if __name__ == "__main__":
    

    p = Params()
    
    path = init_states(p)
    timevec = range(1,p.nT)
    path[0:,p.i_mu] = 0.03
    path = update_path(path,timevec,p)

    # Compute welfare on some saving rates
    s0    = np.zeros(p.nT-1)+.2  
    a     = obj_fun(s0, path, timevec, p, [p.i_s])
    s0    = np.zeros(p.nT-1)+.25 
    b     = obj_fun(s0, path, timevec, p, [p.i_s])
    

    # Laissez-faire
    # setting optimization
    print('Compute Laissez-faire: one control')
    the_bounds   = (p.s_lower, p.s_upper);
    control_id   = [p.i_s];
    path_opt_s   = run_optimal_policy(path, timevec, p, the_bounds, control_id);

    # Business-as-usual
    # setting optimization
    print('Compute Optimal tax: two controls')
    the_bounds   = [(p.s_lower, p.s_upper),(0, 1)];
    control_id   = [p.i_s,p.i_mu];
    path_opt_smu = run_optimal_policy(path, timevec, p, the_bounds, control_id);

 
    # plotting main figure
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    # --- Subplot 1: Saving rate ---
    axes[0].plot(path_opt_smu[:, p.i_time], path_opt_smu[:, p.i_s], 
                 label="Optimal transition", color="green", linewidth=2)
    axes[0].plot(path_opt_s[:, p.i_time], path_opt_s[:, p.i_s], 
                 label="No transition", color="red", linestyle="--", linewidth=2)
    axes[0].set_xlabel("Time")
    axes[0].set_ylabel("Saving rate")
    axes[0].set_title("Control 1: Saving rate dynamics")
    axes[0].legend()
    axes[0].grid(True)
    # --- Subplot 2: CO2 Reduction rate ---
    axes[1].plot(path_opt_smu[:, p.i_time], path_opt_smu[:, p.i_mu], 
                 label="Optimal transition", color="green", linewidth=2)
    axes[1].plot(path_opt_s[:, p.i_time], path_opt_s[:, p.i_mu], 
                 label="No transition", color="red", linestyle="--", linewidth=2)
    axes[1].set_xlabel("Time")
    axes[1].set_ylabel("CO2 Reduction rate")
    axes[1].set_title("Control 2: Abatement rate")
    axes[1].legend()
    axes[1].grid(True)
    plt.tight_layout()
    plt.show()

    # possibility to use dataframe
    df   = mat_to_df(path,p)
    df

    # let user define its own damage function
    # possibility
    def my_damage(T, p: Params):
        return 0.003 * (np.asarray(T)**2)

    
    # Exemple d’usage dans le notebook :
    p.user_damage_fn = my_damage
    control_id   = [p.i_s,p.i_mu];
    path_opt_smu_damages = run_optimal_policy(path, timevec, p, the_bounds, control_id);


    # (1) Trajectories
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    axes[0].plot(path_opt_smu[:, p.i_time], path_opt_smu_damages[:, p.i_mu], label="Higher damages (optimal policy)", linewidth=2)
    axes[0].plot(path_opt_smu[:, p.i_time], path_opt_smu[:, p.i_mu], label="Baseline damages (optimal policy)", linestyle="--", linewidth=2)
    axes[0].set_xlabel("Time")
    axes[0].set_ylabel("Abatement rate μ")
    axes[0].set_title("Optimal abatement rate μ")
    axes[0].legend()
    axes[0].grid(True)
    # (1) Trajectories
    axes[1].plot(path_opt_smu[:, p.i_time], path_opt_smu_damages[:, p.i_Tax], label="Higher damages (optimal policy)", linewidth=2)
    axes[1].plot(path_opt_smu[:, p.i_time], path_opt_smu[:, p.i_Tax], label="Baseline damages (optimal policy)", linestyle="--", linewidth=2)
    axes[1].set_xlabel("Time")
    axes[1].set_ylabel("Abatement rate μ")
    axes[1].set_title("Optimal abatement rate μ")
    axes[1].legend()
    axes[1].grid(
    True)
    
