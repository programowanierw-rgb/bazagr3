import streamlit as st
from supabase import create_client, Client

# 1. Konfiguracja połączenia z Supabase
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.error("Błąd konfiguracji kluczy API. Sprawdź Secrets w Streamlit.")
    st.stop()

# Konfiguracja strony
st.set_page_config(page_title="Zarządzanie Magazynem", layout="wide")

# --- NAWIGACJA (SIDEBAR) ---
st.sidebar.title("🏢 Menu Główne")
page = st.sidebar.radio("Wybierz sekcję:", ["📦 Magazyn", "📂 Kategorie"])

# Funkcje pomocnicze
def get_categories():
    try:
        response = supabase.table("kategorie").select("id, nazwa").execute()
        return {item['nazwa']: item['id'] for item in response.data}
    except Exception:
        return {}

# --- STRONA: KATEGORIE ---
if page == "📂 Kategorie":
    st.title("📂 Zarządzanie Kategoriami")
    
    st.header("➕ Dodaj nową kategorię")
    with st.form("category_form", clear_on_submit=True):
        kat_nazwa = st.text_input("Nazwa kategorii (np. Elektronika)")
        kat_opis = st.text_area("Opis kategorii")
        submitted_kat = st.form_submit_button("Zapisz kategorię")
        
        if submitted_kat:
            if kat_nazwa:
                try:
                    data = {"nazwa": kat_nazwa, "opis": kat_opis}
                    supabase.table("kategorie").insert(data).execute()
                    st.success(f"Dodano kategorię: {kat_nazwa}")
                except Exception as e:
                    st.error(f"Błąd zapisu: {e}")
            else:
                st.error("Nazwa kategorii jest wymagana!")

    st.markdown("---")
    st.header("📋 Lista istniejących kategorii")
    try:
        res_kat = supabase.table("kategorie").select("nazwa, opis").execute()
        if res_kat.data:
            st.table(res_kat.data)
        else:
            st.info("Brak zdefiniowanych kategorii.")
    except Exception as e:
        st.error(f"Błąd pobierania: {e}")

# --- STRONA: MAGAZYN ---
elif page == "📦 Magazyn":
    st.title("📦 Stan Magazynowy")

    # Zakładki wewnątrz strony Magazyn
    tab1, tab2 = st.tabs(["📋 Lista produktów", "➕ Dodaj produkt"])

    with tab2:
        st.header("🛒 Dodaj nowy produkt")
        kategorie_dict = get_categories()

        if not kategorie_dict:
            st.warning("Najpierw dodaj przynajmniej jedną kategorię w sekcji 'Kategorie'.")
        else:
            with st.form("product_form", clear_on_submit=True):
                prod_nazwa = st.text_input("Nazwa produktu")
                prod_liczba = st.number_input("Ilość", min_value=0, step=1)
                prod_cena = st.number_input("Cena (PLN)", min_value=0.0, format="%.2f")
                wybrana_kat_nazwa = st.selectbox("Wybierz kategorię", options=list(kategorie_dict.keys()))
                
                submitted_prod = st.form_submit_button("Dodaj produkt do bazy")
                
                if submitted_prod:
                    if prod_nazwa:
                        try:
                            product_data = {
                                "nazwa": prod_nazwa,
                                "liczba": prod_liczba,
                                "cena": prod_cena,
                                "kategoria_id": kategorie_dict[wybrana_kat_nazwa]
                            }
                            supabase.table("produkty").insert(product_data).execute()
                            st.success(f"Produkt '{prod_nazwa}' został dodany!")
                        except Exception as e:
                            st.error(f"Błąd zapisu produktu: {e}")
                    else:
                        st.error("Nazwa produktu jest wymagana!")

    with tab1:
        st.header("📊 Aktualny inwentarz")
        try:
            res = supabase.table("produkty").select("nazwa, liczba, cena, kategorie(nazwa)").execute()
            if res.data:
                display_data = []
                for item in res.data:
                    display_data.append({
                        "Produkt": item['nazwa'],
                        "Ilość": item['liczba'],
                        "Cena": f"{item['cena']:.2f} PLN",
                        "Kategoria": item['kategorie']['nazwa'] if item['kategorie'] else "Brak"
                    })
                st.dataframe(display_data, use_container_width=True)
                
                # Prosta statystyka
                total_items = sum(item['liczba'] for item in res.data)
                st.metric("Całkowita liczba sztuk w magazynie", total_items)
                
            else:
                st.info("Magazyn jest obecnie pusty.")
        except Exception as e:
            st.error(f"Nie udało się pobrać danych: {e}")
