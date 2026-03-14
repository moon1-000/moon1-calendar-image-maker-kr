import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageColor
import calendar
from datetime import datetime, date
import io
import os
import holidays
import urllib.request # 💡 인터넷에서 폰트를 다운받기 위한 도구 추가

# --- 폰트 및 데이터 설정 ---
def get_font(font_option, uploaded_font, size, lang, force_bold=False):
    # 1. 사용자가 직접 올린 폰트가 있다면 최우선 적용
    if uploaded_font is not None:
        try:
            return ImageFont.truetype(io.BytesIO(uploaded_font.getvalue()), size)
        except:
            st.error("폰트 파일을 읽을 수 없습니다.")
    
    # 한국어일 때 Arial 깨짐 방지
    actual_font = font_option
    if lang == "한국어" and font_option == "Arial":
        actual_font = "맑은 고딕"
        
    font_dict = {
        "Arial": "arial.ttf",
        "맑은 고딕": "malgun.ttf",
        "바탕체": "batang.ttc",
        "나눔고딕": "NanumGothic.ttf"
    }
    
    font_file = font_dict.get(actual_font, "arial.ttf")
    if force_bold:
        font_file = font_file.replace(".ttf", "bd.ttf").replace(".ttc", "bd.ttc")
    
    # 2. 로컬(내 컴퓨터) 윈도우 환경일 경우
    path = os.path.join("C:\\Windows\\Fonts", font_file)
    if os.path.exists(path):
        return ImageFont.truetype(path, size)
    
    # 3. 💡 클라우드(인터넷) 환경일 경우: 크기 조절이 가능한 나눔고딕 자동 다운로드 적용
    cloud_font_name = "NanumGothicBold.ttf" if force_bold else "NanumGothicRegular.ttf"
    
    if not os.path.exists(cloud_font_name):
        try:
            # 구글 서버에서 폰트 파일 실시간 가져오기
            url = "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Bold.ttf" if force_bold else "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf"
            urllib.request.urlretrieve(url, cloud_font_name)
        except:
            pass
            
    if os.path.exists(cloud_font_name):
        return ImageFont.truetype(cloud_font_name, size)
        
    # 만약 모든게 실패하면 비상용 폰트 사용
    return ImageFont.load_default()

def get_calendar_data(year, month, lang, use_holidays):
    cal = calendar.TextCalendar(calendar.SUNDAY)
    weeks = cal.monthdayscalendar(year, month)
    kr_holidays = holidays.KR(years=year) if use_holidays else {}
    
    if lang == "한국어":
        m_name = f"{month}월"
        headers = ["일", "월", "화", "수", "목", "금", "토"]
    else:
        m_name = calendar.month_name[month].upper()
        headers = ["S", "M", "T", "W", "T", "F", "S"]
        
    return m_name, headers, weeks, kr_holidays

# --- 생성 함수 ---
def generate_wallpaper(width, height, year, month, pos_ratio, bg_type, bg_color, bg_image, 
                       text_color_hex, font_size, x_spacing, y_spacing, lang, font_family, uploaded_font, is_bold,
                       use_holidays, show_box, box_color_hex, box_opacity, box_radius,
                       show_watermark):
    
    if bg_type == "이미지 업로드" and bg_image is not None:
        img = Image.open(bg_image).convert("RGBA")
        img = ImageOps.fit(img, (width, height), centering=(0.5, 0.5))
    else:
        img = Image.new('RGBA', (width, height), color=bg_color)
    
    overlay = Image.new('RGBA', img.size, (0,0,0,0))
    draw = ImageDraw.Draw(overlay)
    
    m_name, headers, weeks, kr_holidays = get_calendar_data(year, month, lang, use_holidays)
    bold_font = get_font(font_family, uploaded_font, int(font_size * 1.5), lang, force_bold=True)
    reg_font = get_font(font_family, uploaded_font, font_size, lang, force_bold=is_bold)
    
    text_color = ImageColor.getrgb(text_color_hex)
    red_color = (220, 20, 60, 255)
    
    col_width = font_size * x_spacing
    row_height = font_size * y_spacing
    cal_width = col_width * 7
    cal_height = row_height * (len(weeks) + 2.5)
    
    start_x = (width - cal_width) / 2
    start_y = (height * (pos_ratio / 100)) - (cal_height / 2)

    if show_box:
        b_color = ImageColor.getrgb(box_color_hex)
        full_box_color = (b_color[0], b_color[1], b_color[2], int(255 * (box_opacity/100)))
        padding = 40
        draw.rounded_rectangle(
            [start_x - padding, start_y - padding, start_x + cal_width + padding, start_y + cal_height + padding],
            radius=box_radius, fill=full_box_color
        )

    draw.text((width/2, start_y + row_height/2), m_name, fill=text_color, font=bold_font, anchor="mm")
    
    header_y = start_y + (row_height * 2)
    for i, h in enumerate(headers):
        x = start_x + (i * col_width) + (col_width / 2)
        color = red_color if i == 0 else text_color
        draw.text((x, header_y), h, fill=color, font=reg_font, anchor="mm")

    for row_idx, week in enumerate(weeks):
        y = header_y + (row_height * (row_idx + 1))
        for col_idx, day in enumerate(week):
            if day != 0:
                x = start_x + (col_idx * col_width) + (col_width / 2)
                is_h = date(year, month, day) in kr_holidays
                color = red_color if (col_idx == 0 or is_h) else text_color
                draw.text((x, y), str(day), fill=color, font=reg_font, anchor="mm")

    if show_watermark:
        small_bold_font = get_font(font_family, uploaded_font, 20, lang, force_bold=True)
        draw.text((width - 30, height - 30), "Moon1", fill=text_color, font=small_bold_font, anchor="rd")

    return Image.alpha_composite(img, overlay).convert("RGB")

# --- UI 레이아웃 ---
st.set_page_config(page_title="달력 배경화면 생성기", layout="wide")

st.markdown("<h2 style='margin-top: 0px;'>📅 달력 배경화면 생성기</h2>", unsafe_allow_html=True)

with st.sidebar:
    st.header("1. 기기 규격 설정")
    category = st.selectbox("기기 분류", 
                            ["스마트폰 (1080x2340)", "태블릿 (2048x2732)", "이북 리더기 (758x1024)", "
