import streamlit as st
import pandas as pd
from ShipAssignment import ModeloPlanificacionBarcos
from pyomo.environ import ConcreteModel, Set, RangeSet, Var, Binary, Objective, minimize, Constraint, SolverFactory, TerminationCondition

st.title('Aplicación de Planificación de Barcos')

# 1. Datos de entrada
st.subheader('Datos de entrada')

N = st.number_input('Ingrese el número total de barcos', min_value=1)
D = st.number_input('Ingrese el número total de días en el período de planificación', min_value=1)
T = st.number_input('Ingrese el número de días consecutivos de trabajo en un barco', min_value=1)
P = st.number_input('Ingrese el número mínimo de días de descanso después de trabajar en un barco durante días consecutivos', min_value=1)
max_dias_consecutivos = st.number_input('Ingrese el número máximo de días consecutivos que una persona puede trabajar', min_value=1)

archivo_subido_A = st.file_uploader("Subir archivo CSV de Matriz de Disponibilidad", type="csv")
if archivo_subido_A is not None:
    A = pd.read_csv(archivo_subido_A)
    st.write(A)  # Muestra la tabla de disponibilidad

archivo_subido_R = st.file_uploader("Subir archivo CSV de Requisitos de Roles", type="csv")
if archivo_subido_R is not None:
    R = pd.read_csv(archivo_subido_R).to_dict()
    st.write(R)  # Muestra la tabla de requisitos de roles

archivo_subido_personas = st.file_uploader("Subir archivo CSV de Asignaciones de Roles", type="csv")
if archivo_subido_personas is not None:
    personas = pd.read_csv(archivo_subido_personas).to_dict()
    st.write(personas)  # Muestra la tabla de asignaciones de roles

# 2. Ejecución
if st.button('Ejecutar Modelo'):
    modelo = ModeloPlanificacionBarcos(N, D, T, P, A, R, personas, max_dias_consecutivos)
    modelo.solver()

    # 3. Resultados
    resultados = modelo.resultados_dataframe()
    st.write(resultados)
