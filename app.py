import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageColor
import calendar
from datetime import datetime, date
import io
import os
import holidays
import urllib.request

# --- 폰트 및 데이터 로직 ---
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
    key = font_option if font_option not in ["Arial", "맑은 고딕"] else "나눔고딕"
    if force_bold: key += "_Bold"
    file_name = f"{key}.ttf"
    if not os.path.exists(file_name):
        try: urllib.request.urlretrieve(font_urls.get(key, font_urls["나눔고딕"]), file_name)
        except: return ImageFont.load_default()
    return ImageFont.truetype(file_name, size)

def get_calendar_data(year, month, lang, use_holidays):
    cal = calendar.TextCalendar(calendar.SUNDAY)
    weeks = cal.monthdayscalendar(year, month)
    kr_h = holidays.KR(years=year) if use_holidays else {}
    m_n = f"{month}월" if lang == "한국어" else calendar.month_name[month].upper()
    hds = ["일", "월", "화", "수", "목", "금", "토"] if lang == "한국어" else ["S", "M", "T", "W", "T", "F", "S"]
    return m_n, hds, weeks, kr_h

# --- 생성 함수 ---
def generate_wallpaper(width, height, year, month, pos_ratio, bg_type, bg_color, bg_image, bg_rotate, bg_x, bg_y, bg_zoom, text_color_hex, font_size, x_spacing, y_spacing, lang, font_family, uploaded_font, is_bold, use_holidays, show_box, box_color_hex, box_opacity, box_radius, show_moon1, show_custom, custom_text, wm_color):
    base_color = ImageColor.getrgb(bg_color)
    img_canvas = Image.new('RGBA', (width, height), color=base_color)

    if bg_type == "이미지 업로드" and bg_image is not None:
        try:
            src_img = Image.open(bg_image).convert("RGBA")
            src_img = src_img.rotate(bg_rotate, expand=True, resample=Image.BICUBIC)
            w_r, h_r = width / src_img.width, height / src_img.height
            base_scale = max(w_r, h_r) * bg_zoom
            n_w, n_h = int(src_img.width * base_scale), int(src_img.height * base_scale)
            src_img = src_img.resize((n_w, n_h), resample=Image.LANCZOS)
            off_x, off_y = int((bg_x / 100) * (n_w - width)), int((bg_y / 100) * (n_h - height))
            left, top = int((n_w - width)/2) + off_x, int((n_h - height)/2) + off_y
            src_img = src_img.crop((left, top, left + width, top + height))
            img_canvas.paste(src_img, (0,0), src_img)
        except: pass
    
    overlay = Image.new('RGBA', (width, height), (0,0,0,0))
    draw = ImageDraw.Draw(overlay)
    m_n, hds, wks, kr_h = get_calendar_data(year, month, lang, use_holidays)
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
                
    wm_f = get_font(font_family, uploaded_font, 20, lang, True)
    curr_y = height - 30
    if show_moon1:
        draw.text((width - 30, curr_y), "Moon1", fill=wm_color, font=wm_f, anchor="rd")
        curr_y -= 30
    if show_custom and custom_text:
        draw.text((width - 30, curr_y), custom_text, fill=wm_color, font=wm_f, anchor="rd")
        
    return Image.alpha_composite(img_canvas, overlay).convert("RGB")

# --- UI 레이아웃 ---
st.set_page_config(page_title="달력 배경화면 생성기", layout="wide")

# 💡 리셋 카운터 초기화
if "reset_key" not in st.session_state:
    st.session_state.reset_key = 0

def reset_all():
    st.session_state.reset_key += 1
    # 세션에 저장된 커스텀 컬러 등도 삭제
    for key in list(st.session_state.keys()):
        if key != "reset_key":
            del st.session_state[key]

# 고유 접미사 (리셋될 때마다 바뀜)
suffix = f"_{st.session_state.reset_key}"

st.markdown("<h2 style='font-size: 1.8rem; text-align: center; margin-top: 0px;'>📅 달력 배경화면 생성기</h2>", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### ⚙️ 설정 메뉴")
    
    st.info("1️⃣ **화면 비율 설정**")
    cat = st.selectbox("기기 분류", ["스마트폰 (1080x2340)", "태블릿 (2048x2732)", "이북 리더기 (758x1024)", "직접 입력"], index=2, key=f"cat{suffix}")
    res = {"스마트폰 (1080x2340)": (1080, 2340), "태블릿 (2048x2732)": (2048, 2732), "이북 리더기 (758x1024)": (758, 1024)}
