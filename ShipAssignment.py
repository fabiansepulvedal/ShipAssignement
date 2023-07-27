class ModeloPlanificacionBarcos:
    """
    Clase que implementa un modelo de planificación de barcos utilizando la biblioteca Pyomo.

    Parámetros:
    - N: Número total de barcos.
    - D: Número total de días en el período de planificación.
    - T: Número de días consecutivos de trabajo en un barco.
    - P: Número mínimo de días de descanso después de trabajar en un barco durante T días consecutivos.
    - A: Matriz de disponibilidad de las personas en cada día y barco.
    - R: Lista de diccionarios que especifica los requisitos mínimos de personas por rol en cada barco.
    - personas: Diccionario que asigna a cada persona su rol.
    - max_dias_consecutivos: Número máximo de días consecutivos que una persona puede trabajar.

    Métodos:
    - crear_modelo(): Crea el modelo de planificación de barcos.
    - solver(): Resuelve el modelo utilizando un solver de Pyomo.
    - imprimir_resultados(): Imprime los resultados de la planificación en la consola.
    - resultados_dataframe(): Guarda los resultados de la planificación en un archivo Excel.

    """

    def __init__(self, N, D, T, P, A, R, personas, max_dias_consecutivos):
        """
        Inicializa una instancia de la clase ModeloPlanificacionBarcos.

        Parámetros:
        - N: Número total de barcos.
        - D: Número total de días en el período de planificación.
        - T: Número de días consecutivos de trabajo en un barco.
        - P: Número mínimo de días de descanso después de trabajar en un barco durante T días consecutivos.
        - A: Matriz de disponibilidad de las personas en cada día y barco.
        - R: Lista de diccionarios que especifica los requisitos mínimos de personas por rol en cada barco.
        - personas: Diccionario que asigna a cada persona su rol.
        - max_dias_consecutivos: Número máximo de días consecutivos que una persona puede trabajar.
        """
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
        """
        Crea el modelo de planificación de barcos utilizando Pyomo.

        Retorna:
        - m: Modelo de Pyomo.
        """
        m = ConcreteModel()

        # Conjuntos
        m.I = Set(initialize=self.personas.keys())  # personas
        m.J = RangeSet(1, self.N)  # barcos
        m.K = RangeSet(1, self.D)  # días
        m.R = Set(initialize=self.R[0].keys())  # roles

        # Variables
        m.X = Var(m.I, m.J, m.K, within=Binary)
        m.Y = Var(m.I, m.J, m.K, within=Binary)

        # Objetivo
        def regla_objetivo(modelo):
            return sum(modelo.X[i, j, k] for i in modelo.I for j in modelo.J for k in modelo.K)
        m.OBJ = Objective(rule=regla_objetivo, sense=minimize)

        # Restricciones
        def regla_requisito_rol(modelo, j, r, k):
            """
            Restricción que asegura que se cumpla el requisito mínimo de personas por rol en cada barco y día.

            Esta restricción garantiza que la cantidad de personas con el rol 'r' asignadas al barco 'j' en el día 'k'
            sea mayor o igual que el requisito mínimo especificado en el diccionario de requisitos R.

            Parámetros:
            - modelo: Instancia del modelo de Pyomo.
            - j: Número del barco.
            - r: Rol de la persona.
            - k: Número del día.
            """
            return sum(modelo.X[i, j, k] for i in modelo.I if self.personas[i] == r) >= self.R[j - 1][r]

        def regla_dias_consecutivos(modelo, i, j, k):
            """
            Restricción que limita la cantidad de días consecutivos que una persona puede trabajar en un barco.

            Esta restricción asegura que una persona 'i' solo pueda trabajar en el barco 'j' durante un máximo de 'T' días consecutivos.
            Se consideran los días desde 'k + 1' hasta 'k + T', y se suman las variables de decisión correspondientes a otros barcos
            diferentes a 'j' en esos días. Además, se utiliza una variable auxiliar Y para controlar el cambio de barco.

            Parámetros:
            - modelo: Instancia del modelo de Pyomo.
            - i: Número de la persona.
            - j: Número del barco.
            - k: Número del día.
            """
            if k <= self.D - self.T:
                return sum(modelo.X[i, jp, t] for jp in modelo.J if jp != j for t in range(k + 1, k + self.T + 1)) <= self.T * (1 - modelo.Y[i, j, k]) + modelo.X[i, j, k]
            return Constraint.Skip

        def regla_cambio_buque(modelo, i, j, k):
            """
            Restricción que limita el cambio de barco para una persona durante un período de tiempo.

            Esta restricción asegura que una persona 'i' solo pueda cambiar de barco después de trabajar en 'T' días consecutivos en un barco 'j'.
            Se consideran los días desde 'k + 1' hasta 'k + T', y se suman las variables de decisión correspondientes a otros barcos
            diferentes a 'j' en esos días. Además, se utiliza una variable auxiliar Y para controlar el cambio de barco.

            Parámetros:
            - modelo: Instancia del modelo de Pyomo.
            - i: Número de la persona.
            - j: Número del barco.
            - k: Número del día.
            """
            if k <= self.D - self.T:
                return sum(modelo.X[i, jp, t] for jp in modelo.J if jp != j for t in range(k + 1, k + self.T + 1)) <= self.T * (1 - modelo.Y[i, j, k]) + modelo.X[i, j, k]
            return Constraint.Skip

        def regla_dias_descanso(modelo, i, j, k):
            """
            Restricción que garantiza días de descanso después de trabajar en un barco durante T días consecutivos.

            Esta restricción asegura que una persona 'i' tenga un mínimo de 'P' días de descanso después de trabajar 'T' días consecutivos en el barco 'j'.
            Se consideran los días desde 'k + T + 1' hasta 'k + T + P', y se limita la cantidad de días trabajados en ese rango utilizando una variable auxiliar Y.

            Parámetros:
            - modelo: Instancia del modelo de Pyomo.
            - i: Número de la persona.
            - j: Número del barco.
            - k: Número del día.
            """
            if k <= self.D - self.T - self.P:
                return sum(modelo.X[i, j, t] for t in range(k + self.T, k + self.T + self.P)) <= self.P * (1 - modelo.Y[i, j, k])
            return Constraint.Skip

        def regla_asignacion_mismo_dia(modelo, i, k):
            """
            Restricción que limita la asignación de una persona a un máximo de un barco en un día dado.

            Esta restricción asegura que una persona 'i' solo puede ser asignada a un máximo de un barco en un día 'k'.
            Se suma la variable de decisión correspondiente para todos los barcos 'j' y se limita a un máximo de 1.

            Parámetros:
            - modelo: Instancia del modelo de Pyomo.
            - i: Número de la persona.
            - k: Número del día.
            """
            return sum(modelo.X[i, j, k] for j in modelo.J) <= 1

        def regla_max_dias_consecutivos(modelo, i):
            """
            Restricción que limita el número máximo de días consecutivos que una persona puede trabajar.

            Esta restricción asegura que una persona 'i' no trabaje más de 'max_dias_consecutivos' días consecutivos.
            Se suman las variables de decisión correspondientes para todos los barcos 'j' y días 'k' y se limita a un máximo.

            Parámetros:
            - modelo: Instancia del modelo de Pyomo.
            - i: Número de la persona.
            """
            return sum(modelo.X[i, j, k] for j in modelo.J for k in range(1, self.D + 1)) <= self.max_dias_consecutivos

        def regla_disponibilidad(modelo, i, j, k):
            """
            Restricción que considera la disponibilidad de una persona en un barco y día determinados.

            Esta restricción asegura que una persona 'i' solo pueda ser asignada a un barco 'j' en un día 'k' si está disponible según la matriz de disponibilidad 'A'.

            Parámetros:
            - modelo: Instancia del modelo de Pyomo.
            - i: Número de la persona.
            - j: Número del barco.
            - k: Número del día.
            """
            return modelo.X[i, j, k] <= self.A[i - 1][k - 1]


        m.requisito_rol = Constraint(m.J, m.R, m.K, rule=regla_requisito_rol)
        m.dias_consecutivos = Constraint(m.I, m.J, m.K, rule=regla_dias_consecutivos)
        m.cambio_buque = Constraint(m.I, m.J, m.K, rule=regla_cambio_buque)
        m.dias_descanso = Constraint(m.I, m.J, m.K, rule=regla_dias_descanso)
        m.asignacion_mismo_dia = Constraint(m.I, m.K, rule=regla_asignacion_mismo_dia)
        m.max_dias_consecutivos = Constraint(m.I, rule=regla_max_dias_consecutivos)
        m.disponibilidad = Constraint(m.I, m.J, m.K, rule=regla_disponibilidad)

        return m


    def solver(self):
        """
        Resuelve el modelo utilizando un solver de Pyomo.
        """
        solver = SolverFactory('glpk')
        self.resultados = solver.solve(self.modelo)

    def imprimir_resultados(self):
        """
        Imprime los resultados de la planificación en la consola.
        """
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

# Crear el modelo con datos más complejos
R = [{"cocinero": 2, "piloto": 2, "oficial": 1}, {"cocinero": 1, "piloto": 1, "oficial": 1}]
A = [[1] * 14 for _ in range(30)]  # disponibilidad completa

