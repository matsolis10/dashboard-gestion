import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Dashboard de Gestión", layout="wide", page_icon="📊")

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

@st.cache_data(ttl=300)
def load_data():
    file_path = "Gestion de Melbet_Brazzino (1).xlsx" 
    try:
        df_melbet = pd.read_excel(file_path, sheet_name='Melbet')
        df_brazzino = pd.read_excel(file_path, sheet_name='Brazinno')
    except Exception as e:
        st.error(f"Error al cargar el archivo. Revisa el nombre: {e}")
        return pd.DataFrame(), pd.DataFrame()
    
    df_melbet['Ingresos(Recarga)'] = df_melbet['Ingresos(Recarga)'].apply(clean_currency)
    df_melbet['Egresos (Retiro)'] = df_melbet['Egresos (Retiro)'].apply(clean_currency)
    df_melbet['Fecha'] = pd.to_datetime(df_melbet['Fecha']).dt.date
    
    df_brazzino['Deposito'] = df_brazzino['Deposito'].apply(clean_currency)
    df_brazzino['Fecha'] = pd.to_datetime(df_brazzino['Fecha']).dt.date
    
    return df_melbet, df_brazzino

df_melbet, df_brazzino = load_data()

if df_melbet.empty:
    st.stop()

st.title("📊 Dashboard Directivo: Gestión de Plataformas")

if st.sidebar.button("🔄 Refrescar Datos de GitHub"):
    st.cache_data.clear()
    st.rerun()

plataforma = st.sidebar.radio("Navegación", ["Melbet - Resumen", "Melbet - Kardex", "Brazzino"])

# ---- SECCIÓN 1: MELBET RESUMEN ----
if plataforma == "Melbet - Resumen":
    st.header("📈 Resumen Ejecutivo: Melbet")
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("Filtros de Datos")
    
    min_date = df_melbet['Fecha'].min()
    max_date = df_melbet['Fecha'].max()
    
    col_f_inicio, col_f_fin = st.sidebar.columns(2)
    with col_f_inicio:
        fecha_inicio = st.date_input("Fecha Inicio", min_date, min_value=min_date, max_value=max_date)
    with col_f_fin:
        fecha_fin = st.date_input("Fecha Fin", max_date, min_value=min_date, max_value=max_date)
    
    clientes = sorted(df_melbet['Nombre'].dropna().unique())
    cliente_seleccionado = st.sidebar.multiselect("Buscar Cliente(s)", options=clientes)

    df_filtrado = df_melbet.copy()
    df_filtrado = df_filtrado[(df_filtrado['Fecha'] >= fecha_inicio) & (df_filtrado['Fecha'] <= fecha_fin)]
    
    if cliente_seleccionado:
        df_filtrado = df_filtrado[df_filtrado['Nombre'].isin(cliente_seleccionado)]

    st.subheader("Indicadores Clave")
    col1, col2, col3 = st.columns(3)
    total_ingresos = df_filtrado['Ingresos(Recarga)'].sum()
    total_egresos = df_filtrado['Egresos (Retiro)'].sum()
    balance = total_ingresos - total_egresos
    
    col1.metric("Total Ingresos (Recargas)", f"Bs {total_ingresos:,.2f}", f"{len(df_filtrado[df_filtrado['Ingresos(Recarga)'] > 0])} transacciones")
    col2.metric("Total Egresos (Retiros)", f"Bs {total_egresos:,.2f}", f"-{len(df_filtrado[df_filtrado['Egresos (Retiro)'] > 0])} transacciones", delta_color="inverse")
    col3.metric("Balance de Periodo", f"Bs {balance:,.2f}")
    
    st.markdown("---")
    
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.subheader("Flujo Diario")
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
        st.subheader("Top Clientes")
        top_por = st.selectbox("Clasificar por:", ["Ingresos(Recarga)", "Egresos (Retiro)"])
        top_n = st.slider("Cantidad de clientes a mostrar:", 5, 20, 10)
        
        top_clientes = df_filtrado.groupby('Nombre')[top_por].sum().reset_index()
        top_clientes = top_clientes[top_clientes[top_por] > 0]
        top_clientes = top_clientes.sort_values(by=top_por, ascending=False).head(top_n)
        
        color_bar = '#00CC96' if top_por == 'Ingresos(Recarga)' else '#EF553B'
        
        fig_bar = px.bar(top_clientes, x=top_por, y='Nombre', orientation='h', 
                         title=f"Top Clientes por {top_por.split('(')[0]}",
                         color_discrete_sequence=[color_bar])
        fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_bar, use_container_width=True)

# ---- SECCIÓN 2: MELBET KARDEX ACTUALIZADO ----
elif plataforma == "Melbet - Kardex":
    st.header("📋 Kardex Analítico: Melbet")
    
    col_f1, col_f2, col_f3 = st.columns(3)
    
    with col_f1:
        clientes_kardex = sorted(df_melbet['Nombre'].dropna().unique())
        filtro_cliente = st.multiselect("🔍 Buscar Cliente(s)", options=clientes_kardex)
    
    with col_f2:
         min_date_k = df_melbet['Fecha'].min()
         max_date_k = df_melbet['Fecha'].max()
         col_k1, col_k2 = st.columns(2)
         with col_k1:
             f_inicio_k = st.date_input("Fecha Inicio", min_date_k)
         with col_k2:
             f_fin_k = st.date_input("Fecha Fin", max_date_k)
    
    with col_f3:
        tipo_movimiento = st.selectbox("🔄 Tipo de Movimiento", ["Todos", "Solo Recargas (Ingresos)", "Solo Retiros (Egresos)"])
        
    df_kardex = df_melbet.copy()
    
    if filtro_cliente:
        df_kardex = df_kardex[df_kardex['Nombre'].isin(filtro_cliente)]
    df_kardex = df_kardex[(df_kardex['Fecha'] >= f_inicio_k) & (df_kardex['Fecha'] <= f_fin_k)]
    if tipo_movimiento == "Solo Recargas (Ingresos)":
        df_kardex = df_kardex[df_kardex['Ingresos(Recarga)'] > 0]
    elif tipo_movimiento == "Solo Retiros (Egresos)":
        df_kardex = df_kardex[df_kardex['Egresos (Retiro)'] > 0]

    # --- NUEVA ZONA DE KPIs FINANCIEROS ---
    st.markdown("---")
    st.subheader("💡 Inteligencia Financiera (Según Filtros)")
    
    tot_ingresos = df_kardex['Ingresos(Recarga)'].sum()
    tot_egresos = df_kardex['Egresos (Retiro)'].sum()
    balance_neto = tot_ingresos - tot_egresos
    
    # Cálculos avanzados
    margen_casa = ((tot_ingresos - tot_egresos) / tot_ingresos * 100) if tot_ingresos > 0 else 0
    retorno_cliente = (tot_egresos / tot_ingresos * 100) if tot_ingresos > 0 else 0
    
    recs = df_kardex[df_kardex['Ingresos(Recarga)'] > 0]['Ingresos(Recarga)']
    rets = df_kardex[df_kardex['Egresos (Retiro)'] > 0]['Egresos (Retiro)']
    ticket_recarga = recs.mean() if not recs.empty else 0
    ticket_retiro = rets.mean() if not rets.empty else 0
    ratio = len(recs) / len(rets) if len(rets) > 0 else len(recs)

    col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
    
    with col_kpi1:
        st.metric("Subtotal Balance Neto", f"Bs {balance_neto:,.2f}", f"Ingresos: Bs {tot_ingresos:,.0f} | Egresos: Bs {tot_egresos:,.0f}")
    
    with col_kpi2:
        # Si el margen es negativo, significa que la casa perdió dinero
        color_margen = "normal" if margen_casa >= 0 else "inverse"
        st.metric("Margen Neto (Casa)", f"{margen_casa:,.1f}%", f"Retorno al cliente: {retorno_cliente:,.1f}%", delta_color=color_margen)

    with col_kpi3:
        st.metric("Ticket Promedio (Recarga)", f"Bs {ticket_recarga:,.2f}")
    
    with col_kpi4:
        st.metric("Ratio de Frecuencia", f"{ratio:,.1f} a 1", "Por cada retiro, hay 'X' recargas", delta_color="off")

    st.markdown("---")
    
    # --- PREPARACIÓN DE LA TABLA CON FILA DE TOTALES ---
    # Ordenar los datos por fecha
    df_mostrar = df_kardex.sort_values(by='Fecha', ascending=False).copy()
    
    # Convertimos Fecha y Telefono a string temporalmente para la fila total
    df_mostrar['Fecha'] = df_mostrar['Fecha'].astype(str)
    df_mostrar['Telefono'] = df_mostrar['Telefono'].fillna("").astype(str)
    
    # Crear la fila "TOTAL"
    fila_total = pd.DataFrame({
        'Fecha': ['TOTALES'],
        'Nombre': [''],
        'Telefono': [''],
        'Ingresos(Recarga)': [tot_ingresos],
        'Egresos (Retiro)': [tot_egresos]
    })
    
    # Concatenar la fila de total al final
    df_final = pd.concat([df_mostrar, fila_total], ignore_index=True)

    # Mostrar la tabla en la app
    st.dataframe(
        df_final,
        use_container_width=True,
        column_config={
            "Ingresos(Recarga)": st.column_config.NumberColumn("Ingresos (Bs)", format="Bs %.2f"),
            "Egresos (Retiro)": st.column_config.NumberColumn("Egresos (Bs)", format="Bs %.2f")
        },
        hide_index=True
    )

# ---- SECCIÓN 3: BRAZZINO ----
elif plataforma == "Brazzino":
    st.header("🎰 Gestión de Brazzino")
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("Filtros Brazzino")
    
    min_date_bz = df_brazzino['Fecha'].min()
    max_date_bz = df_brazzino['Fecha'].max()
    
    col_bz1, col_bz2 = st.sidebar.columns(2)
    with col_bz1:
        f_inicio_bz = st.date_input("Inicio", min_date_bz)
    with col_bz2:
        f_fin_bz = st.date_input("Fin", max_date_bz)
    
    clientes_bz = sorted(df_brazzino['Nombre'].dropna().unique())
    cliente_seleccionado_bz = st.sidebar.multiselect("Buscar Cliente(s)", options=clientes_bz)
    
    df_filtrado_bz = df_brazzino.copy()
    df_filtrado_bz = df_filtrado_bz[(df_filtrado_bz['Fecha'] >= f_inicio_bz) & (df_filtrado_bz['Fecha'] <= f_fin_bz)]
    
    if cliente_seleccionado_bz:
        df_filtrado_bz = df_filtrado_bz[df_filtrado_bz['Nombre'].isin(cliente_seleccionado_bz)]

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