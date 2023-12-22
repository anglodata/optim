from ortools.linear_solver import pywraplp
import numpy as np
import sys
import pandas as pd



def main():
    # Create the linear solver with the GLOP backend.
    solver = pywraplp.Solver.CreateSolver("SAT")
    if not solver:
        return


    

    # set variable names with strings
    # Create the variables x and y. (equivalent to :)
    # x = solver.NumVar(0, solver.infinity(), "x")
    # y = solver.NumVar(0, solver.infinity(), "y")
    # z = solver.NumVar(0, solver.infinity(), "z")

    my_vars = sys.argv[1:]



    for my_var in my_vars:
      globals()[my_var] = solver.NumVar(0, solver.infinity(), my_var)

    print("Number of variables =", solver.NumVariables())
    
    # Create a linear constraint, 0 <= x + y + z<= 

    perf_theo = np.array([150, 100, 80],dtype="float")
    perf_theo_half_month = np.array([2*x for x in perf_theo],dtype="float")
    realized = np.array([100,110,70],dtype="float")

    df = pd.read_csv("monthly_objectives.csv")

    perf_theo = df["perf_theo_10"]
    perf_theo_half_month = df["perf_theo_20"]
    realized_10 = df["realized_10"]

    assert len(perf_theo) == len(perf_theo_half_month)
    assert len(perf_theo) == len(realized_10)
    assert len(perf_theo) == len(my_vars)

    # performance theorique a 20 j:
    # 2x fois la performance hebdo - réalisé
    # 2 cas:
    # sousproduction : delta >0 et la production le mois prochain doit couvrir ce manque
    # si la sous prod est nulle: il faudra produire la quantité du mois +5% (burnout)

    # surproduction : delta <0 et la production le mois prochain peut ralentir
    # la valeur

    delta = perf_theo_half_month - realized
    # si le reste a produire est superieur a l'objectif
    if np.sum(delta) >= np.sum(perf_theo):
      upper_bound = np.sum(delta)*1.05 # value + burnout
      lower_bound = 0
    
    # si le reste a produire est inferieur a l'objectif
    else:
      upper_bound = np.sum(perf_theo)*1.05 # value + burnout
      lower_bound = np.sum(delta)


    ct = solver.Constraint(lower_bound, upper_bound, "ct")
    ct.SetCoefficient(globals()[my_vars[0]], 1)
    ct.SetCoefficient(globals()[my_vars[1]], 1)
    ct.SetCoefficient(globals()[my_vars[2]], 1)

    # delta = perf hebdo vs produced
    coef = perf_theo - realized
    coef = coef < 0
    coef = coef.astype(int)
    print(coef)

    # variable x,y,z
    ctx = solver.Constraint(0.5*(perf_theo_half_month[0]-realized[0]), 
                            min((2*perf_theo[0] - realized[0])*((coef[0]*1.05) + (1 - coef[0])*1.0), perf_theo[0]*1.05), 
                            "ctx")
    ctx.SetCoefficient(globals()[my_vars[0]], 1)

    cty = solver.Constraint(0.5*(perf_theo_half_month[1]-realized[1]), 
                            min((2*perf_theo[1] - realized[1])*((coef[1]*1.05) + (1 - coef[1])*1.0), perf_theo[1]*1.05), 
                            "cty")
    cty.SetCoefficient(globals()[my_vars[1]], 1)

    ctz = solver.Constraint(0.5*(perf_theo_half_month[2]-realized[2]), 
                            min((2*perf_theo[2] - realized[2])*((coef[2]*1.05) + (1 - coef[2])*1.0), perf_theo[2]*1.05), 
                            "ctz")
    ctz.SetCoefficient(globals()[my_vars[2]], 1)


    print("Number of constraints =", solver.NumConstraints())

    # Create the objective function, x + y + z.
    # we want to maximize the number of produced units for each laboratory
    objective = solver.Objective()

    for m_var in my_vars:
      objective.SetCoefficient(globals()[m_var], 1)
      objective.SetMaximization()

    print(f"Solving with {solver.SolverVersion()}")
    solver.Solve()

    print("Solution:")
    print("Objective value =", objective.Value())
    for m_var in my_vars:
      print(f"{m_var} =", globals()[m_var].solution_value())
    

if __name__ == "__main__":
    main()