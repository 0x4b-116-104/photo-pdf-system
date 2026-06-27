import streamlit as st
from fpdf import FPDF
from PIL import Image
import io
import base64
import os

class PhotoPDF(FPDF):
    def __init__(self):
        super().__init__()
        base_path = os.path.dirname(__file__)
        font_path = os.path.join(base_path, 'font', 'malgun.ttf')
        bd_path = os.path.join(base_path, 'font', 'malgunbd.ttf')
        try:
            self.add_font('malgun', '', font_path)
            self.add_font('malgunbd', '', bd_path)
        except Exception as e:
            printer(f"폰트 로드 실패! 경로를 확인하세요: {font_path}")

    def header(self):
        if 'malgun' in self.fonts:
            self.set_font('malgun', '', 20)
            if self.page_no() > 1:
                self.cell(0, 15, '사 진 대 지', align='C', new_x="LMARGIN", new_y="NEXT")
            self.ln(5)
        else:
            self.set_font('helvetica', 'B', 20)
            self.cell(0, 15, 'PHOTO LOG', align='C', new_x="LMARGIN", new_y="NEXT")
            self.ln(5)


def compress_image(img_file, max_size=1500, quality=60):
    """업로드된 파일을 즉시 압축해서 BytesIO로 반환"""
    img = Image.open(img_file).convert('RGB')
    if max(img.size) > max_size:
        img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=quality)
    buf.seek(0)
    return buf


def create_combined_pdf(work_name, location, before_bufs, mid_bufs, after_bufs, contractor_name):
    pdf = PhotoPDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    # 갑지
    pdf.add_page()
    pdf.set_font('malgunbd', '', 45)
    pdf.cell(0, 30, '사 진 대 지', align='C', new_x="LMARGIN", new_y="NEXT")

    try:
        img_buffer = io.BytesIO()
        main_img.save(img_buffer, format='JPEG', quality=80)
        img_buffer.seek(0)
        pdf.image(img_buffer, x=30, y=80, w=150)
    except:
        st.warning("⚠️ '로고.jpg' 파일을 찾을 수 없어 이미지 없이 생성합니다.")

    pdf.set_y(220)
    pdf.set_font('malgun', '', 15)
    for label, value in [('공 사 명', work_name), ('위 치', location), ('시 공 사', contractor_name)]:
        pdf.set_x(35)
        pdf.cell(40, 15, label, border=1, align='C')
        pdf.cell(100, 15, value, border=1, align='L', new_x="LMARGIN", new_y="NEXT")

    # 본문
    sections = [("시공전", before_bufs), ("시공중", mid_bufs), ("시공후", after_bufs)]
    for section_name, bufs in sections:
        if not bufs:
            continue
        for i in range(0, len(bufs), 2):
            pdf.add_page()
            for buf in bufs[i:i+2]:
                buf.seek(0)
                pdf.image(buf, x=25, w=160, h=90)
                pdf.ln(2)
                pdf.set_font('malgun', '', 11)
                pdf.set_x(25)
                pdf.cell(25, 10, '공사명', border=1, align='C')
                pdf.cell(55, 10, work_name, border=1)
                pdf.cell(25, 10, '위 치', border=1, align='C')
                pdf.cell(55, 10, location, border=1, new_x="LMARGIN", new_y="NEXT")
                pdf.set_x(25)
                pdf.cell(25, 10, '내 용', border=1, align='C')
                pdf.cell(135, 10, f"{section_name}", border=1, new_x="LMARGIN", new_y="NEXT")
                pdf.ln(10)

    return pdf.output()


# --- UI ---
st.set_page_config(page_title="모바일 사진대지", layout="wide")
st.title("📱 사진대지")

col1, col2 = st.columns([1, 1])
with col1:
    work_name = st.text_input("공사명", placeholder="공사명을 입력하세요")
with col2:
    location = st.text_input("위치", placeholder="위치를 입력하세요")

contractor_name = st.text_input("시공사", "시공사 입력")

st.subheader("📸 사진 업로드")
main_img = st.file_uploader("시공사 로고", accept_multiple_files=True, key="main_img")
before = st.file_uploader("1. 시공전 사진", accept_multiple_files=True, key="before")
mid    = st.file_uploader("2. 시공중 사진", accept_multiple_files=True, key="mid")
after  = st.file_uploader("3. 시공후 사진", accept_multiple_files=True, key="after")

st.divider()

# ✅ 핵심 변경: 버튼을 눌러야 PDF 생성
if st.button("📄 PDF 생성하기", type="primary", disabled=not (before or mid or after)):
    with st.spinner('이미지 압축 및 PDF 생성 중...'):
        try:
            # 업로드 완료 후 한번에 압축
            before_bufs = [compress_image(f) for f in before]
            mid_bufs    = [compress_image(f) for f in mid]
            after_bufs  = [compress_image(f) for f in after]

            pdf_bytes = create_combined_pdf(
                work_name, location,
                before_bufs, mid_bufs, after_bufs,
                contractor_name
            )
            final_data = pdf_bytes if isinstance(pdf_bytes, bytes) else bytes(pdf_bytes)

            st.success("✅ PDF 생성 완료!")

            st.download_button(
                label="📂 완성된 사진대지 PDF 다운로드",
                data=final_data,
                file_name=f"{work_name}_사진대지.pdf",
                mime="application/pdf",
                key="download-main"
            )

            base64_pdf = base64.b64encode(final_data).decode('utf-8')
            href = f'<a href="data:application/pdf;base64,{base64_pdf}" download="{work_name}_사진대지.pdf" style="color:#007bff;font-weight:bold;">[여기]를 눌러서 수동으로 다운로드</a>'
            st.markdown(href, unsafe_allow_html=True)

        except Exception as e:
            st.error(f"PDF 생성 오류: {e}")

st.info("""
💡 **안내사항**
- 사진 업로드 후 **'PDF 생성하기'** 버튼을 눌러주세요.
- 카톡 브라우저 사용 시 오른쪽 하단 '...' → **'다른 브라우저로 열기'**
""")
