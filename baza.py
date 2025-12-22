import streamlit as st
from supabase import create_client, Client

# 1. Konfiguracja połączenia z Supabase
# Upewnij się, że te dane są w Settings -> Advanced Settings -> Secrets w Streamlit Cloud
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.error("Błąd konfiguracji kluczy API. Sprawdź Secrets w Streamlit.")
    st.stop()

st.set_page_config(page_title="Zarządzanie Magazynem", layout="centered")
st.title("📦 System Zarządzania Magazynem")

# --- SEKCJA 1: DODAWANIE KATEGORII ---
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
                st.rerun() # Odśwież, aby nowa kategoria pojawiła się na liście poniżej
            except Exception as e:
                st.error(f"Błąd zapisu: {e}")
        else:
            st.error("Nazwa kategorii jest wymagana!")

st.markdown("---")

# --- SEKCJA 2: DODAWANIE PRODUKTU ---
st.header("🛒 Dodaj nowy produkt")

# Funkcja pobierająca kategorie
def get_categories():
    try:
        response = supabase.table("kategorie").select("id, nazwa").execute()
        return {item['nazwa']: item['id'] for item in response.data}
    except Exception:
        return {}

kategorie_dict = get_categories()

if not kategorie_dict:
    st.warning("Najpierw dodaj przynajmniej jedną kategorię, aby móc dodać produkt.")
else:
    with st.form("product_form", clear_on_submit=True):
        prod_nazwa = st.text_input("Nazwa produktu")
        prod_liczba = st.number_input("Ilość", min_value=0, step=1)
        prod_cena = st.number_input("Cena (PLN)", min_value=0.0, format="%.2f")
        
        wybrana_kat_nazwa = st.selectbox(
            "Wybierz kategorię", 
            options=list(kategorie_dict.keys())
        )
        
        submitted_prod = st.form_submit_button("Dodaj produkt")
        
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

# --- SEKCJA 3: PODGLĄD TABELI ---
st.markdown("---")
if st.checkbox("Pokaż aktualny stan magazynowy"):
    try:
        # Pobieramy produkty wraz z nazwą kategorii (tzw. JOIN)
        res = supabase.table("produkty").select("nazwa, liczba, cena, kategorie(nazwa)").execute()
        if res.data:
            # Formatowanie danych do ładnej tabeli
            display_data = []
            for item in res.data:
                display_data.append({
                    "Produkt": item['nazwa'],
                    "Ilość": item['liczba'],
                    "Cena": f"{item['cena']} PLN",
                    "Kategoria": item['kategorie']['nazwa'] if item['kategorie'] else "Brak"
                })
            st.table(display_data)
        else:
            st.info("Baza danych jest pusta.")
    except Exception as e:
        st.error(f"Nie udało się pobrać danych: {e}")
