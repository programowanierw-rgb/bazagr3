import streamlit as st
from supabase import create_client, Client

# 1. KONFIGURACJA POŁĄCZENIA
# Upewnij się, że Twoje Secrets w Streamlit Cloud mają klucze: SUPABASE_URL i SUPABASE_KEY
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.error("Błąd konfiguracji kluczy API. Sprawdź ustawienia Secrets w Streamlit.")
    st.stop()

# Konfiguracja strony
st.set_page_config(page_title="System Magazynowy", layout="wide")

# --- FUNKCJE POMOCNICZE (Pobieranie danych) ---
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
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
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

    with col2:
        st.header("📋 Lista kategorii")
        try:
            res_kat = supabase.table("kategorie").select("nazwa, opis").execute()
            if res_kat.data:
                st.table(res_kat.data)
            else:
                st.info("Brak zdefiniowanych kategorii.")
        except Exception as e:
            st.error(f"Błąd pobierania: {e}")

# --- SEKCJA: MAGAZYN ---
elif page == "📦 Magazyn":
    st.title("📦 Zarządzanie Produktami")

    # Zakładki dla Magazynu
    tab_lista, tab_dodaj, tab_usun = st.tabs([
        "📋 Lista produktów", 
        "➕ Dodaj produkt", 
        "🗑️ Usuń produkt"
    ])

    # Tabela z produktami
    with tab_lista:
        st.header("📊 Aktualny stan magazynowy")
        try:
            # JOIN: Pobieramy produkty i nazwy ich kategorii
            res = supabase.table("produkty").select("id, nazwa, liczba, cena, kategorie(nazwa)").execute()
            if res.data:
                display_data = []
                for item in res.data:
                    display_data.append({
                        "ID": item['id'],
                        "Produkt": item['nazwa'],
                        "Ilość": item['liczba'],
                        "Cena": f"{item['cena']:.2f} PLN",
                        "Kategoria": item['kategorie']['nazwa'] if item['kategorie'] else "Brak"
                    })
                st.dataframe(display_data, use_container_width=True)
                
                # Statystyki na dole
                total_items = sum(item['liczba'] for item in res.data)
                st.metric("Łączna liczba produktów (sztuki)", total_items)
            else:
                st.info("Magazyn jest obecnie pusty.")
        except Exception as e:
            st.error(f"Nie udało się pobrać danych: {e}")

    # Formularz dodawania
    with tab_dodaj:
        st.header("🛒 Dodaj nowy produkt")
        kategorie_dict = get_categories()

        if not kategorie_dict:
            st.warning("Najpierw przejdź do sekcji 'Kategorie' i dodaj przynajmniej jedną.")
        else:
            with st.form("product_form", clear_on_submit=True):
                prod_nazwa = st.text_input("Nazwa produktu")
                prod_liczba = st.number_input("Ilość", min_value=0, step=1)
                prod_cena = st.number_input("Cena (PLN)", min_value=0.0, format="%.2f")
                wybrana_kat = st.selectbox("Wybierz kategorię", options=list(kategorie_dict.keys()))
                
                submitted_prod = st.form_submit_button("Dodaj do bazy")
                
                if submitted_prod:
                    if prod_nazwa:
                        try:
                            new_product = {
                                "nazwa": prod_nazwa,
                                "liczba": prod_liczba,
                                "cena": prod_cena,
                                "kategoria_id": kategorie_dict[wybrana_kat]
                            }
                            supabase.table("produkty").insert(new_product).execute()
                            st.success(f"Dodano produkt: {prod_nazwa}")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Błąd: {e}")
                    else:
                        st.error("Nazwa produktu jest wymagana!")

    # Usuwanie produktów
    with tab_usun:
        st.header("🗑️ Usuń produkt")
        try:
            res_del = supabase.table("produkty").select("id, nazwa").execute()
            if res_del.data:
                # Tworzymy opcje wyboru: "Nazwa (ID)"
                opcje = {f"{i['nazwa']} (ID: {i['id']})": i['id'] for i in res_del.data}
                
                with st.form("delete_form"):
                    do_usuniecia = st.selectbox("Wybierz produkt do skasowania", options=list(opcje.keys()))
                    potwierdz = st.checkbox("Potwierdzam, że chcę trwale usunąć ten produkt")
                    przycisk_usun = st.form_submit_button("USUŃ PRODUKT", type="primary")
                    
                    if przycisk_usun:
                        if potwierdz:
                            target_id = opcje[do_usuniecia]
                            supabase.table("produkty").delete().eq("id", target_id).execute()
                            st.success(f"Usunięto: {do_usuniecia}")
                            st.rerun()
                        else:
                            st.warning("Zaznacz pole potwierdzenia przed kliknięciem przycisku.")
            else:
                st.info("Brak produktów w bazie.")
        except Exception as e:
            st.error(f"Błąd usuwania: {e}")
