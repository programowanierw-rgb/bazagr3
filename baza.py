import streamlit as st
import pandas as pd
from supabase import create_client, Client

# 1. KONFIGURACJA POŁĄCZENIA
@st.cache_resource
def init_connection():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"Błąd konfiguracji kluczy API. Sprawdź Secrets w Streamlit.")
        return None

supabase = init_connection()

if supabase is None:
    st.stop()

# Konfiguracja strony
st.set_page_config(page_title="Magazyn PRO", layout="wide", page_icon="📦")

# --- FUNKCJE POMOCNICZE ---
def get_categories():
    try:
        response = supabase.table("kategorie").select("id, nazwa").execute()
        return {item['nazwa']: item['id'] for item in response.data}
    except Exception:
        return {}

def get_full_data():
    try:
        # Pobieramy dane z JOINem kategorii
        res = supabase.table("produkty").select("id, nazwa, liczba, cena, kategorie(nazwa)").execute()
        if not res.data:
            return pd.DataFrame()
        
        # Przetwarzanie na DataFrame dla łatwiejszej analizy
        df = pd.json_normalize(res.data)
        # Zmiana nazw kolumn po joinie
        df = df.rename(columns={
            'kategorie.nazwa': 'Kategoria',
            'nazwa': 'Produkt',
            'liczba': 'Ilość',
            'cena': 'Cena'
        })
        # Obsługa brakujących danych (NULL w bazie)
        df['Ilość'] = df['Ilość'].fillna(0).astype(int)
        df['Cena'] = df['Cena'].fillna(0.0).astype(float)
        df['Kategoria'] = df['Kategoria'].fillna('Brak')
        # Dodatkowa kolumna: Wartość
        df['Wartość'] = df['Ilość'] * df['Cena']
        return df
    except Exception as e:
        st.error(f"Błąd pobierania danych: {e}")
        return pd.DataFrame()

# --- NAWIGACJA (SIDEBAR) ---
st.sidebar.title("🏢 Magazyn v2.0")
page = st.sidebar.radio("Nawigacja:", ["📊 Dashboard", "📦 Magazyn", "📂 Kategorie"])

# --- SEKCJA 1: DASHBOARD ---
if page == "📊 Dashboard":
    st.title("📊 Analityka Magazynowa")
    df = get_full_data()

    if df.empty:
        st.info("Brak danych do wyświetlenia dashboardu. Dodaj produkty w zakładce Magazyn.")
    else:
        # --- METRYKI ---
        m1, m2, m3 = st.columns(3)
        total_value = df['Wartość'].sum()
        total_qty = df['Ilość'].sum()
        avg_price = df['Cena'].mean()

        m1.metric("Wartość całkowita", f"{total_value:,.2f} PLN")
        m2.metric("Liczba sztuk", f"{total_qty} szt.")
        m3.metric("Średnia cena produktu", f"{avg_price:.2f} PLN")

        st.markdown("---")

        # --- WYKRESY ---
        c1, c2 = st.columns(2)

        with c1:
            st.subheader("📦 Stan ilościowy wg Kategorii")
            cat_qty = df.groupby('Kategoria')['Ilość'].sum()
            st.bar_chart(cat_qty)

        with c2:
            st.subheader("💰 Udział wartościowy Kategorii")
            cat_val = df.groupby('Kategoria')['Wartość'].sum()
            # Wykorzystujemy st.vega_lite_chart dla bardziej profesjonalnego wykresu kołowego
            st.write("Wartości PLN w grupach:")
            st.dataframe(cat_val)

        st.subheader("🔍 Tabela podsumowująca (TOP 5 najdroższych zasobów)")
        st.table(df.nlargest(5, 'Wartość')[['Produkt', 'Kategoria', 'Ilość', 'Wartość']])

# --- SEKCJA 2: KATEGORIE ---
elif page == "📂 Kategorie":
    st.title("📂 Zarządzanie Kategoriami")
    t1, t2, t3 = st.tabs(["📋 Lista", "➕ Dodaj", "🗑️ Usuń"])

    with t1:
        res_kat = supabase.table("kategorie").select("id, nazwa, opis").execute()
        if res_kat.data:
            st.dataframe(res_kat.data, use_container_width=True)
        else:
            st.info("Brak kategorii.")

    with t2:
        with st.form("add_kat"):
            n = st.text_input("Nazwa")
            o = st.text_area("Opis")
            if st.form_submit_button("Zapisz"):
                if n:
                    supabase.table("kategorie").insert({"nazwa": n, "opis": o}).execute()
                    st.success("Dodano!")
                    st.rerun()

    with t3:
        kats = get_categories()
        with st.form("del_kat"):
            sel = st.selectbox("Wybierz do usunięcia", options=list(kats.keys()))
            confirm = st.checkbox("Potwierdzam")
            if st.form_submit_button("USUŃ", type="primary") and confirm:
                supabase.table("kategorie").delete().eq("id", kats[sel]).execute()
                st.rerun()

# --- SEKCJA 3: MAGAZYN ---
elif page == "📦 Magazyn":
    st.title("📦 Zarządzanie Produktami")
    t1, t2, t3 = st.tabs(["📋 Inwentarz", "➕ Przyjmij towar", "🗑️ Wydaj/Usuń"])

    with t1:
        df = get_full_data()
        if not df.empty:
            # Kolorowanie niskich stanów (poniżej 5 sztuk)
            def color_low_stock(val):
                color = 'red' if val < 5 else 'black'
                return f'color: {color}'
            
            st.dataframe(df.style.applymap(color_low_stock, subset=['Ilość']), use_container_width=True)
        else:
            st.info("Pusto.")

    with t2:
        kats = get_categories()
        if not kats:
            st.warning("Dodaj najpierw kategorię!")
        else:
            with st.form("add_prod"):
                nazwa = st.text_input("Nazwa produktu")
                ilosc = st.number_input("Ilość", min_value=0, step=1)
                cena = st.number_input("Cena netto (PLN)", min_value=0.0, format="%.2f")
                kat = st.selectbox("Kategoria", options=list(kats.keys()))
                if st.form_submit_button("Dodaj do magazynu"):
                    if nazwa:
                        supabase.table("produkty").insert({
                            "nazwa": nazwa, "liczba": ilosc, "cena": cena, "kategoria_id": kats[kat]
                        }).execute()
                        st.success("Produkt dodany!")
                        st.rerun()

    with t3:
        df_del = get_full_data()
        if not df_del.empty:
            with st.form("del_prod"):
                prod_options = {f"{r['Produkt']} (ID: {r['id']})": r['id'] for _, r in df_del.iterrows()}
                sel_p = st.selectbox("Produkt", options=list(prod_options.keys()))
                conf_p = st.checkbox("Potwierdzam trwałe usunięcie")
                if st.form_submit_button("USUŃ Z BAZY", type="primary") and conf_p:
                    supabase.table("produkty").delete().eq("id", prod_options[sel_p]).execute()
                    st.rerun()
