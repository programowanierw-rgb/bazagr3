import streamlit as st
from supabase import create_client, Client

# 1. Konfiguracja połączenia z Supabase
# Dane te znajdziesz w Settings -> API w panelu Supabase
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Zarządzanie Produktami", layout="centered")
st.title("📦 System Zarządzania Magazynem")

# --- SEKCJA 1: DODAWANIE KATEGORII ---
st.header("Dodaj nową kategorię")
with st.form("category_form", clear_on_submit=True):
    kat_nazwa = st.text_input("Nazwa kategorii")
    kat_opis = st.text_area("Opis kategorii")
    
    submitted_kat = st.form_submit_button("Zapisz kategorię")
    
    if submitted_kat:
        if kat_nazwa:
            data = {"nazwa": kat_nazwa, "opis": kat_opis}
            response = supabase.table("Kategorie").insert(data).execute()
            st.success(f"Dodano kategorię: {kat_nazwa}")
        else:
            st.error("Nazwa kategorii jest wymagana!")

st.markdown("---")

# --- SEKCJA 2: DODAWANIE PRODUKTU ---
st.header("Dodaj nowy produkt")

# Pobieranie aktualnych kategorii do listy rozwijanej
def get_categories():
    response = supabase.table("Kategorie").select("id, nazwa").execute()
    return {item['nazwa']: item['id'] for item in response.data}

kategorie_dict = get_categories()

with st.form("product_form", clear_on_submit=True):
    prod_nazwa = st.text_input("Nazwa produktu")
    prod_liczba = st.number_input("Liczba (szt.)", min_value=0, step=1)
    prod_cena = st.number_input("Cena", min_value=0.0, format="%.2f")
    
    # Wybór kategorii z listy
    wybrana_kat_nazwa = st.selectbox("Wybierz kategorię", options=list(kategorie_dict.keys()))
    
    submitted_prod = st.form_submit_button("Dodaj produkt")
    
    if submitted_prod:
        if prod_nazwa and wybrana_kat_nazwa:
            product_data = {
                "nazwa": prod_nazwa,
                "liczba": prod_liczba,
                "cena": prod_cena,
                "kategoria_id": kategorie_dict[wybrana_kat_nazwa]
            }
            supabase.table("Produkty").insert(product_data).execute()
            st.success(f"Produkt '{prod_nazwa}' został dodany!")
        else:
            st.error("Uzupełnij nazwę produktu!")

# --- PODGLĄD DANYCH ---
if st.checkbox("Pokaż listę produktów"):
    res = supabase.table("Produkty").select("nazwa, liczba, cena, Kategorie(nazwa)").execute()
    st.table(res.data)
