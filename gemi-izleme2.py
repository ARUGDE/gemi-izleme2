import streamlit as st
from datetime import datetime, timedelta, timezone
import firebase_admin
from firebase_admin import credentials, db
import json
import asyncio

# --- SAYFA YAPILANDIRMASI ---
st.set_page_config(page_title="Gemi Operasyon Takibi", layout="wide")

# --- STATİK VERİLER (VEM_DATA) ---
VEM_DATA = {
    "001": 391.791, "002": 389.295, "003": 392.011, "004": 391.557, "005": 389.851, 
    "006": 391.441, "007": 391.493, "008": 390.552, "009": 389.794, "010": 178.753, 
    "011": 180.166, "012": 178.061, "013": 392.32,  "014": 178.185, "015": 178.411, 
    "016": 1039.497,"017": 1034.121,"018": 1025.938,"019": 1025.27, "020": 1027.811, 
    "021": 97.898,  "022": 98.003,  "023": 98.462,  "024": 98.404,  "025": 98.61, 
    "026": 781.143, "027": 1127.928,"028": 254.253, "029": 517.076, "030": 522.115, 
    "031": 107.283, "032": 107.524, "033": 107.698, "034": 107.664, "035": 526.755, 
    "036": 527.766, "037": 527.367, "038": 527.952, "039": 527.616, "040": 541.741, 
    "041": 542.375, "042": 526.247, "043": 527.185, "044": 540.746, "045": 542.227, 
    "046": 528.479, "047": 527.477, "048": 526.176, "049": 526.188, "050": 526.117, 
    "051": 524.518, "052": 527.247, "053": 528.463, "054": 528.756, "055": 527.324, 
    "056": 1188.487,"057": 1136.632,"058": 2122.349,"059": 2123.827,"060": 527.245, 
    "061": 527.739, "062": 526.548, "063": 525.686, "064": 522.434, "065": 1185.875, 
    "066": 1183.671,"067": 1191.306,"068": 2643.057,"069": 2649.717,"070": 2636.396, 
    "071": 1483.561,"072": 1488.437,"073": 1490.362,"074": 1480.819,"075": 1495.382, 
    "076": 2645.81, "077": 2632.868,"078": 2630.297,"079": 2647.475,"080": 579.255, 
    "081": 566.202, "082": 578.837, "083": 564.322, "084": 583.532, "085": 569.659, 
    "086": 578.323, "087": 568.077, "088": 566.443, "089": 578.54,  "090": 587.064, 
    "091": 580.274, "092": 583.271, "093": 579.69,  "094": 580.349, "095": 583.86, 
    "096": 582.703, "097": 581.385, "098": 582.418, "099": 581.144, "100": 582.187, 
    "101": 583.819, "102": 584.803, "103": 570.481, "104": 580.639, "105": 577.646, 
    "106": 579.205, "107": 583.335, "108": 581.425, "109": 577.899, "110": 581.558, 
    "111": 578.115, "112": 1167.226,"113": 1178.644,"114": 1184.071,"115": 1180.926,
    "116": 1168.353,"117": 1147.341,"118": 577.367, "119": 1180.058,"120": 1185.756,
    "121": 1186.214,"122": 1186.515,"123": 1185.956,"124": 1191.284,"125": 1175.939,
    "126": 4136.656,"127": 4128.681,"128": 2993.668,"129": 1478.984,"130": 1479.225,
    "131": 1472.527,"132": 2593.355,"133": 2587.532,"134": 2596.17, "135": 3137.18, 
    "136": 1621.501,"137": 1611.726,"138": 1609.112,"139": 1613.309,"140": 3146.776,
    "141": 521.833, "142": 522.585, "143": 820.545, "144": 801.728, "145": 819.384, 
    "146": 813.946, "147": 819.602, "148": 820.454, "149": 818.544, "150": 525.526, 
    "151": 525.847, "152": 510.06,  "153": 573.01,  "154": 655.602, "155": 580.811, 
    "156": 582.711, "157": 582.714, "158": 657.378, "159": 572.065, "160": 661.797, 
    "161": 661.366, "162": 662.567, "163": 662.107, "164": 2592.668,"165": 2575.208,
    "166": 2585.051,"167": 2580.359,"168": 791.414, "169": 2571.594,"170": 2604.542,
    "171": 2585.171,"172": 2577.996,"173": 2574.269,"174": 790.722, "175": 2596.882,
    "176": 2593.97, "177": 2553.061,"178": 2572.033,"179": 2592.381,"180": 792.914, 
    "181": 2603.373,"182": 2610.79, "183": 2612.105,"184": 1750,    "185": 2582.589,
    "186": 521.891, "187": 2601.41, "188": 2576.718,"189": 2608.206,"190": 2600.912,
    "191": 2615.307,"192": 2604.075,"193": 2603.129,"194": 2579.044,"195": 2589.959,
    "196": 523.443, "197": 2615.873,"198": 2615.074,"199": 2613.543,"200": 2621.85, 
    "201": 2886.254,"202": 2947.046,"203": 2940.117,"301": 8326.391,"302": 8312.304,
    "303": 8338.008,"304": 2602.301,"305": 4056.633,"306": 4901.019,"307": 4909.636,
    "308": 4920.855,"309": 2597.913,"310": 4921.899,"311": 2581.794,"312": 4047.328,
    "313": 2584.728,"314": 4047.136,"315": 4046.604,"316": 817.511
}

# --- SESSION STATE İNİTALİZASYONU ---
if 'previous_tanks' not in st.session_state:
    st.session_state.previous_tanks = []
if 'tank_placeholders' not in st.session_state:
    st.session_state.tank_placeholders = {}
if 'last_known_data' not in st.session_state:
    st.session_state.last_known_data = {}

# --- FIREBASE BAĞLANTISI ---
@st.cache_resource
def init_firebase():
    """Firebase bağlantısını kurar."""
    try:
        cred_dict = st.secrets["firebase_credentials"]
        db_url = "https://gemi-izleme-default-rtdb.europe-west1.firebasedatabase.app"
        
        with open("temp_credentials.json", "w") as f:
            json.dump(dict(cred_dict), f)
            
        if not firebase_admin._apps:
            cred = credentials.Certificate("temp_credentials.json")
            firebase_admin.initialize_app(cred, {'databaseURL': db_url})
            
        return db.reference('live_tanks')

    except Exception as e:
        st.error(f"Firebase bağlantısı kurulamadı. Hata: {e}")
        return None

# --- VERİ ÇEKME FONKSİYONU ---
def get_fresh_data_from_firebase():
    """Firebase'den fresh data çeker ve last_known_data'yı günceller"""
    ref = init_firebase()
    if ref is None:
        return st.session_state.last_known_data
    
    try:
        current_data = ref.get() or {}
        
        # Eğer veri geldi ise last_known_data'yı güncelle
        if current_data:
            st.session_state.last_known_data = current_data
            
        return current_data or st.session_state.last_known_data
        
    except Exception as e:
        st.warning(f"Veri çekilirken hata oluştu: {e}")
        # Hata durumunda son bilinen veriyi kullan
        return st.session_state.last_known_data

# Tank listesini almak için fonksiyon
@st.cache_data(ttl=30)
def get_available_tanks():
    """Mevcut tankların listesini döner"""
    data = get_fresh_data_from_firebase()
    if not data:
        return []
        
    sorted_tanks = sorted(
        data.keys(),
        key=lambda k: data[k].get('updated_at', '1970-01-01T00:00:00.000Z'),
        reverse=True
    )
    return sorted_tanks

# --- TANK KARTI ÇIZME FONKSİYONU ---
def render_tank_card(tank_no, data, placeholder):
    """Tek bir tank kartını çizer"""
    product_name = data.get('product', 'Bilinmiyor')
    gov = data.get('gov', 0)
    rate = data.get('rate', 0)
    vem = VEM_DATA.get(tank_no, 0)
    
    kalan_hacim = max(0, vem - gov)
    progress_yuzde = (gov / vem) * 100 if vem > 0 else 0
    
    # Kalan süre hesaplama
    if rate > 0 and vem > gov:
        kalan_saat = (vem - gov) / rate
        utc_plus_3 = timezone(timedelta(hours=3))
        now_utc_plus_3 = datetime.now(utc_plus_3)
        bitis_zamani = now_utc_plus_3 + timedelta(hours=kalan_saat)
        tahmini_bitis_str = bitis_zamani.strftime('%H:%M')
        
        kalan_saat_int = int(kalan_saat)
        kalan_dakika_int = int((kalan_saat * 60) % 60)
        kalan_sure_str = f"{kalan_saat_int} sa {kalan_dakika_int} dk"
    else:
        tahmini_bitis_str = "Hesaplanamadı"
        kalan_sure_str = "N/A"

    # Placeholder içeriğini güncelle
    with placeholder.container(border=True):
        # Kart başlığı ve metrikleri
        col1, col2, col3, col4 = st.columns(4)
        
        title = f"T{tank_no}"
        if product_name != 'Bilinmiyor':
            title += f" / {product_name}"
        
        with col1:
            st.markdown(f"<h3>{title}</h3>", unsafe_allow_html=True)
        
        with col2:
            st.metric(label="Tahmini Bitiş Saati", value=tahmini_bitis_str)
        
        with col3:
            st.metric(label="Kalan Süre", value=kalan_sure_str)
        
        with col4:
            st.metric(label="Rate (m³/h)", value=f"{rate:.3f}")

        # Progress bar ve detaylar
        p_col, d_col = st.columns([2, 1])
        
        with p_col:
            progress_val = min(int(progress_yuzde), 100)
            st.progress(progress_val, text=f"{progress_yuzde:.2f}%")
        
        with d_col:
            detail_html = f"""
            <div style='font-size: 1.1rem; text-align: center;'>
                <b>Vem:</b> {vem:,.3f} m³ | <b>GOV:</b> {gov:,.3f} m³ | <b>Kalan:</b> {kalan_hacim:,.3f} m³
            </div>
            """.replace(",", "X").replace(".", ",").replace("X", ".")
            st.markdown(detail_html, unsafe_allow_html=True)

# --- STREAMLIT ARAYÜZÜ ---
st.title("🚢 Gemi Operasyonları Canlı Takip Paneli")

# Tank seçimi
available_tanks = get_available_tanks()
selected_tanks = st.multiselect(
    "İzlemek istediğiniz tankları seçiniz:",
    options=available_tanks,
    default=[]
)

# Durum mesajları için placeholder
status_placeholder = st.empty()

# Ana konteyner
main_container = st.container()

# Her 3 saniyede bir fresh data çek ve kartları güncelle
@st.cache_data(ttl=3)  # 3 saniyede bir yenile
def get_cached_operations_data():
    """Her 3 saniyede bir Firebase'den fresh data çeker"""
    return get_fresh_data_from_firebase()

# Güncel veriyi al
all_tanks_data = get_cached_operations_data()

# Durum mesajı güncelle
with status_placeholder:
    ref = init_firebase()
    if not ref:
        st.error("Firebase bağlantısı kurulamadı. Lütfen Streamlit Cloud 'Secrets' ayarlarını kontrol edin.")
    elif not all_tanks_data:
        st.warning("Veri bekleniyor... Tarayıcıda Bookmarklet'in çalıştığından emin olun.")
    elif not selected_tanks:
        st.info("Lütfen yukarıdan izlemek istediğiniz bir veya daha fazla tank seçin.")
    else:
        utc_plus_3 = timezone(timedelta(hours=3))
        current_time_str = datetime.now(utc_plus_3).strftime('%H:%M:%S')
        st.success(f"{len(selected_tanks)} adet tank izleniyor. (Son Güncelleme: {current_time_str})")

# Placeholder yönetimi - Seçimden kaldırılanları temizle
current_selection_set = set(selected_tanks)
previous_selection_set = set(st.session_state.previous_tanks)

# Kaldırılan tankların placeholder'larını temizle
for tank_no in previous_selection_set - current_selection_set:
    if tank_no in st.session_state.tank_placeholders:
        st.session_state.tank_placeholders[tank_no].empty()
        del st.session_state.tank_placeholders[tank_no]

# Yeni eklenen tanklar için placeholder oluştur
for tank_no in current_selection_set - previous_selection_set:
    if tank_no not in st.session_state.tank_placeholders:
        with main_container:
            st.session_state.tank_placeholders[tank_no] = st.empty()

# Seçimi kaydet
st.session_state.previous_tanks = selected_tanks.copy()

# Tank kartlarını render et
if selected_tanks and all_tanks_data:
    # Kalan saate göre sıralama için liste oluştur
    display_list = []
    
    for tank_no in selected_tanks:
        data = all_tanks_data.get(tank_no, {})
        gov = data.get('gov', 0)
        rate = data.get('rate', 0)
        vem = VEM_DATA.get(tank_no, 0)
        
        if rate > 0 and vem > gov:
            kalan_saat = (vem - gov) / rate
        else:
            kalan_saat = float('inf')
            
        display_list.append({
            'tank_no': tank_no,
            'data': data,
            'kalan_saat': kalan_saat
        })
    
    # Kalan saate göre sırala (acil olanlar önce)
    display_list.sort(key=lambda x: x['kalan_saat'])
    
    # Her tank için kartı render et
    for item in display_list:
        tank_no = item['tank_no']
        data = item['data']
        
        if tank_no in st.session_state.tank_placeholders:
            render_tank_card(tank_no, data, st.session_state.tank_placeholders[tank_no])

# Otomatik yenileme için JavaScript
st.markdown("""
<script>
setTimeout(function(){
    window.location.reload();
}, 3000); // 3 saniyede bir yenile
</script>
""", unsafe_allow_html=True)