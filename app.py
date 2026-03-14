import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageColor
import calendar
from datetime import datetime, date
import io
import os
import holidays

# --- 폰트 및 데이터 설정 ---
def get_font(font_option, uploaded_font, size, lang, force_bold=False):
    if uploaded_font is not None:
        try:
            return ImageFont.truetype(io.BytesIO(uploaded_font.getvalue()), size)
        except:
            st.error("폰트 파일을 읽을 수 없습니다.")
    
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
    
    path = os.path.join("C:\\Windows\\Fonts", font_file)
    if os.path.exists(path):
        return ImageFont.truetype(path, size)
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
    
    # 💡 글자 크기와 무관하게 사용자가 간격 비율을 직접 조절하도록 변경
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

# 💡 상단 제목 크기 수정 (기존 st.title 대신 html <h2> 태그 사용으로 크기 축소 및 줄바꿈 방지)
st.markdown("<h2 style='margin-top: 0px;'>📅 달력 배경화면 생성기</h2>", unsafe_allow_html=True)

with st.sidebar:
    st.header("1. 기기 규격 설정")
    category = st.selectbox("기기 분류", 
                            ["스마트폰 (1080x2340)", "태블릿 (2048x2732)", "이북 리더기 (758x1024)", "직접 입력"],
                            index=2)
    
    res_map = {
        "스마트폰 (1080x2340)": (1080, 2340),
        "태블릿 (2048x2732)": (2048, 2732),
        "이북 리더기 (758x1024)": (758, 1024)
    }
    
    if category == "직접 입력":
        w, h = st.number_input("가로", value=1080), st.number_input("세로", value=1920)
    else:
        w, h = res_map[category]

    st.header("2. 날짜 및 위치")
    c1, c2 = st.columns(2)
    year, month = c1.number_input("년", value=2026), c2.number_input("월", 1, 12, 3)
    is_landscape = st.checkbox("🔄 가로로 돌리기 (가로 모드)", value=False)
    if is_landscape: w, h = h, w
    use_holidays = st.checkbox("대한민국 공휴일 반영", value=True)
    pos_val = st.slider("세로 위치 (%)", 0, 100, 50)

    st.header("3. 달력 디자인")
    lang = st.radio("언어", ["English", "한국어"], horizontal=True)
    font_family = st.selectbox("서체", ["Arial", "맑은 고딕", "바탕체", "나눔고딕"], index=0)
    is_bold = st.checkbox("볼드체 설정", value=False)
    uploaded_font = st.file_uploader("외부 폰트 추가 (.ttf, .otf)", type=['ttf', 'otf'])
    text_color = st.color_picker("텍스트 색상", "#000000")
    
    # 💡 글자 크기 기본값 상향 및 가로/세로 간격 슬라이더 추가
    font_size = st.slider("글자 크기", 10, 120, 40)
    x_spacing = st.slider("가로 간격 (격자 넓이)", 1.0, 5.0, 2.5, step=0.1)
    y_spacing = st.slider("세로 간격 (격자 높이)", 1.0, 5.0, 2.0, step=0.1)

    st.header("4. 배경 설정")
    bg_type = st.radio("배경", ["단색 컬러", "이미지 업로드"], horizontal=True, index=0)
    if bg_type == "이미지 업로드":
        bg_image = st.file_uploader("이미지 업로드", type=['jpg', 'png', 'jpeg'])
        bg_color = "#FFFFFF"
    else:
        bg_color = st.color_picker("배경색 선택", "#FFFFFF")
        bg_image = None
    
    st.markdown("---")
    show_box = st.checkbox("가독성 박스 추가(이미지 배경 시)", value=False)
    box_color = st.color_picker("바탕 색상", "#FFFFFF")
    box_opacity = st.slider("바탕 투명도", 0, 100, 100)
    box_radius = st.slider("바탕 모서리 곡률", 0, 100, 20)

    st.header("5. 제작자 출처 표기")
    show_watermark = st.checkbox("Moon1 마크 표시 (우측 하단)", value=False)

# 결과 생성
final_img = generate_wallpaper(w, h, year, month, pos_val, bg_type, bg_color, bg_image, 
                               text_color, font_size, x_spacing, y_spacing, lang, font_family, uploaded_font, is_bold,
                               use_holidays, show_box, box_color, box_opacity, box_radius,
                               show_watermark)

st.markdown("### 미리보기")
buf = io.BytesIO()
final_img.save(buf, format="PNG")
st.image(buf.getvalue(), width=400)
st.download_button("📥 이미지 파일로 저장", buf.getvalue(), f"calendar_{year}_{month}.png")
