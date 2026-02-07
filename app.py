import streamlit as st
import pandas as pd
import os
from datetime import datetime
import random

# =========================
# CONFIGURACIÓN DE PÁGINA
# =========================
st.set_page_config(
    page_title="⚡ Incident Load Balancer",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================
# ESTILOS CSS
# =========================
st.markdown("""
<style>
    .main-title {
        color: #1E3A8A;
        font-size: 2.5rem;
        font-weight: 800;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 3px solid #3B82F6;
    }
    
    .section-title {
        color: #1E40AF;
        font-size: 1.8rem;
        font-weight: 700;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
    }
    
    .special-task {
        background-color: #FEF3C7;
        border-left: 4px solid #F59E0B;
        padding: 10px;
        margin: 5px 0;
        border-radius: 5px;
        font-weight: 600;
    }
    
    .engineer-card {
        background: white;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        border-left: 5px solid #3B82F6;
    }
</style>
""", unsafe_allow_html=True)

# =========================
# CONFIGURACIÓN
# =========================
DAYS_OF_WEEK = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
DAY_NAMES_ES = {
    "monday": "Lunes",
    "tuesday": "Martes",
    "wednesday": "Miércoles",
    "thursday": "Jueves",
    "friday": "Viernes",
    "saturday": "Sábado",
    "sunday": "Domingo"
}
DAY_SHORT_ES = {
    "monday": "Lun",
    "tuesday": "Mar", 
    "wednesday": "Mié",
    "thursday": "Jue",
    "friday": "Vie",
    "saturday": "Sáb",
    "sunday": "Dom"
}

# Tareas especiales que deben rotar
SPECIAL_TASKS = ["EoS Report", "DCOSS Monitoring"]
SPECIAL_TASK_INTENSITY = 2  # Intensidad fija para tareas especiales

# =========================
# SIDEBAR
# =========================
with st.sidebar:
    st.markdown("## ⚙️ Configuración")
    
    selected_day = st.selectbox(
        "📅 **Seleccionar día**",
        options=DAYS_OF_WEEK,
        format_func=lambda x: DAY_NAMES_ES[x],
        index=0
    )
    
    st.markdown("---")
    st.markdown("### 🎯 Parámetros")
    
    col1, col2 = st.columns(2)
    with col1:
        use_weighted = st.checkbox("📍 Distribución ponderada", value=True)
    with col2:
        randomize = st.checkbox("🎲 Orden aleatorio", value=False)
    
    st.markdown("---")
    st.markdown("### 🔄 Rotación Tareas Especiales")
    
    # Historial de asignaciones de tareas especiales
    if 'special_task_history' not in st.session_state:
        st.session_state.special_task_history = {}
    
    st.info("**Tareas especiales:**")
    for task in SPECIAL_TASKS:
        st.markdown(f"• {task}")

# =========================
# FUNCIONES DE CARGA DE DATOS
# =========================
@st.cache_data
def load_engineers_data():
    """Carga datos de ingenieros"""
    try:
        if os.path.exists("engineers.csv"):
            df = pd.read_csv("engineers.csv")
        else:
            df = pd.DataFrame({
                'engineer_id': [1, 2, 3, 4],
                'engineer_name': ['Sergio', 'Marvin', 'Christopher', 'Esteban'],
                'shift': ['Afternoon', 'Afternoon', 'Afternoon', 'Afternoon'],
                'active': ['yes', 'yes', 'yes', 'yes']
            })
        
        df.columns = df.columns.str.strip()
        df['engineer_name'] = df['engineer_name'].str.strip()
        return df
    except Exception as e:
        st.error(f"❌ Error cargando engineers.csv: {e}")
        return pd.DataFrame()

@st.cache_data
def load_availability_data():
    """Carga datos de disponibilidad"""
    try:
        if os.path.exists("availability.csv"):
            df = pd.read_csv("availability.csv")
        else:
            data = []
            for day in DAYS_OF_WEEK:
                for engineer_id in [1, 2, 3, 4]:
                    available = 'yes' if day != 'sunday' else 'no'
                    data.append({'engineer_id': engineer_id, 'day': day, 'available': available})
            df = pd.DataFrame(data)
        
        df.columns = df.columns.str.strip()
        df['day'] = df['day'].str.lower().str.strip()
        df['available'] = df['available'].str.lower().str.strip()
        return df
    except Exception as e:
        st.error(f"❌ Error cargando availability.csv: {e}")
        return pd.DataFrame()

@st.cache_data
def load_accounts_data():
    """Carga datos de cuentas"""
    try:
        if os.path.exists("accounts.csv"):
            df = pd.read_csv("accounts.csv")
        else:
            accounts_data = {
                'account': [
                    'CMF', 'BGR', 'ITAU', 'Pich Ecuador', 'Pich Peru', 'Arauco', 'CCA', 'Cermaq',
                    'Claro Peru', 'CMA (HNN)', 'CMP', 'DIGICEL', 'Forum', 'INS', 'Lima Exp',
                    'Philips', 'Produbanco', 'Qualitas', 'Recipharm', 'RENIEC', 'Registro Civil',
                    'Suzano', 'Chedraui', 'Walmart', 'EoS Report', 'DCOSS Monitoring'
                ],
                'intensity': [2, 1, 5, 5, 3, 5, 4, 2, 4, 3, 3, 3, 4, 4, 1, 2, 2, 1, 3, 3, 4, 4, 2, 4, 2, 2]
            }
            df = pd.DataFrame(accounts_data)
        
        df.columns = df.columns.str.strip()
        
        # Buscar columna de intensidad
        intensity_cols = [col for col in df.columns if 'intensity' in col.lower()]
        if intensity_cols:
            df = df.rename(columns={intensity_cols[0]: 'intensity'})
        else:
            df['intensity'] = 1
        
        # Buscar columna de account
        account_cols = [col for col in df.columns if 'account' in col.lower() or 'name' in col.lower()]
        if account_cols and 'account' not in df.columns:
            df = df.rename(columns={account_cols[0]: 'account'})
        
        df['intensity'] = pd.to_numeric(df['intensity'], errors='coerce').fillna(2).astype(int)
        return df[['account', 'intensity']].dropna()
    except Exception as e:
        st.error(f"❌ Error cargando accounts.csv: {e}")
        return pd.DataFrame()

# =========================
# ALGORITMO CON ROTACIÓN DE TAREAS ESPECIALES
# =========================
def distribute_with_special_tasks(accounts_df, engineers_list, selected_day, weighted=True, randomize=False):
    """Distribuye cuentas con rotación de tareas especiales"""
    if not engineers_list or accounts_df.empty:
        return pd.DataFrame()
    
    # Separar tareas especiales del resto
    regular_accounts = accounts_df[~accounts_df['account'].isin(SPECIAL_TASKS)].copy()
    special_accounts = accounts_df[accounts_df['account'].isin(SPECIAL_TASKS)].copy()
    
    # Inicializar historial si no existe
    if selected_day not in st.session_state.special_task_history:
        st.session_state.special_task_history[selected_day] = {}
    
    # 1. ASIGNAR TAREAS ESPECIALES (una por ingeniero, diferentes días)
    special_assignments = {}
    
    # Obtener historial de la semana
    week_history = {}
    for day in DAYS_OF_WEEK:
        if day in st.session_state.special_task_history:
            week_history.update(st.session_state.special_task_history[day])
    
    # Para cada tarea especial, encontrar ingeniero que no la haya tenido
    available_engineers = engineers_list.copy()
    
    for task in SPECIAL_TASKS:
        # Filtrar ingenieros que NO han tenido esta tarea esta semana
        engineers_without_task = [
            eng for eng in available_engineers 
            if not any(h.get('task') == task for h in week_history.values() 
                      if h.get('engineer') == eng)
        ]
        
        if engineers_without_task:
            # Elegir ingeniero con menos tareas especiales esta semana
            task_counts = {}
            for eng in engineers_without_task:
                task_counts[eng] = sum(1 for h in week_history.values() 
                                     if h.get('engineer') == eng)
            
            # Elegir ingeniero con menos tareas especiales
            chosen_engineer = min(task_counts.items(), key=lambda x: x[1])[0]
        else:
            # Si todos ya tuvieron esta tarea, reiniciar ciclo
            chosen_engineer = random.choice(available_engineers)
        
        # Asignar tarea especial
        special_assignments[chosen_engineer] = task
        available_engineers = [eng for eng in available_engineers if eng != chosen_engineer]
        
        # Guardar en historial
        st.session_state.special_task_history[selected_day][task] = {
            'engineer': chosen_engineer,
            'task': task,
            'day': selected_day
        }
    
    # 2. DISTRIBUIR CUENTAS REGULARES
    if weighted:
        regular_accounts = regular_accounts.sort_values('intensity', ascending=False)
    
    if randomize:
        regular_accounts = regular_accounts.sample(frac=1, random_state=42).reset_index(drop=True)
    
    # Inicializar estructura
    engineers = {eng: {'accounts': [], 'intensity_sum': 0, 'count': 0} for eng in engineers_list}
    
    # Asignar tareas especiales primero
    for engineer, task in special_assignments.items():
        engineers[engineer]['accounts'].append(f"**{task}**")
        engineers[engineer]['intensity_sum'] += SPECIAL_TASK_INTENSITY
        engineers[engineer]['count'] += 1
    
    # Distribuir cuentas regulares
    for _, row in regular_accounts.iterrows():
        # Encontrar ingeniero con menor carga
        min_engineer = min(engineers.items(), key=lambda x: (x[1]['intensity_sum'], x[1]['count']))
        
        engineers[min_engineer[0]]['accounts'].append(row['account'])
        engineers[min_engineer[0]]['intensity_sum'] += row['intensity']
        engineers[min_engineer[0]]['count'] += 1
    
    # 3. PREPARAR RESULTADOS
    assignments = []
    for engineer, data in engineers.items():
        if data['count'] > 0:
            # Separar tareas especiales (con **) de las regulares
            special_tasks = [acc for acc in data['accounts'] if acc.startswith('**')]
            regular_tasks = [acc for acc in data['accounts'] if not acc.startswith('**')]
            
            # Formatear para mostrar
            accounts_display = []
            if special_tasks:
                accounts_display.extend(special_tasks)
            if regular_tasks:
                accounts_display.extend(regular_tasks)
            
            assignments.append({
                'Ingeniero': engineer,
                'Cuentas Asignadas': ", ".join(accounts_display),
                'Lista Cuentas': data['accounts'],
                'Tiene Tarea Especial': len(special_tasks) > 0,
                'Tarea Especial': special_tasks[0] if special_tasks else "Ninguna",
                'Total Cuentas': data['count'],
                'Intensidad Total': data['intensity_sum'],
                'Intensidad Promedio': round(data['intensity_sum'] / data['count'], 1)
            })
    
    return pd.DataFrame(assignments)

# =========================
# INTERFAZ PRINCIPAL
# =========================
def main():
    # TÍTULO PRINCIPAL
    st.markdown('<h1 class="main-title">⚡ INCIDENT LOAD BALANCER</h1>', unsafe_allow_html=True)
    st.markdown("### Sistema con Rotación de Tareas Especiales")
    
    # Mostrar info de tareas especiales
    with st.expander("📌 Información de Tareas Especiales", expanded=True):
        st.markdown("""
        ### 🔄 **Política de Rotación:**
        
        **EoS Report** y **DCOSS Monitoring** son tareas especiales que deben:
        1. **Asignarse todos los días** (una por día)
        2. **Rotar entre todos los ingenieros**
        3. **Nunca asignarse al mismo ingeniero el mismo día**
        4. **Evitar repetición en la semana**
        
        Cada tarea especial tiene intensidad: **2 puntos**
        """)
    
    # CARGAR DATOS
    with st.spinner("🔄 Cargando datos del sistema..."):
        engineers_df = load_engineers_data()
        availability_df = load_availability_data()
        accounts_df = load_accounts_data()
    
    # VERIFICAR DATOS
    if engineers_df.empty or availability_df.empty or accounts_df.empty:
        st.error("❌ Error crítico: No se pudieron cargar todos los datos necesarios")
        return
    
    # FILTRAR INGENIEROS DISPONIBLES
    day_availability = availability_df[availability_df['day'] == selected_day]
    available_engineers = day_availability[day_availability['available'] == 'yes']
    
    if available_engineers.empty:
        st.warning(f"⚠️ No hay ingenieros disponibles para el {DAY_NAMES_ES[selected_day]}")
        return
    
    available_ids = available_engineers['engineer_id'].tolist()
    available_names = engineers_df[engineers_df['engineer_id'].isin(available_ids)]['engineer_name'].tolist()
    
    # DISTRIBUIR CUENTAS CON TAREAS ESPECIALES
    assignments_df = distribute_with_special_tasks(
        accounts_df, 
        available_names,
        selected_day,
        weighted=use_weighted,
        randomize=randomize
    )
    
    if assignments_df.empty:
        st.warning("⚠️ No se pudieron generar asignaciones")
        return
    
    # =========================
    # RESUMEN DE TAREAS ESPECIALES
    # =========================
    st.markdown("---")
    st.markdown('<h3 class="section-title">📌 ASIGNACIÓN DE TAREAS ESPECIALES HOY</h3>', unsafe_allow_html=True)
    
    # Filtrar ingenieros con tareas especiales
    special_assignments = assignments_df[assignments_df['Tiene Tarea Especial']]
    
    if not special_assignments.empty:
        cols = st.columns(len(special_assignments))
        for idx, (_, row) in enumerate(special_assignments.iterrows()):
            with cols[idx]:
                st.markdown(f"""
                <div style='background-color: #FEF3C7; padding: 15px; border-radius: 10px; 
                            border: 2px solid #F59E0B; text-align: center;'>
                    <div style='font-size: 1.2rem; font-weight: 700; color: #92400E;'>
                        {row['Ingeniero']}
                    </div>
                    <div style='font-size: 1rem; color: #92400E; margin-top: 5px;'>
                        {row['Tarea Especial'].replace('**', '')}
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    # =========================
    # DISPONIBILIDAD
    # =========================
    st.markdown("---")
    st.markdown('<h3 class="section-title">📅 DISPONIBILIDAD</h3>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Tabla de disponibilidad
        availability_table = []
        for _, engineer in engineers_df.iterrows():
            row = {'Ingeniero': engineer['engineer_name']}
            for day in DAYS_OF_WEEK:
                available = availability_df[
                    (availability_df['engineer_id'] == engineer['engineer_id']) & 
                    (availability_df['day'] == day)
                ]
                if not available.empty:
                    status = available.iloc[0]['available']
                    row[DAY_SHORT_ES[day]] = '✅' if status == 'yes' else '❌'
                else:
                    row[DAY_SHORT_ES[day]] = '-'
            availability_table.append(row)
        
        st.dataframe(pd.DataFrame(availability_table), use_container_width=True, hide_index=True)
    
    with col2:
        st.markdown(f"### 📊 {DAY_NAMES_ES[selected_day]}")
        st.metric("Ingenieros Disponibles", len(available_names))
        
        st.markdown("**👥 Disponibles hoy:**")
        for name in available_names:
            st.markdown(f"• {name}")
    
    # =========================
    # MÉTRICAS
    # =========================
    st.markdown("---")
    st.markdown('<h3 class="section-title">📊 MÉTRICAS DE DISTRIBUCIÓN</h3>', unsafe_allow_html=True)
    
    metrics_cols = st.columns(4)
    
    with metrics_cols[0]:
        total_intensity = assignments_df['Intensidad Total'].sum()
        st.metric("Intensidad Total", total_intensity)
    
    with metrics_cols[1]:
        avg_per_engineer = assignments_df['Intensidad Total'].mean()
        st.metric("Promedio x Ing.", f"{avg_per_engineer:.1f}")
    
    with metrics_cols[2]:
        special_count = assignments_df['Tiene Tarea Especial'].sum()
        st.metric("Tareas Especiales", special_count)
    
    with metrics_cols[3]:
        total_accounts = assignments_df['Total Cuentas'].sum()
        st.metric("Cuentas Totales", total_accounts)
    
    # =========================
    # ASIGNACIONES DETALLADAS
    # =========================
    st.markdown("---")
    st.markdown('<h3 class="section-title">📋 ASIGNACIONES COMPLETAS</h3>', unsafe_allow_html=True)
    
    # Preparar datos para mostrar
    display_df = assignments_df[['Ingeniero', 'Cuentas Asignadas', 'Total Cuentas', 'Intensidad Total']].copy()
    
    # Resaltar tareas especiales en la tabla
    def highlight_special_tasks(text):
        if '**EoS Report**' in text or '**DCOSS Monitoring**' in text:
            return 'background-color: #FEF3C7;'
        return ''
    
    # Mostrar tabla
    st.dataframe(
        display_df.style.applymap(highlight_special_tasks, subset=['Cuentas Asignadas']),
        use_container_width=True,
        height=300
    )
    
    # =========================
    # DETALLE POR INGENIERO
    # =========================
    st.markdown("---")
    st.markdown('<h3 class="section-title">👨‍💻 DETALLE POR INGENIERO</h3>', unsafe_allow_html=True)
    
    cols = st.columns(min(len(assignments_df), 4))
    
    for idx, (_, row) in enumerate(assignments_df.iterrows()):
        if idx < len(cols):
            with cols[idx]:
                st.markdown(f"### {row['Ingeniero']}")
                
                col_a, col_b = st.columns(2)
                with col_a:
                    st.metric("Intensidad", row['Intensidad Total'])
                with col_b:
                    st.metric("Cuentas", row['Total Cuentas'])
                
                # Mostrar tarea especial primero si tiene
                special_tasks = [acc for acc in row['Lista Cuentas'] if acc.startswith('**')]
                regular_tasks = [acc for acc in row['Lista Cuentas'] if not acc.startswith('**')]
                
                st.markdown("**📋 Cuentas asignadas:**")
                
                # Tareas especiales
                for task in special_tasks:
                    st.markdown(f"""
                    <div class="special-task">
                        ⭐ {task.replace('**', '')}
                    </div>
                    """, unsafe_allow_html=True)
                
                # Cuentas regulares
                for account in regular_tasks:
                    st.markdown(f"• {account}")
    
    # =========================
    # HISTORIAL DE TAREAS ESPECIALES
    # =========================
    st.markdown("---")
    st.markdown('<h3 class="section-title">📅 HISTORIAL DE TAREAS ESPECIALES</h3>', unsafe_allow_html=True)
    
    # Mostrar historial de la semana
    history_data = []
    for day in DAYS_OF_WEEK:
        if day in st.session_state.special_task_history:
            for task, info in st.session_state.special_task_history[day].items():
                history_data.append({
                    'Día': DAY_NAMES_ES[day],
                    'Tarea': task,
                    'Ingeniero': info['engineer']
                })
    
    if history_data:
        history_df = pd.DataFrame(history_data)
        st.dataframe(history_df, use_container_width=True, hide_index=True)
    else:
        st.info("Aún no hay historial de tareas especiales esta semana.")
    
    # =========================
    # HERRAMIENTAS
    # =========================
    st.markdown("---")
    st.markdown('<h3 class="section-title">🛠️ HERRAMIENTAS</h3>', unsafe_allow_html=True)
    
    tool_cols = st.columns(3)
    
    with tool_cols[0]:
        if st.button("📥 Exportar Asignaciones", use_container_width=True):
            export_df = assignments_df.copy()
            export_df['Día'] = DAY_NAMES_ES[selected_day]
            export_df['Fecha'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            csv = export_df.to_csv(index=False, encoding='utf-8-sig')
            
            st.download_button(
                label="Descargar CSV",
                data=csv,
                file_name=f"asignaciones_{selected_day}.csv",
                mime="text/csv",
                use_container_width=True
            )
    
    with tool_cols[1]:
        if st.button("🔄 Reiniciar Semana", use_container_width=True):
            st.session_state.special_task_history = {}
            st.rerun()
    
    with tool_cols[2]:
        if st.button("📊 Ver Datos", use_container_width=True):
            with st.expander("Datos Crudos", expanded=False):
                st.dataframe(accounts_df, use_container_width=True)

# =========================
# EJECUCIÓN
# =========================
if __name__ == "__main__":
    main()