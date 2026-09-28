import streamlit as st
import pandas as pd
import io

# Configuració de la pàgina
st.set_page_config(
    page_title="Lector de Dades CSV",
    page_icon="📊",
    layout="centered"
)

st.title("📊 Lector i Visor de Dades")
st.write("Aquesta aplicació llegeix fitxers CSV corregint automàticament els errors de format.")

# Zona per pujar el fitxer des de la web
fitxer_pujat = st.file_uploader("Puja el teu fitxer CSV aquí", type=["csv", "txt"])

if fitxer_pujat is not None:
    try:
        # Llegim els primers bytes per detectar el separador automàticament
        contingut = fitxer_pujat.getvalue().decode("utf-8", errors="ignore")
        
        # Intentem detectar si és punt i coma o coma
        if ";" in contingut.split("\n")[0]:
            separador = ";"
        elif "\t" in contingut.split("\n")[0]:
            separador = "\t"
        else:
            separador = ","
            
        # Tornem al principi del fitxer per a que Pandas el llegeixi
        fitxer_pujat.seek(0)
        
        # Llibreria Pandas optimitzada per saltar-se línies corruptes (com la línia 36)
        df = pd.read_csv(
            fitxer_pujat, 
            sep=separador, 
            on_bad_lines='skip',  # Salta les línies amb errors en lloc de fallar
            engine='python'
        )
        
        st.success("🎉 Fitxer carregat correctament!")
        
        # Mostrem mètriques bàsiques
        col1, col2 = st.columns(2)
        col1.metric("Files totals", df.shape[0])
        col2.metric("Columnes detectades", df.shape[1])
        
        # Mostrem la taula de dades
        st.subheader("Vista prèvia de les dades:")
        st.dataframe(df.head(100)) # Mostra les primeres 100 files
        
    except Exception as e:
        st.error(f"S'ha produït un error al processar el fitxer: {e}")
else:
    st.info("👋 Si us plau, puja un fitxer CSV per començar a visualitzar les dades.")
