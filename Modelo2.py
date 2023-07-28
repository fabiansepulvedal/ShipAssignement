from pyomo.environ import ConcreteModel
import pyomo.environ as pyo
from pyomo.environ import ConcreteModel, Set, RangeSet, Var, Binary, Objective, minimize, Constraint, SolverFactory, TerminationCondition, NonNegativeIntegers
import pandas as pd 

class ModeloPlanificacionBarcosBeta:
    def __init__(self, N, D, T, P, A, R, personas, max_dias_consecutivos):
        self.N = N
        self.D = D
        self.T = T
        self.P = P
        self.A = A
        self.R = R
        self.personas = personas
        self.max_dias_consecutivos = max_dias_consecutivos
        self.modelo = self.crear_modelo()

    def crear_modelo(self):
        m = ConcreteModel()

        m.I = Set(initialize=self.personas.keys())  # personas
        m.J = RangeSet(1, self.N)  # barcos
        m.K = RangeSet(1, self.D)  # días
        m.R = Set(initialize=self.R[0].keys())  # roles

        m.X = Var(m.I, m.J, m.K, within=Binary)
        m.Y = Var(m.I, m.J, m.K, within=Binary)
        m.Z = Var()

        def regla_objetivo(modelo):
            return modelo.Z
        m.OBJ = Objective(rule=regla_objetivo, sense=minimize)

        # Updated constraints
        def regla_requisito_rol(modelo, j, r, k):
            return sum(modelo.X[i, j, k] for i in modelo.I if self.personas[i] == r) >= self.R[j - 1][r]

        def regla_dias_consecutivos(modelo, i, j, k):
            if k <= modelo.K - self.T + 1:
                return sum(modelo.X[i, j, kp] for kp in range(k, min(k + self.T, self.D+1))) - self.T * modelo.Y[i, j, k] >= 0
            return Constraint.Skip

        def regla_dias_descanso(modelo, i, k):
            if k <= self.D - self.T - self.P:
                return sum(modelo.X[i, j, t] for t in range(k + self.T + 1, k + self.T + self.P + 1) for j in modelo.J) <= self.P * (1 - sum(modelo.Y[i, j, k] for j in modelo.J))
            return Constraint.Skip

        def regla_asignacion_mismo_dia(modelo, i, k):
            return sum(modelo.X[i, j, k] for j in modelo.J) <= 1

        def regla_max_dias_consecutivos(modelo, i):
            return sum(modelo.X[i, j, k] for j in modelo.J for k in range(1, self.D + 1)) <= self.max_dias_consecutivos

        def regla_disponibilidad(modelo, i, j, k):
            return modelo.X[i, j, k] <= self.A[i - 1][k - 1]

        def regla_max_workload(modelo, i):
            return sum(modelo.X[i, j, k] for j in modelo.J for k in modelo.K) <= modelo.Z

        m.requisito_rol = Constraint(m.J, m.R, m.K, rule=regla_requisito_rol)
        #m.dias_consecutivos = Constraint(m.I, m.J, m.K, rule=regla_dias_consecutivos)
        m.dias_descanso = Constraint(m.I, m.K, rule=regla_dias_descanso)
        m.asignacion_mismo_dia = Constraint(m.I, m.K, rule=regla_asignacion_mismo_dia)
        m.max_dias_consecutivos = Constraint(m.I, rule=regla_max_dias_consecutivos)
        m.disponibilidad = Constraint(m.I, m.J, m.K, rule=regla_disponibilidad)
        m.max_workload = Constraint(m.I, rule=regla_max_workload)

        return m

    def solver(self):
        solver = SolverFactory('glpk')
        self.resultados = solver.solve(self.modelo)

    def imprimir_resultados(self):
        if self.resultados.solver.termination_condition == TerminationCondition.optimal:
            print("Valor Objetivo: ", self.modelo.OBJ())
            for i in self.modelo.I:
                for j in self.modelo.J:
                    for k in self.modelo.K:
                        if self.modelo.X[i, j, k].value > 0:
                            print(f"Persona {i} (Rol: {self.personas[i]}) asignada al barco {j} el día {k}.")
        else:
            print("No se encontró una solución óptima.")

    def resultados_dataframe(self):
        """
        Guarda los resultados de la planificación en un archivo Excel.
        """
        if self.resultados.solver.termination_condition == TerminationCondition.optimal:
            print("Valor Objetivo: ", self.modelo.OBJ())

            # Recopilar datos en una lista de diccionarios
            data = []
            for j in self.modelo.J:
                for i in self.modelo.I:
                    fila = {"barcos": f"barco {j}", "persona": f"persona {i} (Rol: {self.personas[i]})"}
                    for k in self.modelo.K:
                        fila[f"día {k}"] = 1 if self.modelo.X[i, j, k].value >= 0.5 else 0
                    data.append(fila)

            # Crear DataFrame
            df = pd.DataFrame(data)
            df = df.set_index(["barcos", "persona"])

            # Guardar DataFrame en un archivo Excel
            df.to_excel("planificacion_barcos.xlsx")
        else:
            print("No se encontró una solución óptima.")

    def resultados_dataframe_streamlit(self):
        """
        Returns the results of the planning as a pandas DataFrame.
        """
        if self.resultados.solver.termination_condition == TerminationCondition.optimal:
            print("Valor Objetivo: ", self.modelo.OBJ())

            # Collect data in a list of dictionaries
            data = []
            for j in self.modelo.J:
                for i in self.modelo.I:
                    fila = {"barcos": f"barco {j}", "persona": f"persona {i} (Rol: {self.personas[i]})"}
                    for k in self.modelo.K:
                        fila[f"día {k}"] = 1 if self.modelo.X[i, j, k].value >= 0.5 else 0
                    data.append(fila)

            # Create DataFrame
            df = pd.DataFrame(data)
            df = df.set_index(["barcos", "persona"])

            return df
        else:
            print("No se encontró una solución óptima.")
            return None
