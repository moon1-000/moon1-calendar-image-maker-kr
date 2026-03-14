import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageColor
import calendar
from datetime import datetime, date
import io
import os
import holidays
import urllib.request

# --- 폰트 로직 ---
def get_font(font_option, uploaded_font, size, lang, force_bold=False):
    if uploaded_font is not None:
        try: return ImageFont.truetype(io.BytesIO(uploaded_font.getvalue()), size)
        except: pass
    font_urls = {
        "나눔고딕": "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf",
        "나눔고딕_Bold": "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Bold.ttf",
        "바탕체": "https://github.com/google/fonts/raw/main/ofl/nanummyeongjo/NanumMyeongjo-Regular.ttf",
        "바탕체_Bold": "https://github.com/google/fonts/raw/main/ofl/nanummyeongjo/NanumMyeongjo-Bold.ttf"
    }
    key = font_option if font_option != "Arial" and font_option != "맑은 고딕" else "나눔고딕"
    if force_bold: key += "_Bold"
    file_name = f"{key}.ttf"
    if not os.path.exists(file_name):
        try: urllib.request.urlretrieve(font_urls.get(key, font_urls["나눔고딕"]), file_name)
        except: return ImageFont.load_default()
    return ImageFont.truetype(file_name, size)

# --- 컬러 프리셋 로직 (수정됨) ---
def color_selector(label, key, default_val):
    st.write(f"**{label}**")
    presets = {"핑크": "#FFD1DC", "블루": "#ADD8E6", "그린": "#B2FBA5", "옐로우": "#FFF44F", "라벤더": "#E6E6FA", "흰색": "#FFFFFF", "검정": "#000000"}
    
    if key not in st.session_state:
        st.session_state[key] = default_val
        
    cols = st.columns(len(presets))
    for i, (name, hex_v) in enumerate(presets.items()):
        if cols[i].button(name, key=f"btn_{key}_{i}"):
            st.session_state[key] = hex_v
            st.rerun() # 즉시 반영
            
    return st.color_picker(f"{label} 상세", st.session_state[key], key=f"p_{key}")

# --- 생성 함수 ---
def generate_wallpaper(width, height, year, month, pos_ratio, bg_type, bg_color, bg_image, bg_rotate, bg_x, bg_y, bg_zoom, text_color_hex, font_size, x_spacing, y_spacing, lang, font_family, uploaded_font, is_bold, use_holidays, show_box, box_color_hex, box_opacity, box_radius, show_watermark, wm_text, wm_color):
    if bg_type == "이미지 업로드" and bg_image is not None:
        img = Image.open(bg_image).convert("RGBA")
        img = img.rotate(bg_rotate, expand=True)
        # 줌 및 리사이즈
        w_r, h_r = width / img.width, height / img.height
        base_scale = max(w_r, h_r) * bg_zoom
        n_w, n_h = int(img.width * base_scale), int(img.height * base_scale)
        img = img.resize((n_w, n_h), resample=Image.LANCZOS)
        # 위치 이동
        left = int((n_w - width)/2) + int((bg_x / 100) * (n_w - width))
        top = int((n_h - height)/2) + int((bg_y / 100) * (n_h - height))
        img = img.crop((left, top, left + width, top + height))
    else:
        img = Image.new('RGBA', (width, height), color=bg_color)
    
    overlay = Image.new('RGBA', img.size, (0,0,0,0))
    draw = ImageDraw.Draw(overlay)
    cal = calendar.TextCalendar(calendar.SUNDAY)
    wks = cal.monthdayscalendar(year, month)
    kr_h = holidays.KR(years=year) if use_holidays else {}
    
    m_n = f"{month}월" if lang == "한국어" else calendar.month_name[month].upper()
    hds = ["일", "월", "화", "수", "목", "금", "토"] if lang == "한국어" else ["S", "M", "T", "W", "T", "F", "S"]
    
    b_f = get_font(font_family, uploaded_font, int(font_size * 1.5), lang, True)
    r_f = get_font(font_family, uploaded_font, font_size, lang, is_bold)
    t_c, r_c = ImageColor.getrgb(text_color_hex), (220, 20, 60, 255)
    c_w, r_h = font_size * x_spacing, font_size * y_spacing
    cal_w, cal_h = c_w * 7, r_h * (len(wks) + 2.5)
    s_x, s_y = (width - cal_w) / 2, (height * (pos_ratio / 100)) - (cal_h / 2)
    
    if show_box:
        bc = ImageColor.getrgb(box_color_hex)
        draw.rounded_rectangle([s_x - 40, s_y - 40, s_x + cal_w + 40, s_y + cal_h + 40], radius=box_radius, fill=(bc[0], bc[1], bc[2], int(255 * (box_opacity/100))))
    
    draw.text((width/2, s_y + r_h/2), m_n, fill=t_c, font=b_f, anchor="mm")
    h_y = s_y + (r_h * 2)
    for i, h in enumerate(hds):
        draw.text((s_x + (i * c_w) + (c_w/2), h_y), h, fill=r_c if i == 0 else t_c, font=r_f, anchor="mm")
    for ri, wk in enumerate(wks):
        y = h_y + (r_h * (ri + 1))
        for ci, dy in enumerate(wk):
            if dy != 0:
                is_h = date(year, month, dy) in kr_h
                draw.text((s_x + (ci * c_w) + (c_w/2), y), str(dy), fill=r_c if (ci == 0 or is_h) else t_c, font=r_f, anchor="mm")
                
    if show_watermark:
        w_f = get_font(font_family, uploaded_font, 20, lang, True)
        draw.text((width - 30, height - 30), wm_text, fill=wm_color, font=w_f, anchor="rd")
    return Image.alpha_composite(img, overlay).convert("RGB")

# --- UI 레이아웃 ---
st.set_page_config(page_title="달력 배경화면 생성기", layout="wide")
st.markdown("<h1 style='text-align: center;'>📅 달력 배경화면 생성기</h1>", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### 🛠️ 설정 메뉴")
    
    st.info("1️⃣ **기기 규격 설정**")
    cat = st.selectbox("기기 분류", ["스마트폰 (1080x2340)", "태블릿 (2048x2732)", "이북 리더기 (758x1024)", "직접 입력"], index=2)
    res = {"스마트폰 (1080x2340)": (1080, 2340), "태블릿 (2048x2732)": (2048, 2732), "이북 리더기 (758x1024)": (758, 1024)}
    w, h = (st.number_input("가로", value=1080), st.number_input("세로", value=1920)) if cat == "직접 입력" else res[cat]
    
    st.markdown("---")
    st.info("2️⃣ **날짜 및 위치**")
    c1, c2 = st.columns(2)
    year, month = c1.number_input("년", value=2026), c2.number_input("월", 1, 12, 3)
    is_landscape = st.checkbox("🔄 가로로 돌리기", value=False)
    if is_landscape: w, h = h, w
    use_holidays, pos_val = st.checkbox("대한민국 공휴일 반영", value=True), st.slider("세로 위치 (%)", 0, 100, 50)
    
    st.markdown("---")
    st.info("3️⃣ **달력 디자인**")
    lang = st.radio("언어", ["English", "한국어"], horizontal=True)
    font_f = st.selectbox("서체", ["Arial", "맑은 고딕", "바탕체", "나눔고딕"], index=0)
    is_bold = st.checkbox("볼드체 설정", value=False)
    up_font = st.file_uploader("외부 폰트 추가", type=['ttf', 'otf'])
    t_color = color_selector("텍스트 색상", "txt", "#000000")
    f_size = st.slider("글자 크기", 10, 120, 30)
    with st.expander("📏 간격 세부 설정"):
        x_s, y_s = st.slider("가로 간격", 1.0, 5.0, 2.5), st.slider("세로 간격", 1.0, 5.0, 2.0)
    
    st.markdown("---")
    st.info("4️⃣ **배경 설정**")
    bg_type = st.radio("배경 종류", ["단색 컬러", "이미지 업로드"], horizontal=True)
    bg_rotate, bg_x, bg_y, bg_zoom, bg_img, bg_color = 0, 0, 0, 1.0, None, "#FFFFFF"
    if bg_type == "이미지 업로드":
        bg_img = st.file_uploader("이미지 파일 선택", type=['jpg', 'png', 'jpeg'])
        st.write("🖼️ **이미지 조작**")
        bg_zoom = st.slider("확대/축소 (Zoom)", 1.0, 3.0, 1.0, 0.1)
        bg_rotate = st.slider("회전 (도)", 0, 360, 0, 90)
        bg_x, bg_y = st.slider("가로 이동 (%)", -100, 100, 0), st.slider("세로 이동 (%)", -100, 100, 0)
    else: bg_color = color_selector("배경색 선택", "bg", "#FFFFFF")
    
    st.markdown("---")
    show_box = st.checkbox("가독성 박스 추가(이미지 배경 시)", value=False)
    if show_box:
        bx_c = color_selector("바탕 박스 색상", "box", "#FFFFFF")
        bx_o, bx_r = st.slider("바탕 투명도", 0, 100, 75), st.slider("바탕 모서리 곡률", 0, 100, 20)
    else: bx_c, bx_o, bx_r = "#FFFFFF", 75, 20
    
    st.markdown("---")
    st.info("5️⃣ **제작자 출처 표기**")
    show_wm = st.checkbox("표시", value=False)
    wm_text = st.text_input("싫어요 내 이름 적을꺼야", value="Moon1")
    wm_color = st.color_picker("출처 글자 색상", "#000000")
    
    st.markdown("---")
    st.info("6️⃣ **초기화**")
    if st.button("🔄 모든 설정 기본값으로"):
        for key in st.session_state.keys(): del st.session_state[key]
        st.rerun()

    st.caption("🚀 최종 수정: 2026.03.15.03.40")

# 결과 생성
final_img = generate_wallpaper(w, h, year, month, pos_val, bg_type, bg_color, bg_img, bg_rotate, bg_x, bg_y, bg_zoom, t_color, f_size, x_s, y_s, lang, font_f, up_font, is_bold, use_holidays, show_box, bx_c, bx_o, bx_r, show_wm, wm_text, wm_color)
st.image(final_img, width=450)
buf = io.BytesIO()
final_img.save(buf, format="PNG")
st.download_button("📥 이미지 파일로 저장", buf.getvalue(), f"calendar_{year}_{month}.png")
