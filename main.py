import streamlit as st
import pandas as pd
from ShipAssignment import ModeloPlanificacionBarcos
from pyomo.environ import ConcreteModel, Set, RangeSet, Var, Binary, Objective, minimize, Constraint, SolverFactory, TerminationCondition
import pandas as pd 

st.title('Aplicación de Planificación de Barcos Naviera')

# 1. Datos de entrada
st.subheader('Datos de entrada')

N = st.number_input('Ingrese el número total de barcos', min_value=1)
D = st.number_input('Ingrese el número total de días en el período de planificación', min_value=1)
T = st.number_input('Ingrese el número de días consecutivos de trabajo en un barco', min_value=1)
P = st.number_input('Ingrese el número mínimo de días de descanso después de trabajar en un barco durante días consecutivos', min_value=1)
max_dias_consecutivos = st.number_input('Ingrese el número máximo de días consecutivos que una persona puede trabajar', min_value=1)

# Initialize input data
A, R, personas = None, None, None

archivo_subido_A = st.file_uploader("Subir archivo CSV de Matriz de Disponibilidad", type="csv")
if archivo_subido_A is not None:
    A = pd.read_csv(archivo_subido_A).values.tolist()
    st.write(pd.DataFrame(A))  # Muestra la tabla de disponibilidad por persona 

archivo_subido_R = st.file_uploader("Subir archivo CSV de Requisitos de Roles", type="csv")
if archivo_subido_R is not None:
    R = pd.read_csv(archivo_subido_R).to_dict('records')
    st.write(pd.DataFrame(R))  # Muestra la tabla de requisitos de roles

archivo_subido_personas = st.file_uploader("Subir archivo CSV de Asignaciones de Roles", type="csv")
if archivo_subido_personas is not None:
    personas_df = pd.read_csv(archivo_subido_personas)
    personas = personas_df.set_index(personas_df.columns[0]).iloc[:, 0].to_dict()
    st.write(personas_df)  # Muestra la tabla de asignaciones de roles

# 2. Ejecución
if st.button('Ejecutar Modelo'):
    if A is not None and R is not None and personas is not None:
        modelo = ModeloPlanificacionBarcos(N, D, T, P, A, R, personas, max_dias_consecutivos)
        modelo.solver()

        # 3. Resultados
        if modelo.resultados.solver.termination_condition == TerminationCondition.optimal:
            df = modelo.resultados_dataframe_streamlit()
            st.dataframe(df)
        else:
            st.write("No se encontró una solución óptima.")
    else:
        st.write("Por favor, cargue todos los archivos requeridos.")
