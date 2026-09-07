import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de la página (¡Ahora ocupa todo el ancho!)
st.set_page_config(page_title="Dashboard de Gestión", layout="wide", page_icon="📊")

# Función para limpiar los datos de moneda (Quitar 'Bs', manejar comas y puntos)
def clean_currency(x):
    if pd.isna(x):
        return 0.0
    if isinstance(x, str):
        x = x.replace('Bs', '').strip()
        if ',' in x and '.' in x:
            x = x.replace('.', '').replace(',', '.')
        elif ',' in x and '.' not in x:
            x = x.replace(',', '.')
        try:
            return float(x)
        except:
            return 0.0
    return float(x)

# Cargar datos
@st.cache_data
def load_data():
    # Asegúrate de que el nombre coincide con tu archivo
    file_path = "Gestion de Melbet_Brazzino (1).xlsx" 
    try:
        df_melbet = pd.read_excel(file_path, sheet_name='Melbet')
        df_brazzino = pd.read_excel(file_path, sheet_name='Brazinno')
    except Exception as e:
        st.error(f"Error al cargar el archivo. Revisa el nombre: {e}")
        return pd.DataFrame(), pd.DataFrame()
    
    # Limpieza Melbet
    df_melbet['Ingresos(Recarga)'] = df_melbet['Ingresos(Recarga)'].apply(clean_currency)
    df_melbet['Egresos (Retiro)'] = df_melbet['Egresos (Retiro)'].apply(clean_currency)
    df_melbet['Fecha'] = pd.to_datetime(df_melbet['Fecha']).dt.date # Convertir a fecha pura
    
    # Limpieza Brazzino
    df_brazzino['Deposito'] = df_brazzino['Deposito'].apply(clean_currency)
    df_brazzino['Fecha'] = pd.to_datetime(df_brazzino['Fecha']).dt.date
    
    return df_melbet, df_brazzino

df_melbet, df_brazzino = load_data()

if df_melbet.empty:
    st.stop() # Detener si no carga el archivo

st.title("📊 Dashboard Directivo: Gestión de Plataformas")

# Sidebar para navegación principal
plataforma = st.sidebar.radio("Navegación", ["Melbet - Resumen", "Melbet - Kardex", "Brazzino"])

# ---- SECCIÓN 1: MELBET RESUMEN ----
if plataforma == "Melbet - Resumen":
    st.header("📈 Resumen Ejecutivo: Melbet")
    
    # FILTROS GLOBALES DE MELBET EN LA BARRA LATERAL
    st.sidebar.markdown("---")
    st.sidebar.subheader("Filtros de Datos")
    
    # Filtro de Fechas
    min_date = df_melbet['Fecha'].min()
    max_date = df_melbet['Fecha'].max()
    fechas = st.sidebar.date_input("Rango de Fechas", [min_date, max_date], min_value=min_date, max_value=max_date)
    
    # Filtro por Clientes
    clientes = sorted(df_melbet['Nombre'].dropna().unique())
    cliente_seleccionado = st.sidebar.multiselect("Buscar Cliente(s)", options=clientes)

    # APLICAR FILTROS
    df_filtrado = df_melbet.copy()
    if len(fechas) == 2:
        df_filtrado = df_filtrado[(df_filtrado['Fecha'] >= fechas[0]) & (df_filtrado['Fecha'] <= fechas[1])]
    if cliente_seleccionado:
        df_filtrado = df_filtrado[df_filtrado['Nombre'].isin(cliente_seleccionado)]

    # KPIs
    st.subheader("Indicadores Clave")
    col1, col2, col3 = st.columns(3)
    total_ingresos = df_filtrado['Ingresos(Recarga)'].sum()
    total_egresos = df_filtrado['Egresos (Retiro)'].sum()
    balance = total_ingresos - total_egresos
    
    col1.metric("Total Ingresos (Recargas)", f"Bs {total_ingresos:,.2f}", f"{len(df_filtrado[df_filtrado['Ingresos(Recarga)'] > 0])} transacciones")
    col2.metric("Total Egresos (Retiros)", f"Bs {total_egresos:,.2f}", f"-{len(df_filtrado[df_filtrado['Egresos (Retiro)'] > 0])} transacciones", delta_color="inverse")
    col3.metric("Balance de Periodo", f"Bs {balance:,.2f}")
    
    st.markdown("---")
    
    # GRÁFICOS INTERACTIVOS
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.subheader("Flujo Diario")
        # Selector para ver Ingresos, Egresos o Ambos
        tipo_flujo = st.radio("Mostrar:", ["Ambos", "Solo Ingresos", "Solo Egresos"], horizontal=True)
        diario = df_filtrado.groupby('Fecha')[['Ingresos(Recarga)', 'Egresos (Retiro)']].sum().reset_index()
        
        if tipo_flujo == "Ambos":
            fig_line = px.area(diario, x='Fecha', y=['Ingresos(Recarga)', 'Egresos (Retiro)'], 
                               labels={'value': 'Monto (Bs)', 'variable': 'Tipo'},
                               color_discrete_map={'Ingresos(Recarga)': '#00CC96', 'Egresos (Retiro)': '#EF553B'})
        elif tipo_flujo == "Solo Ingresos":
            fig_line = px.area(diario, x='Fecha', y='Ingresos(Recarga)', labels={'Ingresos(Recarga)': 'Monto (Bs)'}, color_discrete_sequence=['#00CC96'])
        else:
            fig_line = px.area(diario, x='Fecha', y='Egresos (Retiro)', labels={'Egresos (Retiro)': 'Monto (Bs)'}, color_discrete_sequence=['#EF553B'])
            
        st.plotly_chart(fig_line, use_container_width=True)
    
    with col_chart2:
        st.subheader("Top 10 Clientes")
        # Selector dinámico para el Top
        top_por = st.selectbox("Clasificar por:", ["Ingresos(Recarga)", "Egresos (Retiro)"])
        top_n = st.slider("Cantidad de clientes a mostrar:", 5, 20, 10)
        
        top_clientes = df_filtrado.groupby('Nombre')[top_por].sum().reset_index()
        top_clientes = top_clientes[top_clientes[top_por] > 0] # Filtrar los de monto 0
        top_clientes = top_clientes.sort_values(by=top_por, ascending=False).head(top_n)
        
        color_bar = '#00CC96' if top_por == 'Ingresos(Recarga)' else '#EF553B'
        
        fig_bar = px.bar(top_clientes, x=top_por, y='Nombre', orientation='h', 
                         title=f"Top Clientes por {top_por.split('(')[0]}",
                         color_discrete_sequence=[color_bar])
        fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_bar, use_container_width=True)

# ---- SECCIÓN 2: MELBET KARDEX ----
elif plataforma == "Melbet - Kardex":
    st.header("📋 Kardex Detallado: Melbet")
    
    st.markdown("Filtra y explora las transacciones individuales. Puedes exportar esta tabla si lo necesitas.")
    
    col_f1, col_f2, col_f3 = st.columns(3)
    
    # Filtros específicos del Kardex
    with col_f1:
        clientes_kardex = sorted(df_melbet['Nombre'].dropna().unique())
        filtro_cliente = st.multiselect("🔍 Cliente(s)", options=clientes_kardex)
    
    with col_f2:
         min_date_k = df_melbet['Fecha'].min()
         max_date_k = df_melbet['Fecha'].max()
         filtro_fecha = st.date_input("📅 Fecha", [min_date_k, max_date_k], min_value=min_date_k, max_value=max_date_k)
    
    with col_f3:
        tipo_movimiento = st.selectbox("🔄 Tipo de Movimiento", ["Todos", "Solo Recargas (Ingresos)", "Solo Retiros (Egresos)"])
        
    # Aplicar filtros Kardex
    df_kardex = df_melbet.copy()
    
    if filtro_cliente:
        df_kardex = df_kardex[df_kardex['Nombre'].isin(filtro_cliente)]
        
    if len(filtro_fecha) == 2:
        df_kardex = df_kardex[(df_kardex['Fecha'] >= filtro_fecha[0]) & (df_kardex['Fecha'] <= filtro_fecha[1])]
        
    if tipo_movimiento == "Solo Recargas (Ingresos)":
        df_kardex = df_kardex[df_kardex['Ingresos(Recarga)'] > 0]
    elif tipo_movimiento == "Solo Retiros (Egresos)":
        df_kardex = df_kardex[df_kardex['Egresos (Retiro)'] > 0]
        
    # Mostrar tabla (Streamlit maneja esto maravillosamente con filtros nativos extra en los headers)
    st.dataframe(
        df_kardex.sort_values(by='Fecha', ascending=False),
        use_container_width=True,
        column_config={
            "Ingresos(Recarga)": st.column_config.NumberColumn("Ingresos (Bs)", format="Bs %.2f"),
            "Egresos (Retiro)": st.column_config.NumberColumn("Egresos (Bs)", format="Bs %.2f"),
            "Fecha": st.column_config.DateColumn("Fecha")
        },
        hide_index=True
    )

# ---- SECCIÓN 3: BRAZZINO ----
elif plataforma == "Brazzino":
    st.header("🎰 Gestión de Brazzino")
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("Filtros Brazzino")
    
    # Filtro de Fechas Brazzino
    min_date_bz = df_brazzino['Fecha'].min()
    max_date_bz = df_brazzino['Fecha'].max()
    fechas_bz = st.sidebar.date_input("Rango de Fechas", [min_date_bz, max_date_bz], min_value=min_date_bz, max_value=max_date_bz)
    
    # Filtro por Clientes Brazzino
    clientes_bz = sorted(df_brazzino['Nombre'].dropna().unique())
    cliente_seleccionado_bz = st.sidebar.multiselect("Buscar Cliente(s)", options=clientes_bz)
    
    df_filtrado_bz = df_brazzino.copy()
    if len(fechas_bz) == 2:
        df_filtrado_bz = df_filtrado_bz[(df_filtrado_bz['Fecha'] >= fechas_bz[0]) & (df_filtrado_bz['Fecha'] <= fechas_bz[1])]
    if cliente_seleccionado_bz:
        df_filtrado_bz = df_filtrado_bz[df_filtrado_bz['Nombre'].isin(cliente_seleccionado_bz)]

    # KPIs Brazzino
    total_depositos = df_filtrado_bz['Deposito'].sum()
    st.metric("Total Depósitos (Periodo Seleccionado)", f"Bs {total_depositos:,.2f}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Estado de Bonos (20bs)")
        bonos = df_filtrado_bz['Pago de Bono (20bs)'].fillna('No Pagado').value_counts().reset_index()
        bonos.columns = ['Estado', 'Cantidad']
        fig_pie = px.pie(bonos, values='Cantidad', names='Estado', hole=0.4, color_discrete_sequence=['#2E86C1','#E74C3C'])
        st.plotly_chart(fig_pie, use_container_width=True)
        
    with col2:
        st.subheader("Depósitos en el Tiempo")
        diario_bz = df_filtrado_bz.groupby('Fecha')['Deposito'].sum().reset_index()
        fig_line_bz = px.area(diario_bz, x='Fecha', y='Deposito', color_discrete_sequence=['#2E86C1'])
        st.plotly_chart(fig_line_bz, use_container_width=True)

    st.subheader("📋 Detalle de Transacciones (Brazzino)")
    st.dataframe(
        df_filtrado_bz.sort_values(by='Fecha', ascending=False),
        use_container_width=True,
        hide_index=True
    )