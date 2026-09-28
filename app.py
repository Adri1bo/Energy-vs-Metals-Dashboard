import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import io

# 1. CONFIGURACIÓ DE LA PÀGINA
st.set_page_config(
    page_title="Energia vs Metalls Preciosos",
    page_icon="📈",
    layout="wide"
)

st.title("📊 Comparació: Energia vs Metalls Preciosos")
st.write("Anàlisi dels últims 5 anys per a l'**Or, Plata, Brent i Gas Natural Europeu**.")

# ------------------------------------------------------------
# 2. EXTRACTOR DE DADES (Amb memòria cau per a optimitzar velocitat)
# ------------------------------------------------------------
@st.cache_data(ttl=86400) # Guarda les dades en memòria durant 24 hores
def carregar_dades():
    fecha_fin = datetime.today()
    fecha_inicio = fecha_fin - timedelta(days=365 * 5)
    
    # 2.1 Or i Plata (Yahoo Finance)
    metales = yf.download(
        ["GC=F", "SI=F"],
        start=fecha_inicio,
        end=fecha_fin,
        auto_adjust=False,
        progress=False
    )["Close"]
    metales.columns = ["Oro", "Plata"]
    metales_mensual = metales.resample("ME").mean()

    # 2.2 Brent (FRED)
    # Modifiquem l'enllaç per assegurar-nos que descarrega el CSV net de dades de FRED
    url_brent = f"https://stlouisfed.org"
    brent = pd.read_csv(url_brent)
    brent["DATE"] = pd.to_datetime(brent["DATE"])
    brent["DCOILBRENTEU"] = pd.to_numeric(brent["DCOILBRENTEU"], errors="coerce")
    brent = brent.set_index("DATE")
    brent_mensual = brent["DCOILBRENTEU"].resample("ME").mean()
    brent_mensual.name = "Brent"

    # 2.3 Gas Natural Europeu (FRED)
    url_gas = f"https://stlouisfed.org"
    gas = pd.read_csv(url_gas)
    gas["DATE"] = pd.to_datetime(gas["DATE"])
    gas["PNGASEUUSDM"] = pd.to_numeric(gas["PNGASEUUSDM"], errors="coerce")
    gas = gas.set_index("DATE")
    gas_mensual = gas["PNGASEUUSDM"].resample("ME").mean()
    gas_mensual.name = "Gas UE"

    # 2.4 Unir i netejar
    datos_unidos = pd.concat([metales_mensual, brent_mensual, gas_mensual], axis=1)
    datos_unidos = datos_unidos.loc[fecha_inicio:fecha_fin].dropna()
    
    # Normalització a 100
    normalizado_unido = datos_unidos / datos_unidos.iloc[0] * 100
    
    # Ratio Oro / Brent
    ratio_unido = datos_unidos["Oro"] / datos_unidos["Brent"]
    
    return datos_unidos, normalizado_unido, ratio_unido

# Executar càrrega de dades
try:
    with st.spinner("Descarregant i processant dades del mercat..."):
        datos, normalizado, ratio_oro_brent = carregar_dades()
    
    # ------------------------------------------------------------
    # 3. INTERFÍCIE WEB - GRÀFIQUES INTERACTIVES
    # ------------------------------------------------------------
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Actius Normalitzats a 100")
        st.write("Evolució comparada agafant el primer valor de la sèrie com a base 100.")
        st.line_chart(normalizado)
        
    with col2:
        st.subheader("⚖️ Ratio Oro / Brent")
        st.write("Quants barrils de Brent equivalen a una onza d'or.")
        st.line_chart(ratio_oro_brent)

    # ------------------------------------------------------------
    # 4. TAULES DE DADES I DESCARREGUES
    # ------------------------------------------------------------
    st.divider()
    st.subheader("📋 Últimes dades i exportació")
    
    tab1, tab2 = st.tabs(["Últims valors analitzats", "Descarregar dades"])
    
    with tab1:
        c1, c2 = st.columns(2)
        with c1:
            st.write("**Últim valor normalitzat:**")
            st.dataframe(normalizado.tail(1).T, use_container_width=True)
        with c2:
            st.write("**Històric recent del Ratio Oro/Brent (Últims 6 mesos):**")
            st.dataframe(ratio_oro_brent.tail(6), use_container_width=True)

    with tab2:
        st.write("Prem el botó de sota per a descarregar un fitxer Excel amb totes les pestanyes calculades.")
        
        # Generar l'Excel en memòria virtual (BytesIO) sense desar en disc dur local
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            datos.to_excel(writer, sheet_name="Precios")
            normalizado.to_excel(writer, sheet_name="Normalizado_100")
            ratio_oro_brent.to_excel(writer, sheet_name="Oro_Brent")
            
        st.download_button(
            label="📥 Descarregar Excel (energia_vs_metales.xlsx)",
            data=buffer.getvalue(),
            file_name="energia_vs_metales_5_anos.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

except Exception as e:
    st.error(f"S'ha produït un error al recuperar les dades: {e}")
    st.info("Això pot ser degut a canvis temporals en els servidors de FRED o Yahoo Finance.")
