import streamlit as st
from fpdf import FPDF
from PIL import Image
import io
import base64
import os

class PhotoPDF(FPDF):
    def __init__(self):
        super().__init__()
        # 경로를 더 확실하게 잡기 위해 절대 경로 사용
        base_path = os.path.dirname(__file__)
        font_path = os.path.join(base_path, 'font', 'malgun.ttf')
        bd_path = os.path.join(base_path, 'font', 'malgunbd.ttf' )
        try:
            # 이름을 소문자 'malgun'으로 통일해서 등록합니다.
            self.add_font('malgun', '', font_path)
            self.add_font('malgunbd', '', bd_path)
        except Exception as e:
            # 폰트 로드 실패 시 화면에 에러를 띄워줍니다.
            st.error(f"폰트 로드 실패! 경로를 확인하세요: {font_path}")

    def header(self):
        # 등록한 이름 'malgun'과 똑같이 호출
        if 'malgun' in self.fonts:
            self.set_font('malgun', '', 20)

            if self.page_no() > 1:
               if 'malgun' in self.fonts:
                   self.set_font('malgun', '', 20)
                   self.cell(0, 15, '사 진 대 지', align='C', new_x="LMARGIN", new_y="NEXT")
               else:
                self.set_font('helvetica', 'B', 20)
                self.cell(0, 15, 'PHOTO LOG', align='C', new_x="LMARGIN", new_y="NEXT")
            self.ln(5)

        else:
            self.set_font('helvetica', 'B', 20)
            self.cell(0, 15, 'PHOTO LOG', align='C', new_x="LMARGIN", new_y="NEXT")
        self.ln(5)

# --- (중략: 클래스 및 갑지 부분은 그대로 유지하되 cell 부분만 아래처럼 수정) ---

def create_combined_pdf(work_name, location, before_files, mid_files, after_files, contractor_name):
    pdf = PhotoPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # 1. [갑지 생성]
    pdf.add_page()
    pdf.set_font('malgunbd', '', 45)
    pdf.cell(0, 30, '사 진 대 지', align='C', new_x="LMARGIN", new_y="NEXT")

    # 로고 이미지는 파일이 없을 경우를 대비해 예외처리 추가
    try:
        main_img = Image.open("로고.jpg").convert('RGB')
        img_buffer = io.BytesIO()
        main_img.save(img_buffer, format='JPEG', quality=80)
        img_buffer.seek(0)
        pdf.image(img_buffer, x=30, y=80, w=150)
    except:
        st.warning("⚠️ '로고.jpg' 파일을 찾을 수 없어 이미지 없이 생성합니다.")

    # 상세 정보 테이블
    pdf.set_y(220)
    pdf.set_font('malgun', '', 15)
    info_fields = [('공 사 명', work_name), ('위 치', location), ('시 공 사', contractor_name)]
    
    for label, value in info_fields:
        pdf.set_x(35)
        pdf.cell(40, 15, label, border=1, align='C')
        pdf.cell(100, 15, value, border=1, align='L', new_x="LMARGIN", new_y="NEXT")

    # 2. [본문 사진 페이지]
    sections = [("시공전", before_files), ("시공중", mid_files), ("시공후", after_files)]
    
    for section_name, files in sections:
        if not files: continue
        for i in range(0, len(files), 2):
            pdf.add_page()
            batch = files[i:i+2]
            for img_file in batch:
                img = Image.open(img_file).convert('RGB')
                img.thumbnail((600, 600), Image.Resampling.LANCZOS)
                
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='JPEG', quality=30)
                img_byte_arr.seek(0)
                
                # 이미지 삽입
                pdf.image(img_byte_arr, x=25, w=160, h=90)
                pdf.ln(2) 
                
                # --- 🔥 여기가 에러의 주범! 최신 문법으로 수정 완료 ---
                pdf.set_font('malgun', '', 11)
                pdf.set_x(25)
                pdf.cell(25, 10, '공사명', border=1, align='C')
                pdf.cell(55, 10, work_name, border=1)
                pdf.cell(25, 10, '위 치', border=1, align='C')
                # ln=True 대신 new_x, new_y 사용
                pdf.cell(55, 10, location, border=1, new_x="LMARGIN", new_y="NEXT") 
                
                pdf.set_x(25)
                pdf.cell(25, 10, '내 용', border=1, align='C')
                # ln=True 대신 new_x, new_y 사용
                pdf.cell(135, 10, f"{section_name}", border=1, new_x="LMARGIN", new_y="NEXT")
                pdf.ln(10)
                
    return pdf.output()

# --- UI 레이아웃 부분 수정 ---
st.set_page_config(page_title="모바일 사진대지", layout="wide")
st.title("📱 사진대지")

# 1. 입력창 레이아웃 최적화 (모바일에서는 세로로 나열될 수 있음)
col1, col2 = st.columns([1, 1])
with col1:
    work_name = st.text_input("공사명", placeholder="공사명을 입력하세요")
with col2:
    location = st.text_input("위치", placeholder="위치를 입력하세요")

contractor_name = st.text_input("시공사", "역전의 명수")

# 2. 파일 업로더 (모바일 터치 편의성)
st.subheader("📸 사진 업로드")
# 모바일에서는 한 줄에 하나씩 나오는 것이 터치하기 편함
before = st.file_uploader("1. 시공전 사진", accept_multiple_files=True, key="before")
mid = st.file_uploader("2. 시공중 사진", accept_multiple_files=True, key="mid")
after = st.file_uploader("3. 시공후 사진", accept_multiple_files=True, key="after")

st.divider()

if before or mid or after:
    with st.spinner('PDF 생성 중... (모바일은 시간이 조금 더 걸릴 수 있습니다)'):
        pdf_bytes = create_combined_pdf(work_name, location, before, mid, after, contractor_name)
        
        st.write("✅ 선택된 시공전 사진 (클릭해서 크게 확인):")
        cols = st.columns(4) # 4열로 썸네일 배치
        for idx, file in enumerate(before):
            with cols[idx % 4]:
                 st.image(file)
        
        st.write("✅ 선택된 시공중 사진 (클릭해서 크게 확인):")
        cols = st.columns(4) # 4열로 썸네일 배치
        for idx, file in enumerate(mid):
            with cols[idx % 4]:
                 st.image(file)         

        st.write("✅ 선택된 시공후 사진 (클릭해서 크게 확인):")
        cols = st.columns(4) # 4열로 썸네일 배치
        for idx, file in enumerate(after):
            with cols[idx % 4]:
                 st.image(file)
            # 잘못 올렸다면 여기서 확인 가능!

        # 3. 다운로드 버튼 강조 (모바일에서 가장 중요!)
        st.download_button(
            label="🚀 완성된 PDF 다운로드 (터치)",
            data=bytes(pdf_bytes),
            file_name=f"{work_name}_사진대지.pdf",
            mime="application/pdf",            
        )
        st.info("💡 모바일에서 미리보기가 안 보인다면 위 버튼을 눌러 바로 다운로드하세요.")
        
        # 4. 모바일 호환 미리보기 (Object 태그 활용)
        base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
        # iframe 대신 object 태그를 사용하면 모바일 호환성이 조금 더 좋습니다.
        pdf_display = f'''
            <object data="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf">
                <div style="text-align:center; padding:20px; border:1px dashed #ccc;">
                    모바일 브라우저 환경에 따라 미리보기가 지원되지 않을 수 있습니다.<br>
                    위의 <b>다운로드 버튼</b>을 이용해 주세요.
                </div>
            </object>
        '''
        st.markdown(pdf_display, unsafe_allow_html=True)
