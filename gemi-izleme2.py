import streamlit as st
from datetime import datetime, timedelta, timezone
import firebase_admin
from firebase_admin import credentials, db
from twilio.rest import Client
import json
from typing import Dict, List, Optional, Any
import time

# --- SAYFA YAPILANDIRMASI ---
st.set_page_config(
    page_title="Gemi İzleme",
    layout="wide",
    initial_sidebar_state="collapsed" # Kenar çubuğu varsayılan olarak kapalı
)

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

# --- YENİ FONKSİYON: ŞİFRE KONTROLÜ ---
def check_password():
    """Kullanıcı girişi için bir form gösterir ve şifreyi doğrular."""
    if st.session_state.get("password_correct", False):
        return True

    with st.form("password_form"):
        password = st.text_input("Uygulamayı Görüntülemek İçin Şifre Girin", type="password")
        submitted = st.form_submit_button("Giriş Yap")

        if submitted:
            correct_password = st.secrets.get("APP_PASSWORD", "")
            
            if password == correct_password:
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("Girdiğiniz şifre hatalı.")
    
    return False

# --- TANK SEÇİMİ VE HEDEF HACİM İÇİN FİREBASE İŞLEMLERİ ---
@st.cache_data(ttl=10)
def get_selected_tanks(_config_ref: Any) -> List[str]:
    """Firebase'den seçili tank listesini çeker."""
    if _config_ref is None: return []
    try:
        selected = _config_ref.child('selected_tanks').get()
        return selected if isinstance(selected, list) and selected else []
    except Exception:
        return []

def save_selected_tanks(config_ref: Any, tanks: List[str]):
    """Seçili tank listesini Firebase'e kaydeder."""
    if config_ref is None: return
    try:
        config_ref.child('selected_tanks').set(tanks)
    except Exception as e:
        st.error(f"Tank seçimleri kaydedilemedi: {e}")

# YENİ -> Hedef Hacim verilerini çekmek için
@st.cache_data(ttl=10)
def get_all_target_volumes(_config_ref: Any) -> Dict[str, float]:
    """Firebase'den tüm tanklar için girilmiş hedef hacimlerini çeker."""
    if _config_ref is None: return {}
    try:
        volumes = _config_ref.child('target_volumes').get()
        return volumes or {}
    except Exception:
        return {}

# YENİ -> Hedef Hacim verisini kaydetmek/güncellemek için
def save_target_volume(config_ref: Any, tank_no: str):
    """Bir tank için girilen hedef hacmi anında Firebase'e kaydeder."""
    if config_ref is None: return
    widget_key = f"target_vem_{tank_no}"
    new_value = st.session_state.get(widget_key, 0.0)
    try:
        # Eğer kullanıcı değeri silerse (0 yaparsa), kaydı veritabanından kaldır
        if new_value > 0:
            config_ref.child('target_volumes').child(tank_no).set(new_value)
        else:
            # 0 veya daha küçükse, bu hedefi iptal et ve kaydı sil
            config_ref.child('target_volumes').child(tank_no).delete()
        
        # Diğer kullanıcıların anında görmesi için cache'i temizle
        st.cache_data.clear()
    except Exception as e:
        st.error(f"Hedef hacim kaydedilemedi: {e}")

# YENİ -> İzlemeden çıkarılan tankın hedef hacim verisini silmek için
def delete_target_volume(config_ref: Any, tank_no: str):
    """Bir tank için girilmiş hedef hacim verisini Firebase'den siler."""
    if config_ref is None: return
    try:
        config_ref.child('target_volumes').child(tank_no).delete()
    except Exception as e:
        st.warning(f"Eski hedef hacim verisi silinemedi: {e}")


# --- YARDIMCI FONKSİYONLAR ---
@st.cache_resource
def init_firebase() -> tuple:
    """Firebase bağlantısını önbelleğe alarak başlatır."""
    try:
        cred_dict = st.secrets["firebase_credentials"]
        db_url = st.secrets["db_url"]
        cred = credentials.Certificate(dict(cred_dict))
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred, {'databaseURL': db_url})
        return db.reference('live_tanks'), db.reference('config')
    except Exception as e:
        st.error(f"Firebase bağlantısı başarısız oldu: {e}")
        return None, None

@st.cache_resource
def init_twilio_client():
    """Twilio client'ını önbelleğe alarak başlatır."""
    try:
        account_sid = st.secrets.get("TWILIO_ACCOUNT_SID", "AC450a44faf3362fa799069d4c791c135f")
        auth_token = st.secrets.get("TWILIO_AUTH_TOKEN", "")
        if not auth_token:
            st.warning("Twilio Auth Token secrets'te bulunamadı. WhatsApp bildirimleri çalışmayacak.")
            return None
        return Client(account_sid, auth_token)
    except Exception as e:
        st.error(f"Twilio bağlantısı başarısız oldu: {e}")
        return None

@st.cache_data(ttl=10)
def get_live_data(_ref: Any) -> Dict:
    """Firebase'den canlı veriyi önbelleğe alarak çeker."""
    if _ref is None: return {}
    try:
        data = _ref.get()
        return data or {}
    except Exception as e:
        st.warning(f"Veri alınırken hata oluştu: {e}")
        return {}

# GÜNCELLENDİ -> `target_vem` parametresi eklendi
def calculate_tank_metrics(tank_no: str, data: Dict, target_vem: Optional[float] = None) -> Dict:
    """Tek bir tank için tüm metrikleri hesaplar. Öncelik hedef hacimdedir."""
    
    # HESAPLAMA MANTIĞI GÜNCELLENDİ
    # Eğer geçerli bir hedef hacim girilmişse onu kullan, yoksa VEM_DATA'dan al.
    if target_vem and target_vem > 0:
        vem = target_vem
    else:
        vem = VEM_DATA.get(tank_no, 0)

    gov = data.get('gov', 0)
    
    # Statik VEM için HIGH-LEVEL alarm kontrolü (target_vem'i ignore et)
    static_vem = VEM_DATA.get(tank_no, 0)
    is_high_level_alarm = gov >= static_vem if static_vem > 0 else False

    rate = data.get('rate', 0)
    product_name = data.get('product', 'Bilinmiyor')
    kalan_hacim = max(vem - gov, 0)
    progress_yuzde = (gov / vem) * 100 if vem > 0 else 0
    kalan_saat = float('inf')
    if rate > 0 and vem > gov:
        kalan_saat = (vem - gov) / rate
    
    timezone_tr = timezone(timedelta(hours=3))
    tahmini_bitis_str = "n/a"
    kalan_sure_str = "n/a"
    is_critical = False
    
    if kalan_saat != float('inf'):
        now_tr = datetime.now(timezone_tr)
        bitis_zamani = now_tr + timedelta(hours=kalan_saat)
        tahmini_bitis_str = bitis_zamani.strftime('%H:%M')
        kalan_saat_int = int(kalan_saat)
        kalan_dakika_int = int((kalan_saat * 60) % 60)
        kalan_sure_str = f"{kalan_saat_int} sa {kalan_dakika_int} dk"
        is_critical = kalan_saat <= 0.25
    
    return {
        'tank_no': tank_no, 'product_name': product_name, 'gov': gov, 'rate': rate,
        'vem': vem, 'static_vem': static_vem, 'kalan_hacim': kalan_hacim,
        'progress_yuzde': progress_yuzde, 'kalan_saat': kalan_saat,
        'tahmini_bitis_str': tahmini_bitis_str, 'kalan_sure_str': kalan_sure_str,
        'is_critical': is_critical, 'is_high_level_alarm': is_high_level_alarm
    }

def get_blinking_style(is_critical: bool) -> str:
    """Kritik durumlar için yanıp sönen kırmızı efekti için CSS stili döndürür."""
    if is_critical:
        return """
        <style>
        @keyframes flashing-red {
            0%   { background-color: #ff4b4b; }
            50%  { background-color: #a02c2c; }
            100% { background-color: #ff4b4b; }
        }
        .flash-metric-container {
            border-radius: 0.5rem; padding: 0.75rem;
            animation-name: flashing-red; animation-duration: 1.5s;
            animation-iteration-count: infinite; text-align: left;
            border: 1px solid transparent; 
        }
        .flash-metric-container .metric-label {
            font-size: 0.875rem; color: rgba(255, 255, 255, 0.7);
            font-weight: normal; display: block;
        }
        .flash-metric-container .metric-value {
            font-size: 1.75rem; font-weight: normal;
            color: white; line-height: 1.4; 
        }
        </style>
        """
    return ""

# GÜNCELLENDİ -> Hedef hacim girişi için `config_ref` ve `target_vem` parametreleri eklendi
def render_tank_card(metrics: Dict, container_key: str, config_ref: Any, target_vem: Optional[float]) -> None:
    """Tek bir tank izleme kartını oluşturur."""
    if metrics['is_critical']:
        st.markdown(get_blinking_style(True), unsafe_allow_html=True)

    with st.container(border=True, key=f"tank_{container_key}"):
        col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

        # col1 içinde mini-sütun: başlık + hedef hacim yan yana
        with col1:
            sub_c1, sub_c2 = st.columns([1, 1.5])
            with sub_c1:
                st.markdown(f"<h2 style='margin:0; pointer-events: none; cursor: default;'>T{metrics['tank_no']}</h2>",
                            unsafe_allow_html=True)
            with sub_c2:
                st.number_input(
                    label="Hedef Hacim (Opsiyonel)",
                    value=target_vem if target_vem is not None else 0.0,
                    min_value=0.0,
                    format="%.3f",
                    key=f"target_vem_{metrics['tank_no']}",
                    on_change=save_target_volume,
                    args=(config_ref, metrics['tank_no']),
                    # label_visibility="collapsed"
                )

        col2.metric("Tahmini Bitiş Saati", metrics['tahmini_bitis_str'])

        if metrics['is_critical'] and metrics['kalan_sure_str'] != "N/A":
            col3.markdown(f"""
                <div class='flash-metric-container'>
                    <div class='metric-label'>Kalan Süre</div>
                    <div class='metric-value'>{metrics['kalan_sure_str']}</div>
                </div>""", unsafe_allow_html=True)
        else:
            col3.metric("Kalan Süre", metrics['kalan_sure_str'])

        col4.metric("Rate (m³/h)", f"{metrics['rate']:.3f}")
        
        p_col, d_col = st.columns([2, 1])
        percentage = metrics['progress_yuzde']
        color = "#198754"
        if percentage >= 90: color = "#dc3545"
        elif percentage >= 75: color = "#ffc107"
        
        bar_width_percentage = min(percentage, 100)
        bar_style = (f"width: {bar_width_percentage}%; background-color: {color}; height: 24px; border-radius: 5px; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold;")
        container_style = "width: 100%; background-color: #e9ecef; border-radius: 5px;"
        html_code = (f'<div style="{container_style}"><div style="{bar_style}">{percentage:.1f}%</div></div>')
        p_col.markdown(html_code, unsafe_allow_html=True)
        
        # Kullanılan hacmin hedef mi yoksa VEM mi olduğunu belirtmek için başlık güncellendi
        vem_title = "Hedef" if target_vem and target_vem > 0 else "Vem"
        vem_str = f"{metrics['vem']:,.3f}".replace(",", "X").replace(".", ",").replace("X", ".")
        gov_str = f"{metrics['gov']:,.3f}".replace(",", "X").replace(".", ",").replace("X", ".")
        kalan_str = f"{metrics['kalan_hacim']:,.3f}".replace(",", "X").replace(".", ",").replace("X", ".")
        
        detail_html = f"""
        <div style='font-size: 1.1rem; text-align: center;'>
            <b>{vem_title}:</b> {vem_str} m³ | <b>GOV:</b> {gov_str} m³ | <b>Kalan:</b> {kalan_str} m³
        </div>"""
        d_col.markdown(detail_html, unsafe_allow_html=True)

# --- HIGH-LEVEL ALARM FONKSİYONU ---
def send_high_level_alert(client: Client, metrics: Dict):
    """HIGH-LEVEL alarm için Twilio WhatsApp mesajı gönderir."""
    if client is None:
        st.warning("Twilio client mevcut değil. Mesaj gönderilemedi.")
        return
    
    try:
        # Secrets'ten değerleri al
        to_number = st.secrets.get("TWILIO_TO_NUMBER", "whatsapp:+905432601887")
        from_number = "whatsapp:+14155238886"
        
        # Düz metin mesaj oluştur
        tank_no = metrics['tank_no']
        rate = metrics['rate']
        gov = metrics['gov']
        message_body = f"HL ⚠️ T{tank_no} - Rate: {rate} - GOV: {gov}"
        
        message = client.messages.create(
            from_=from_number,
            body=message_body,
            to=to_number
        )
        
        return message.sid
        
    except Exception as e:
        return None

# --- SESLİ ALARM FONKSİYONU ---
def play_high_level_audio_alert():
    """HIGH-LEVEL alarm için 9 saniyelik sesli uyarı çalar."""
    from streamlit.components.v1 import html
    
    js_code = """
    <script>
    function playAlarmSound() {
        // AudioContext oluştur (user gesture gerekebilir)
        if (!window.audioCtx) {
            window.audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        }
        const audioCtx = window.audioCtx;
        let currentTime = audioCtx.currentTime;

        // Yardımcı fonksiyon (DIT bip sesi)
        function playBip(start, freq=800, duration=0.07) {
            const oscillator = audioCtx.createOscillator();
            const gainNode = audioCtx.createGain();

            oscillator.type = 'square'; // EKG benzeri kare dalga
            oscillator.frequency.setValueAtTime(freq, currentTime + start);

            gainNode.gain.setValueAtTime(0, currentTime + start);
            gainNode.gain.linearRampToValueAtTime(1, currentTime + start + 0.005);
            gainNode.gain.linearRampToValueAtTime(0, currentTime + start + duration);

            oscillator.connect(gainNode);
            gainNode.connect(audioCtx.destination);

            oscillator.start(currentTime + start);
            oscillator.stop(currentTime + start + duration + 0.05);
        }

        // 2. Periyot: DIT DIT (boşluk) DIT DIT (boşluk) pattern (0 - 9 sn)
        // Her çift 0.6 sn (0.07 bip + 0.23 boşluk), 0.7 sn aralıklarla
        playBip(1.0);
        playBip(1.3);
        playBip(2.0);
        playBip(2.3);
        playBip(3.0);
        playBip(3.3);
        playBip(4.0);
        playBip(4.3);
        playBip(5.0);
        playBip(5.3);
        playBip(6.0);
        playBip(6.3);
        playBip(7.0);
        playBip(7.3);
        playBip(8.0);
        playBip(8.3);

        // Temizlik
        setTimeout(() => {
            try {
                if (audioCtx.state === 'running') {
                    audioCtx.close();
                }
            } catch(e) {}
        }, 9000);
    }

    // Alarmı tetikle
    playAlarmSound();
    </script>
    """
    
    html(js_code, height=0)

# --- SESLİ ALARM TETIKLEYICI ---
def trigger_audio_alert_if_needed(tank_no: str):
    """Sesli alarmı tetikler (tank bazlı 10 saat cooldown ile)."""
    now = datetime.now()
    
    # Tank bazlı session state
    if 'high_level_audio_alerts' not in st.session_state:
        st.session_state['high_level_audio_alerts'] = {}
    
    last_alert_time = st.session_state['high_level_audio_alerts'].get(tank_no)
    
    # İlk tetikleme veya 10 saat geçtiyse
    if last_alert_time is None or (now - last_alert_time).total_seconds() >= 36000:  # 10 saat
        play_high_level_audio_alert()
        st.session_state['high_level_audio_alerts'][tank_no] = now
        return True
    else:
        return False

# --- ANA UYGULAMA ---
def main():
    ref, config_ref = init_firebase()
    twilio_client = init_twilio_client()
    
    # Session state için HIGH-LEVEL alarm takibi (spam önleme)
    if 'high_level_alerts' not in st.session_state:
        st.session_state['high_level_alerts'] = {}
    
    tank_selection_col, status_col1, status_col2 = st.columns([3, 3, 2])
    
    available_tanks = sorted(VEM_DATA.keys(), key=lambda x: int(x))
    current_selected_tanks = get_selected_tanks(config_ref)
    
    with tank_selection_col:
        selected_tanks = st.multiselect(
            "",
            options=available_tanks,
            default=current_selected_tanks,
            key="tank_selector",
            placeholder="İzlenecek tanklar:",
            label_visibility="collapsed"
        )
        
        # GÜNCELLENDİ -> Tank kaldırıldığında hedef hacim verisini silme mantığı eklendi
        if selected_tanks != current_selected_tanks:
            # Hangi tankların kaldırıldığını bul
            removed_tanks = set(current_selected_tanks) - set(selected_tanks)
            for tank_no in removed_tanks:
                delete_target_volume(config_ref, tank_no)

            save_selected_tanks(config_ref, selected_tanks)
            st.cache_data.clear()
            st.rerun()
    
    TANKS_TO_MONITOR = selected_tanks if selected_tanks else current_selected_tanks
    
    all_tanks_data = get_live_data(ref)
    # YENİ -> Tüm hedef hacim verileri en başta çekilir
    all_target_volumes = get_all_target_volumes(config_ref)

    # Timestamp kontrolü... (Değişiklik yok)
    is_data_stale = False
    last_update_str = "Bilinmiyor"
    if all_tanks_data and isinstance(all_tanks_data, dict):
        try:
            timestamps = []
            for tank_no, tank_data in all_tanks_data.items():
                if isinstance(tank_data, dict) and 'updated_at' in tank_data:
                    try:
                        timestamp_str = tank_data['updated_at']
                        if timestamp_str.endswith('Z'):
                            last_update_utc = datetime.fromisoformat(timestamp_str[:-1] + '+00:00')
                        else:
                            last_update_utc = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                        timestamps.append(last_update_utc)
                    except:
                        continue
            
            if timestamps:
                most_recent = max(timestamps)
                now_utc = datetime.now(timezone.utc)
                time_diff = (now_utc - most_recent).total_seconds()
                
                if time_diff > 15:
                    is_data_stale = True
                
                timezone_tr = timezone(timedelta(hours=3))
                last_update_tr = most_recent.astimezone(timezone_tr)
                last_update_str = last_update_tr.strftime('%H:%M:%S')
                
        except Exception:
            is_data_stale = False

    timezone_tr = timezone(timedelta(hours=3))
    current_time_str = datetime.now(timezone_tr).strftime('%H:%M:%S')

    if not ref:
        status_col1.error("Firebase bağlantısı kurulamadı. Lütfen Streamlit Cloud 'Secrets' ayarlarını kontrol edin.")
    elif not all_tanks_data:
        status_col1.warning("Veri akışı durdu veya bekleniyor...")
    elif is_data_stale:
        status_col1.warning(f"Veri güncellenmemiş olabilir. Son güncelleme: {last_update_str}")
    else:
        if len(TANKS_TO_MONITOR) == 0:
            status_col1.info("İzlenecek tankları seçin. Seçtiğiniz tanklar herkes için geçerli olacaktır!")
        else:
            active_tanks = sum(1 for tank_no in TANKS_TO_MONITOR if tank_no in all_tanks_data)
            status_col1.success(f"{active_tanks}/{len(all_tanks_data)} adet tank izleniyor. Son güncelleme: {current_time_str}")

    if TANKS_TO_MONITOR and all_tanks_data and isinstance(all_tanks_data, dict):
        tank_metrics = []
        for tank_no in TANKS_TO_MONITOR:
            data = all_tanks_data.get(tank_no, {})
            if not data: continue
            
            # YENİ -> İlgili tankın hedef hacmi hesaplama fonksiyonuna gönderilir
            target_vem = all_target_volumes.get(tank_no)
            metrics = calculate_tank_metrics(tank_no, data, target_vem)
            tank_metrics.append(metrics)
        
        tank_metrics.sort(key=lambda x: x['kalan_saat'])
        
        # HIGH-LEVEL ALARM KONTROLÜ (hem WhatsApp hem sesli alarm için)
        now = datetime.now()
        audio_needed = False
        
        for metrics in tank_metrics:
            tank_no = metrics['tank_no']
            rate = metrics['rate']  # Değişkenleri döngü başında tanımla
            gov = metrics['gov']
            if metrics['is_high_level_alarm']:
                # WhatsApp spam önleme: Son 10 saatte gönderilmiş mi?
                last_alert_time = st.session_state['high_level_alerts'].get(tank_no)
                if last_alert_time is None or (now - datetime.fromisoformat(last_alert_time)).total_seconds() > 36000:  # 10 saat
                    alert_sid = send_high_level_alert(twilio_client, metrics)
                    if alert_sid:
                        st.session_state['high_level_alerts'][tank_no] = now.isoformat()
                    else:
                        pass
                else:
                    pass
                
                # Sesli alarm tank bazlı kontrol (WhatsApp'dan bağımsız)
                audio_result = trigger_audio_alert_if_needed(tank_no)
                if audio_result:
                    audio_needed = True
        
        for i, metrics in enumerate(tank_metrics):
            # YENİ -> İlgili tankın hedef hacmi kart oluşturma fonksiyonuna da gönderilir
            target_vem_for_card = all_target_volumes.get(metrics['tank_no'])
            render_tank_card(metrics, f"{metrics['tank_no']}_{i}", config_ref, target_vem_for_card)
        
        # SESLİ ALARM: Tek seferlik html bileşeni (layout bozulmasını önlemek için)
        if audio_needed:
            play_high_level_audio_alert()
    
    countdown_placeholder = status_col2.empty()
    refresh_saniye = 10
    for i in range(refresh_saniye, 0, -1):
        countdown_placeholder.write(f"⏳ Sonraki yenileme: {i} sn...")
        time.sleep(1)
    
    st.rerun()

# --- YENİ ÇALIŞTIRMA MANTIĞI ---
if __name__ == "__main__":
    if check_password():
        main()