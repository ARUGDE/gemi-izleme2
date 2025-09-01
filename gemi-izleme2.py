import streamlit as st
from datetime import datetime, timedelta, timezone
import firebase_admin
from firebase_admin import credentials, db
import json
from typing import Dict, List, Optional

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Gemi Operasyon Takibi", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------------------------------------------------------
# CONFIGURATION: TANKS TO MONITOR
# -------------------------------------------------------------------
# Update this list to change which tanks are monitored
TANKS_TO_MONITOR = ['072', '312', '314']
# -------------------------------------------------------------------

# --- STATIC DATA (VEM_DATA) ---
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

# --- HELPER FUNCTIONS ---
@st.cache_resource
def init_firebase():
    """Initialize Firebase connection with caching."""
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
        st.error(f"Firebase connection failed: {e}")
        return None

@st.cache_data(ttl=3)  # Cache for 3 seconds
def get_live_data(_ref) -> Dict:
    """Fetch live data from Firebase with caching."""
    if _ref is None:
        return {}
    
    try:
        data = _ref.get()
        return data or {}
    except Exception as e:
        st.warning(f"Error fetching data: {e}")
        return {}

def calculate_tank_metrics(tank_no: str, data: Dict) -> Dict:
    """Calculate all metrics for a single tank."""
    gov = data.get('gov', 0)
    rate = data.get('rate', 0)
    vem = VEM_DATA.get(tank_no, 0)
    product_name = data.get('product', 'Bilinmiyor')
    
    # Calculate remaining volume and progress
    kalan_hacim = max(vem - gov, 0)
    progress_yuzde = (gov / vem) * 100 if vem > 0 else 0
    
    # Calculate remaining time
    kalan_saat = float('inf')
    if rate > 0 and vem > gov:
        kalan_saat = (vem - gov) / rate
    
    # Calculate estimated completion time
    timezone_tr = timezone(timedelta(hours=3))
    tahmini_bitis_str = "Hesaplanamadı"
    kalan_sure_str = "N/A"
    is_critical = False  # For blinking red warning
    
    if kalan_saat != float('inf'):
        now_tr = datetime.now(timezone_tr)
        bitis_zamani = now_tr + timedelta(hours=kalan_saat)
        tahmini_bitis_str = bitis_zamani.strftime('%H:%M')
        
        kalan_saat_int = int(kalan_saat)
        kalan_dakika_int = int((kalan_saat * 60) % 60)
        kalan_sure_str = f"{kalan_saat_int} sa {kalan_dakika_int} dk"
        
        # Check if less than 15 minutes remaining (0.25 hours)
        is_critical = kalan_saat <= 0.25
    
    return {
        'tank_no': tank_no,
        'product_name': product_name,
        'gov': gov,
        'rate': rate,
        'vem': vem,
        'kalan_hacim': kalan_hacim,
        'progress_yuzde': progress_yuzde,
        'kalan_saat': kalan_saat,
        'tahmini_bitis_str': tahmini_bitis_str,
        'kalan_sure_str': kalan_sure_str,
        'is_critical': is_critical
    }

def get_blinking_style(is_critical: bool) -> str:
    """Return CSS style for blinking red effect when critical."""
    if is_critical:
        return """
        <style>
        @keyframes blink {
            0% { background-color: #ff4444; color: white; }
            50% { background-color: #ff8888; color: white; }
            100% { background-color: #ff4444; color: white; }
        }
        .critical-time {
            animation: blink 1s infinite;
            padding: 5px;
            border-radius: 5px;
            font-weight: bold;
        }
        </style>
        """
    return ""

def render_tank_card(metrics: Dict, container_key: str) -> None:
    """Render a single tank monitoring card with unique container."""
    
    # Add blinking CSS if critical
    if metrics['is_critical']:
        st.markdown(get_blinking_style(True), unsafe_allow_html=True)
    
    with st.container(border=True, key=f"tank_{container_key}"):
        # Header
        col1, col2, col3, col4 = st.columns(4)
        
        title = f"T{metrics['tank_no']}"
        if metrics['product_name'] != 'Bilinmiyor':
            title += f" / {metrics['product_name']}"
        
        col1.markdown(f"<h3>{title}</h3>", unsafe_allow_html=True)
        col2.metric("Tahmini Bitiş Saati", metrics['tahmini_bitis_str'])
        
        # Apply critical styling to remaining time if needed
        if metrics['is_critical'] and metrics['kalan_sure_str'] != "N/A":
            col3.markdown(
                f"<div class='critical-time'>⚠️ {metrics['kalan_sure_str']}</div>", 
                unsafe_allow_html=True
            )
        else:
            col3.metric("Kalan Süre", metrics['kalan_sure_str'])
        
        col4.metric("Rate (m³/h)", f"{metrics['rate']:.3f}")
        
        # Progress bar and details
        p_col, d_col = st.columns([2, 1])
        
        progress_val = min(int(metrics['progress_yuzde']), 100)
        p_col.progress(progress_val, text=f"{metrics['progress_yuzde']:.2f}%")
        
        # Format numbers with Turkish locale style
        vem_str = f"{metrics['vem']:,.3f}".replace(",", "X").replace(".", ",").replace("X", ".")
        gov_str = f"{metrics['gov']:,.3f}".replace(",", "X").replace(".", ",").replace("X", ".")
        kalan_str = f"{metrics['kalan_hacim']:,.3f}".replace(",", "X").replace(".", ",").replace("X", ".")
        
        detail_html = f"""
        <div style='font-size: 1.1rem; text-align: center;'>
            <b>Vem:</b> {vem_str} m³ | 
            <b>GOV:</b> {gov_str} m³ | 
            <b>Kalan:</b> {kalan_str} m³
        </div>
        """
        d_col.markdown(detail_html, unsafe_allow_html=True)

def render_sidebar(all_tanks_data: Dict) -> None:
    """Render sidebar with summary information."""
    with st.sidebar:
        st.header("📊 Özet Bilgiler")
        
        # Connection status
        if not all_tanks_data:
            st.error("Veri yok")
        else:
            st.success(f"✅ {len(all_tanks_data)} tank verisi")
        
        # Tank summary
        st.subheader("İzlenen Tanklar")
        for tank_no in TANKS_TO_MONITOR:
            if tank_no in all_tanks_data:
                data = all_tanks_data[tank_no]
                rate = data.get('rate', 0)
                status = "🟢" if rate > 0 else "🟡"
                st.write(f"{status} Tank {tank_no}")
            else:
                st.write(f"🔴 Tank {tank_no}")
        
        # Auto-refresh info
        st.divider()
        st.info("🔄 Otomatik yenileme: 3 saniye")

# --- MAIN APPLICATION ---
def main():
    st.title("🚢 Gemi Operasyonları Canlı Takip Paneli")
    
    # Initialize Firebase
    ref = init_firebase()
    
    # Status placeholder
    status_placeholder = st.empty()
    
    # Fetch data
    all_tanks_data = get_live_data(ref)
    
    # Update status
    if not ref:
        status_placeholder.error(
            "Firebase bağlantısı kurulamadı. "
            "Lütfen Streamlit Cloud 'Secrets' ayarlarını kontrol edin."
        )
    elif not all_tanks_data:
        status_placeholder.warning(
            "Veri bekleniyor... Lokaldeki 'itici.py' script'inin "
            "çalıştığından emin olun."
        )
    else:
        timezone_tr = timezone(timedelta(hours=3))
        current_time = datetime.now(timezone_tr).strftime('%H:%M:%S')
        status_placeholder.success(
            f"{len(TANKS_TO_MONITOR)} adet tank izleniyor. "
            f"(Son Güncelleme: {current_time})"
        )
    
    # Render sidebar
    render_sidebar(all_tanks_data)
    
    # Calculate metrics for all tanks
    tank_metrics = []
    for tank_no in TANKS_TO_MONITOR:
        data = all_tanks_data.get(tank_no, {})
        metrics = calculate_tank_metrics(tank_no, data)
        tank_metrics.append(metrics)
    
    # Sort by remaining time (lowest first - kritik olanlar önce)
    tank_metrics.sort(key=lambda x: x['kalan_saat'])
    
    # Summary statistics
    if tank_metrics:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            active_tanks = sum(1 for m in tank_metrics if m['rate'] > 0)
            st.metric("Aktif Tanklar", active_tanks)
        
        with col2:
            total_remaining = sum(m['kalan_hacim'] for m in tank_metrics)
            st.metric("Toplam Kalan", f"{total_remaining:,.1f} m³")
        
        with col3:
            critical_tanks = sum(1 for m in tank_metrics if m['is_critical'])
            if critical_tanks > 0:
                st.markdown(
                    f"<div style='background-color: #ff4444; color: white; padding: 10px; "
                    f"border-radius: 5px; text-align: center; font-weight: bold;'>"
                    f"⚠️ KRİTİK: {critical_tanks} TANK</div>", 
                    unsafe_allow_html=True
                )
            else:
                avg_rate = sum(m['rate'] for m in tank_metrics) / len(tank_metrics) if tank_metrics else 0
                st.metric("Ortalama Rate", f"{avg_rate:.3f} m³/h")
    
    st.divider()
    
    # Render tank cards (sorted by remaining time)
    for i, metrics in enumerate(tank_metrics):
        render_tank_card(metrics, f"{metrics['tank_no']}_{i}")
    
    # Auto-refresh using rerun
    import time
    time.sleep(3)
    st.rerun()

if __name__ == "__main__":
    main()