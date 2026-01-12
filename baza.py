import streamlit as st
from supabase import create_client, Client

# 1. KONFIGURACJA POŁĄCZENIA
@st.cache_resource
def init_connection():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"Błąd konfiguracji kluczy API. Upewnij się, że URL zaczyna się od https://")
        return None

supabase = init_connection()

if supabase is None:
    st.stop()

# Konfiguracja strony
st.set_page_config(page_title="System Magazynowy", layout="wide")

# --- FUNKCJE POMOCNICZE ---
def get_categories():
    try:
        response = supabase.table("kategorie").select("id, nazwa").execute()
        return {item['nazwa']: item['id'] for item in response.data}
    except Exception:
        return {}

# --- NAWIGACJA (SIDEBAR) ---
st.sidebar.title("🏢 Menu Główne")
page = st.sidebar.radio("Wybierz sekcję:", ["📦 Magazyn", "📂 Kategorie"])

# --- SEKCJA: KATEGORIE ---
if page == "📂 Kategorie":
    st.title("📂 Zarządzanie Kategoriami")
    
    tab_kat_lista, tab_kat_dodaj, tab_kat_usun = st.tabs([
        "📋 Lista kategorii", 
        "➕ Dodaj kategorię", 
        "🗑️ Usuń kategorię"
    ])

    with tab_kat_lista:
        st.header("📋 Zdefiniowane kategorie")
        try:
            res_kat = supabase.table("kategorie").select("id, nazwa, opis").execute()
            if res_kat.data:
                st.dataframe(res_kat.data, use_container_width=True)
            else:
                st.info("Brak zdefiniowanych kategorii.")
        except Exception as e:
            st.error(f"Błąd pobierania: {e}")

    with tab_kat_dodaj:
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
                        st.rerun()
                    except Exception as e:
                        st.error(f"Błąd zapisu: {e}")
                else:
                    st.error("Nazwa kategorii jest wymagana!")

    with tab_kat_usun:
        st.header("🗑️ Usuń kategorię")
        kategorie_opcje = get_categories()
        if kategorie_opcje:
            with st.form("delete_category_form"):
                kat_do_usuniecia = st.selectbox("Wybierz kategorię do usunięcia", options=list(kategorie_opcje.keys()))
                potwierdz_kat = st.checkbox("Potwierdzam chęć usunięcia kategorii")
                btn_usun_kat = st.form_submit_button("USUŃ KATEGORIĘ", type="primary")
                
                if btn_usun_kat:
                    if potwierdz_kat:
                        try:
                            kat_id = kategorie_opcje[kat_do_usuniecia]
                            supabase.table("kategorie").delete().eq("id", kat_id).execute()
                            st.success(f"Usunięto kategorię: {kat_do_usuniecia}")
                            st.rerun()
                        except Exception as e:
                            st.error("Nie można usunąć kategorii, do której przypisane są produkty.")
                    else:
                        st.warning("Musisz zaznaczyć potwierdzenie.")
        else:
            st.info("Brak kategorii.")

# --- SEKCJA: MAGAZYN ---
elif page == "📦 Magazyn":
    st.title("📦 Zarządzanie Produktami")

    tab_prod_lista, tab_prod_dodaj, tab_prod_usun = st.tabs([
        "📋 Lista produktów", 
        "➕ Dodaj produkt", 
        "🗑️ Usuń produkt"
    ])

    with tab_prod_lista:
        st.header("📊 Aktualny stan magazynowy")
        try:
            res = supabase.table("produkty").select("id, nazwa, liczba, cena, kategorie(nazwa)").execute()
            if res.data:
                display_data = []
                total_items = 0
                for item in res.data:
                    # Rozwiązanie błędu "NoneType": używamy or 0
                    ilosc = item['liczba'] if item['liczba'] is not None else 0
                    total_items += ilosc
                    
                    display_data.append({
                        "ID": item['id'],
                        "Produkt": item['nazwa'],
                        "Ilość": ilosc,
                        "Cena": f"{item['cena']:.2f} PLN" if item['cena'] else "0.00 PLN",
                        "Kategoria": item['kategorie']['nazwa'] if item['kategorie'] else "Brak"
                    })
                st.dataframe(display_data, use_container_width=True)
                st.metric("Łączna liczba produktów", total_items)
            else:
                st.info("Magazyn jest pusty.")
        except Exception as e:
            st.error(f"Błąd wyświetlania: {e}")

    with tab_prod_dodaj:
        st.header("🛒 Dodaj nowy produkt")
        kategorie_dict = get_categories()
        if not kategorie_dict:
            st.warning("Dodaj najpierw kategorię.")
        else:
            with st.form("product_form", clear_on_submit=True):
                prod_nazwa = st.text_input("Nazwa produktu")
                prod_liczba = st.number_input("Ilość", min_value=0, step=1, value=0)
                prod_cena = st.number_input("Cena (PLN)", min_value=0.0, format="%.2f")
                wybrana_kat = st.selectbox("Wybierz kategorię", options=list(kategorie_dict.keys()))
                submitted_prod = st.form_submit_button("Dodaj produkt")
                
                if submitted_prod:
                    if prod_nazwa:
                        try:
                            new_product = {
                                "nazwa": prod_nazwa, "liczba": prod_liczba,
                                "cena": prod_cena, "kategoria_id": kategorie_dict[wybrana_kat]
                            }
                            supabase.table("produkty").insert(new_product).execute()
                            st.success(f"Dodano: {prod_nazwa}")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Błąd zapisu: {e}")

    with tab_prod_usun:
        st.header("🗑️ Usuń produkt")
        try:
            res_del = supabase.table("produkty").select("id, nazwa").execute()
            if res_del.data:
                opcje_prod = {f"{i['nazwa']} (ID: {i['id']})": i['id'] for i in res_del.data}
                with st.form("delete_prod_form"):
                    do_usuniecia = st.selectbox("Wybierz produkt", options=list(opcje_prod.keys()))
                    potwierdz_prod = st.checkbox("Potwierdzam usunięcie")
                    if st.form_submit_button("USUŃ", type="primary"):
                        if potwierdz_prod:
                            supabase.table("produkty").delete().eq("id", opcje_prod[do_usuniecia]).execute()
                            st.rerun()
            else:
                st.info("Brak produktów.")
        except Exception as e:
            st.error(f"Błąd: {e}")
