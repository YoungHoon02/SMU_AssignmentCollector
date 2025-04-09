from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import re
import datetime
import tkinter as tk
from tkinter import ttk, font
import webbrowser
from threading import Thread

def calculate_remaining_time(deadline):
    """마감일까지 남은 시간을 계산 (Nd HH:MM 형식)"""
    now = datetime.datetime.now()
    if isinstance(deadline, datetime.date):
        deadline = datetime.datetime.combine(deadline, datetime.time(23, 59, 59))
    
    time_diff = deadline - now
    total_seconds = max(0, time_diff.total_seconds())
    
    days = int(total_seconds // (24 * 3600))
    hours = int((total_seconds % (24 * 3600)) // 3600)
    minutes = int((total_seconds % 3600) // 60)
    
    return f"{days}d {hours:02d}:{minutes:02d}"

def extract_course_details(course_name):
    """과목명에서 학수번호와 교수 이름을 분리."""
    course_code = None
    professor_name = None
    
    # 학수번호 추출 (예: HBXX0000 형식)
    course_code_match = re.search(r'\b[A-Z]{2,4}\d{4}\b', course_name)
    if course_code_match:
        course_code = course_code_match.group()
        course_name = course_name.replace(course_code, "").strip()
    
    # 교수 이름 추출 (예: '최영훈' 형식)
    professor_name_match = re.search(r'[가-힣]{2,4}', course_name)
    if professor_name_match:
        professor_name = professor_name_match.group()
        course_name = course_name.replace(professor_name, "").strip()
    
    course_name = re.sub(r'\[.*?\]', '', course_name)  # 대괄호 내용 제거
    # ')' 이후 남은 내용 제거
    if '(' in course_name:
        course_name = course_name.split('(')[0]
    course_name = course_name.strip()
    
    return course_name, course_code, professor_name

def create_hud(shared_data):
    """외부 HUD 창을 생성하여 마감 예정 콘텐츠를 표시합니다."""
    root = tk.Tk()
    root.title("SMU eCampus 마감 예정 콘텐츠")
    root.geometry("950x600")  # 창 크기 조정
    root.minsize(750, 400)
    
    font_normal = ('맑은 고딕', 10)
    font_bold = ('맑은 고딕', 11, 'bold')
    font_title = ('맑은 고딕', 14, 'bold')
    
    root.option_add('*Font', font_normal)
    
    default_font = tk.font.nametofont("TkDefaultFont")
    default_font.configure(family="맑은 고딕", size=10)
    
    text_font = tk.font.nametofont("TkTextFont")
    text_font.configure(family="맑은 고딕", size=10)
    
    fixed_font = tk.font.nametofont("TkFixedFont")
    fixed_font.configure(family="맑은 고딕", size=10)
    
    style = ttk.Style()
    style.configure(".", font=font_normal)
    style.configure("Treeview", font=font_normal)
    style.configure("Treeview.Heading", font=font_bold)
    style.configure("TLabelframe.Label", font=font_normal)
    style.configure("TButton", font=font_normal)
    
    control_frame = ttk.Frame(root)
    control_frame.pack(fill=tk.X, padx=10, pady=(10, 0))
    
    title_label = ttk.Label(control_frame, text="1주일 이내 마감 예정 콘텐츠 목록", font=font_title)
    title_label.pack(side=tk.LEFT, pady=(0, 10))
    
    control_var = tk.StringVar(value="중단")
    
    def toggle_crawl():
        """크롤링 시작/중단 토글."""
        if control_var.get() == "중단":
            control_var.set("재시작")
            shared_data["running"] = False
            status_label.config(text="크롤링이 중단되었습니다. 재시작 버튼을 누르면 계속합니다.")
        else:
            control_var.set("중단")
            shared_data["running"] = True
            shared_data["updated"] = True  # 재시작 시 데이터 갱신 플래그 설정
            status_label.config(text="크롤링이 다시 시작되었습니다...")
    
    control_button = ttk.Button(
        control_frame, 
        textvariable=control_var, 
        command=toggle_crawl,
        width=10
    )
    control_button.pack(side=tk.RIGHT, padx=5, pady=(0, 10))
    
    main_frame = ttk.Frame(root)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    separator1 = ttk.Separator(root, orient=tk.HORIZONTAL)
    separator1.pack(fill=tk.X, padx=10, pady=(0, 10))

    details_frame = ttk.LabelFrame(root, text="상세 정보")
    details_frame.pack(fill=tk.X, padx=10, pady=10)

    separator2 = ttk.Separator(root, orient=tk.HORIZONTAL)
    separator2.pack(fill=tk.X, padx=10, pady=(0, 10))

    status_frame = ttk.Frame(root)
    status_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=5)
    
    # HUD 칼럼 재구성 및 스타일 개선
    columns = ('course', 'title', 'type', 'submission', 'due_date', 'remaining_time')
    tree = ttk.Treeview(main_frame, columns=columns, show='headings')
    
    # 모든 헤더 가운데 정렬
    tree.heading('course', text='강좌명', anchor=tk.CENTER)
    tree.heading('title', text='콘텐츠 제목', anchor=tk.CENTER)
    tree.heading('type', text='유형', anchor=tk.CENTER)
    tree.heading('submission', text='제출상태', anchor=tk.CENTER)
    tree.heading('due_date', text='마감일', anchor=tk.CENTER)
    tree.heading('remaining_time', text='남은 시간', anchor=tk.CENTER)
    
    # 칼럼 너비 조정 - course와 title은 유동적, 나머지는 고정 크기
    tree.column('course', width=240, minwidth=240, stretch=True, anchor='w')
    tree.column('title', width=160, minwidth=160, stretch=True, anchor=tk.CENTER)
    tree.column('type', width=40, minwidth=40, stretch=False, anchor=tk.CENTER)
    tree.column('submission', width=70, minwidth=70, stretch=False, anchor=tk.CENTER)
    tree.column('due_date', width=90, minwidth=90, stretch=False, anchor=tk.CENTER)
    tree.column('remaining_time', width=80, minwidth=80, stretch=False, anchor=tk.CENTER)
    
    # 셀 데이터 정렬 설정 - 헤더는 모두 가운데, 컨텐츠는 type, submission, due_date, remaining_time만 가운데
    for col in columns:
        tree.heading(col, anchor=tk.CENTER)
    
    hscrollbar = ttk.Scrollbar(main_frame, orient=tk.HORIZONTAL, command=tree.xview)
    tree.configure(xscrollcommand=hscrollbar.set)
    hscrollbar.pack(side=tk.BOTTOM, fill=tk.X)
    
    scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=tree.yview)
    tree.configure(yscroll=scrollbar.set)
    
    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    item_deadlines = {}
    
    def update_tree_data():
        """HUD 데이터를 갱신합니다."""
        for item in tree.get_children():
            tree.delete(item)
            
        item_deadlines.clear()
        
        for i, content in enumerate(shared_data["contents"]):
            # 과목명에서 학수번호와 교수 이름 분리 및 개행문자, 괄호 제거
            course_name, course_code, professor_name = extract_course_details(content['course'])
            course_name = re.sub(r'\(.*?\)', '', course_name).replace("\n", " ").strip()  # 괄호 및 개행문자 제거
            content['course_code'] = course_code  # 학수번호 저장
            content['professor_name'] = professor_name  # 교수 이름 저장
            
            # 콘텐츠 제목에서 개행문자 제거
            title = content['title'].replace("\n", " ").strip()
            
            deadline_date = datetime.datetime.strptime(content['due_date'], '%Y-%m-%d').date()
            deadline = datetime.datetime.combine(deadline_date, datetime.time(23, 59, 59))
            remaining_time = calculate_remaining_time(deadline)
            
            tag = f"item{i}"
            
            # 미제출 과제 강조
            if content['status'] == "미제출":
                tree.tag_configure(tag, background='#ffcccc')  # 빨간색 강조
            else:
                tree.tag_configure(tag, background='#ffffff')  # 기본 흰색
            
            item_id = tree.insert('', tk.END, values=(
                course_name,
                title,
                content['type'],
                content['status'],
                content['due_date'],
                remaining_time
            ), tags=(tag,))
            
            item_deadlines[item_id] = deadline_date
        
        status_label.config(text=f"총 {len(shared_data['contents'])}개의 콘텐츠가 1주일 이내 마감 예정입니다.")
    
    def on_tree_select(event):
        try:
            selected_items = tree.selection()
            if selected_items:
                selected_item = selected_items[0]
                idx = tree.index(selected_item)
                if 0 <= idx < len(shared_data["contents"]):
                    content = shared_data["contents"][idx]
                    details_text.config(state=tk.NORMAL)
                    details_text.delete(1.0, tk.END)
                    details_info = f"제목: {content['title']}\n"
                    details_info += f"강좌: {content['course']}\n"
                    details_info += f"마감일: {content['due_date']}\n"
                    
                    deadline_date = datetime.datetime.strptime(content['due_date'], '%Y-%m-%d').date()
                    deadline = datetime.datetime.combine(deadline_date, datetime.time(23, 59, 59))
                    details_info += f"남은 시간: {calculate_remaining_time(deadline)}\n"
                    
                    details_info += f"상태: {content['status']}\n"
                    details_info += f"링크: {content['link']}\n\n"
                    details_info += f"내용: {content['context']}"
                    details_text.insert(tk.END, details_info)
                    details_text.config(state=tk.DISABLED)
                    
                    if content['link']:
                        more_button.config(state=tk.NORMAL)
                        more_button.link = content['link']
                    else:
                        more_button.config(state=tk.DISABLED)
                        more_button.link = None
        except Exception as e:
            print(f"상세 정보 표시 오류: {str(e)}")
    
    tree.bind('<<TreeviewSelect>>', on_tree_select)
    
    details_content_frame = ttk.Frame(details_frame)
    details_content_frame.pack(fill=tk.X, expand=True, padx=5, pady=5)
    
    details_text = tk.Text(details_content_frame, height=6, wrap=tk.WORD, font=font_normal)
    details_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    details_text.config(state=tk.DISABLED)
    
    button_frame = ttk.Frame(details_content_frame)
    button_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
    
    status_display = ttk.Label(button_frame, text="", font=font_normal)
    status_display.pack(pady=(10, 5))
    
    def open_link():
        if hasattr(more_button, 'link') and more_button.link:
            webbrowser.open(more_button.link)
    
    more_button = ttk.Button(button_frame, text="더보기", command=open_link, state=tk.DISABLED)
    more_button.pack(pady=5)
    more_button.link = None
    
    status_label = ttk.Label(
        status_frame, 
        text="크롤링을 시작합니다...",
        font=font_normal
    )
    status_label.pack(side=tk.LEFT)
    
    def update_remaining_time():
        """남은 시간을 업데이트하고 크롤링 상태를 확인합니다."""
        for item_id in item_deadlines:
            try:
                deadline_date = item_deadlines[item_id]
                deadline = datetime.datetime.combine(deadline_date, datetime.time(23, 59, 59))
                remaining = calculate_remaining_time(deadline)
                
                current_values = tree.item(item_id, 'values')
                new_values = list(current_values)
                new_values[5] = remaining
                tree.item(item_id, values=new_values)
            except:
                pass
        
        if shared_data.get("crawling_complete", False):
            control_var.set("완료됨")
            control_button.config(state=tk.DISABLED)
        else:
            control_button.config(state=tk.NORMAL)
        
        if shared_data.get("exit", False):
            return
        
        root.after(60000, update_remaining_time)
    
    def check_data_update():
        """데이터 업데이트를 확인하고 HUD를 갱신합니다."""
        if shared_data.get("updated", False):
            shared_data["updated"] = False
            update_tree_data()
        
        # 크롤링 종료 시 불필요한 기능 비활성화
        if shared_data.get("exit", False):
            return
        
        root.after(500, check_data_update)
    
    update_tree_data()
    check_data_update()
    update_remaining_time()
    
    def on_closing():
        """HUD 창 닫기 이벤트 처리."""
        shared_data["running"] = False
        shared_data["exit"] = True
        root.destroy()
        
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

def wait_for_page_load(driver, timeout=10):
    WebDriverWait(driver, timeout).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )

def main():
    options = webdriver.ChromeOptions()
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-infobars')
    options.add_argument('--disable-notifications')
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    shared_data = {
        "contents": [],
        "running": True,
        "exit": False,
        "updated": False,
        "crawling_complete": False
    }
    
    hud_thread = Thread(target=create_hud, args=(shared_data,))
    hud_thread.daemon = True
    hud_thread.start()
    
    try:
        driver.get("https://ecampus.smu.ac.kr/login.php")
        wait_for_page_load(driver)
        print("로그인 페이지가 열렸습니다. 직접 로그인해 주세요.")
        
        login_url = driver.current_url
        
        print("로그인을 기다리는 중...")
        timeout = 300
        start_time = time.time()
        
        while time.time() - start_time < timeout and not shared_data["exit"]:
            current_url = driver.current_url
            if current_url == "https://ecampus.smu.ac.kr/":
                print("로그인이 감지되었습니다.")
                wait_for_page_load(driver, 5)
                break
            time.sleep(1)
        else:
            if shared_data["exit"]:
                print("사용자에 의해 프로그램이 종료되었습니다.")
                return
            print("로그인 시간이 초과되었습니다. 계속하려면 엔터키를 눌러주세요...")
            input()
        
        if shared_data["exit"]: return
            
        current_url = driver.current_url
        if current_url == "https://ecampus.smu.ac.kr/":
            print("로그인이 확인되었습니다.")
        else:
            print("로그인이 확인되지 않았습니다. 다시 시도해 주세요.")
            return
        
        print("\n===== 콘텐츠 수집 시작 =====")
        
        all_contents = []
        processed_items = set()
        
        upcoming_blocks = driver.find_elements(By.CSS_SELECTOR, ".block_timeline, .block_calendar_upcoming, .block_myoverview")
        
        for block in upcoming_blocks:
            try:
                block_title = block.find_element(By.CSS_SELECTOR, ".card-title, .header").text.strip()
                print(f"블록 확인: {block_title}")
                
                events = block.find_elements(By.CSS_SELECTOR, ".list-group-item, .event")
                print(f"{len(events)}개 항목 발견")
                
                for event in events:
                    try:
                        event_text = event.text.strip()
                        links = event.find_elements(By.TAG_NAME, "a")
                        
                        if not links:
                            continue
                            
                        link = links[0].get_attribute("href")
                        if not link or not any(keyword in link for keyword in ['/mod/assign/', '/mod/econtents/']):
                            continue
                            
                        title = links[0].text.strip()
                        print(f"활동 발견: {title}")
                        
                        date_match = re.search(r'(\d{1,2})\s*(?:월|月)\s*(\d{1,2})', event_text)
                        deadline = None
                        
                        if date_match:
                            month = int(date_match.group(1))
                            day = int(date_match.group(2))
                            
                            year = datetime.date.today().year
                            estimated_date = datetime.date(year, month, day)
                            
                            if estimated_date < datetime.date.today():
                                estimated_date = datetime.date(year + 1, month, day)
                                
                            deadline = estimated_date
                        
                        content_type = "기타"
                        if "/mod/assign/" in link:
                            content_type = "과제"
                        elif "/mod/econtents/" in link:
                            content_type = "영상"
                        
                        if (title, link) in processed_items:
                            continue
                            
                        processed_items.add((title, link))
                        
                        course_name = "미확인 강좌"
                        course_match = re.search(r'course=(\d+)', link)
                        if course_match:
                            try:
                                course_link = f"https://ecampus.smu.ac.kr/course/view.php?id={course_match.group(1)}"
                                driver.execute_script("window.open(arguments[0]);", course_link)
                                driver.switch_to.window(driver.window_handles[-1])
                                wait_for_page_load(driver, 5)
                                try:
                                    course_title_elem = driver.find_element(By.CSS_SELECTOR, ".page-header-headings h1")
                                    course_name = course_title_elem.text.strip().replace("[천안]", "").strip()
                                except:
                                    pass
                                
                                driver.close()
                                driver.switch_to.window(driver.window_handles[0])
                            except:
                                pass
                        
                        if not deadline:
                            deadline = datetime.date.today() + datetime.timedelta(days=7)
                            
                        all_contents.append({
                            "course": course_name,
                            "title": title,
                            "link": link,
                            "due_date": str(deadline),
                            "status": "확인필요",
                            "context": event_text,
                            "type": content_type
                        })
                        
                        all_contents.sort(key=lambda x: x['due_date'])
                        shared_data["contents"] = all_contents
                        shared_data["updated"] = True
                    except Exception as e:
                        print(f"항목 처리 오류: {str(e)}")
                        continue
            except Exception as e:
                print(f"블록 처리 오류: {str(e)}")
                continue
        
        print("\n강좌 목록을 수집 중...")
        driver.get("https://ecampus.smu.ac.kr/")
        wait_for_page_load(driver, 5)
        
        course_links = []
        course_elems = driver.find_elements(By.CSS_SELECTOR, ".course_box, .coursebox, .course-listitem")
        
        for elem in course_elems:
            try:
                links = elem.find_elements(By.TAG_NAME, "a")
                for link in links:
                    href = link.get_attribute("href")
                    if href and "course/view.php?id=" in href:
                        title = link.text.strip().replace("[천안]", "").strip()
                        if title:
                            course_links.append((href, title))
                            break
            except:
                continue
        
        if len(course_links) < 3:
            all_links = driver.find_elements(By.TAG_NAME, "a")
            for link in all_links:
                try:
                    href = link.get_attribute("href")
                    if href and "course/view.php?id=" in href:
                        title = link.text.strip().replace("[천안]", "").strip()
                        if title and len(title) > 3 and (href, title) not in course_links:
                            course_links.append((href, title))
                except:
                    continue
        
        print(f"{len(course_links)}개 강좌 발견")
        
        for idx, (course_url, course_title) in enumerate(course_links):
            if not shared_data["running"] or shared_data["exit"]:
                if shared_data["exit"]: return
                print("크롤링이 일시 중단되었습니다. HUD에서 '재시작' 버튼을 누르면 계속됩니다.")
                while not shared_data["running"] and not shared_data["exit"]:
                    time.sleep(1)
                if shared_data["exit"]: return
                print("크롤링을 재개합니다.")
            
            print(f"\n[{idx+1}/{len(course_links)}] '{course_title}' 강좌 처리 중...")
            
            course_id_match = re.search(r'id=(\d+)', course_url)
            if course_id_match:
                course_id = course_id_match.group(1)
                
                try:
                    process_bulk_page(driver, f"https://ecampus.smu.ac.kr/mod/assign/index.php?id={course_id}", 
                                     course_title, "과제", all_contents, processed_items, shared_data)
                except Exception as e:
                    print(f"과제 일괄 페이지 처리 오류: {str(e)}")
                
                try:
                    process_bulk_page(driver, f"https://ecampus.smu.ac.kr/mod/econtents/index.php?id={course_id}", 
                                     course_title, "영상", all_contents, processed_items, shared_data)
                except Exception as e:
                    print(f"영상 일괄 페이지 처리 오류: {str(e)}")
            
            try:
                driver.get(course_url)
                wait_for_page_load(driver, 5)
                
                activity_items = driver.find_elements(By.CSS_SELECTOR, ".activity, .modtype_assign, .modtype_econtents, .activityinstance, .activity-item")
                
                for item in activity_items:
                    try:
                        item_html = item.get_attribute("outerHTML")
                        
                        if not ("mod/assign" in item_html or "mod/econtents" in item_html):
                            continue
                            
                        links = item.find_elements(By.TAG_NAME, "a")
                        if not links:
                            continue
                            
                        link = links[0].get_attribute("href")
                        title = links[0].text.strip()
                        
                        if not link or not title:
                            continue
                        
                        if "/mod/assign/view.php" in link or "/mod/econtents/view.php" in link:
                            continue
                        
                        if (title, link) in processed_items:
                            continue
                            
                        processed_items.add((title, link))
                        
                        content_type = "기타"
                        if "/mod/assign/" in link:
                            content_type = "과제"
                        elif "/mod/econtents/" in link:
                            content_type = "영상"
                        else:
                            continue
                        
                        deadline = None
                        item_text = item.text
                        
                        date_patterns = [
                            r'(\d{4})[-년/\.]\s*(\d{1,2})[-월/\.]\s*(\d{1,2})',
                            r'(\d{2})[-/\.]\s*(\d{1,2})[-/\.]\s*(\d{1,2})',
                            r'(\d{1,2})\s*[월/]\s*(\d{1,2})'
                        ]
                        
                        for pattern in date_patterns:
                            date_match = re.search(pattern, item_text)
                            if date_match:
                                try:
                                    if len(date_match.groups()) == 3:
                                        year = int(date_match.group(1))
                                        if year < 100:
                                            year += 2000
                                        month = int(date_match.group(2))
                                        day = int(date_match.group(3))
                                    else:
                                        month = int(date_match.group(1))
                                        day = int(date_match.group(2))
                                        year = datetime.date.today().year
                                        
                                    deadline = datetime.date(year, month, day)
                                    
                                    if deadline < datetime.date.today():
                                        deadline = datetime.date(year + 1, month, day)
                                    
                                    break
                                except:
                                    continue
                        
                        if not deadline:
                            try:
                                driver.execute_script("window.open(arguments[0]);", link)
                                driver.switch_to.window(driver.window_handles[-1])
                                wait_for_page_load(driver, 5)
                                
                                page_text = driver.find_element(By.TAG_NAME, "body").text
                                for pattern in date_patterns:
                                    date_match = re.search(pattern, page_text)
                                    if date_match:
                                        try:
                                            if len(date_match.groups()) == 3:
                                                year = int(date_match.group(1))
                                                if year < 100:
                                                    year += 2000
                                                month = int(date_match.group(2))
                                                day = int(date_match.group(3))
                                            else:
                                                month = int(date_match.group(1))
                                                day = int(date_match.group(2))
                                                year = datetime.date.today().year
                                                
                                            deadline = datetime.date(year, month, day)
                                            
                                            if deadline < datetime.date.today():
                                                if len(date_match.groups()) == 2:
                                                    deadline = datetime.date(year + 1, month, day)
                                            
                                            break
                                        except:
                                            continue
                                
                                status = "확인필요"
                                if content_type == "과제":
                                    status_elems = driver.find_elements(By.CSS_SELECTOR, ".submissionstatustable .c1, .statedetails")
                                    if status_elems:
                                        status_text = status_elems[0].text.strip()
                                        if "미제출" in status_text:
                                            status = "미제출"
                                        elif "제출" in status_text and "미제출" not in status_text:
                                            status = "제출됨"
                                elif content_type == "영상":
                                    progress_elems = driver.find_elements(By.CSS_SELECTOR, ".progress-bar, .progresstext")
                                    if progress_elems:
                                        progress_text = progress_elems[0].text.strip()
                                        if "100%" in progress_text or "완료" in progress_text:
                                            status = "제출됨"
                                        else:
                                            status = "미제출"
                                
                                context = "세부 정보 없음"
                                try:
                                    main_content = driver.find_element(By.ID, "region-main")
                                    context = main_content.text[:150] + "..."
                                except:
                                    pass
                                
                                driver.close()
                                driver.switch_to.window(driver.window_handles[0])
                            except Exception as e:
                                print(f"상세 페이지 확인 오류: {str(e)}")
                                
                                if len(driver.window_handles) > 1:
                                    driver.close()
                                    driver.switch_to.window(driver.window_handles[0])
                                
                                deadline = datetime.date.today() + datetime.timedelta(days=7)
                                status = "확인필요"
                                context = item_text
                        
                        if not deadline:
                            deadline = datetime.date.today() + datetime.timedelta(days=7)
                        
                        diff_days = (deadline - datetime.date.today()).days
                        if 0 <= diff_days <= 7:
                            print(f"{content_type} 발견: {title}, 마감일: {deadline}")
                            
                            all_contents.append({
                                "course": course_title,
                                "title": title,
                                "link": link,
                                "due_date": str(deadline),
                                "status": status,
                                "context": context if 'context' in locals() else item_text,
                                "type": content_type
                            })
                            
                            all_contents.sort(key=lambda x: x['due_date'])
                            shared_data["contents"] = all_contents
                            shared_data["updated"] = True
                    except Exception as e:
                        print(f"활동 항목 처리 오류: {str(e)}")
                        continue
                        
            except Exception as e:
                print(f"강좌 페이지 처리 오류: {str(e)}")
                continue
        
        for content in shared_data["contents"]:
            course_name = content['course']
            if "천안CTL" in course_name:
                content['category'] = "천안CTL"
                content['course'] = course_name.replace("천안CTL", "").strip()
            elif "SM-CLASS" in course_name:
                content['category'] = "SM-CLASS"
                content['course'] = course_name.replace("SM-CLASS", "").strip()
            elif "교과 기타" in course_name:
                content['category'] = "교과 기타"
                content['course'] = course_name.replace("교과 기타", "").strip()
            else:
                content['category'] = "일반"
        
        all_contents.sort(key=lambda x: x['due_date'])
        shared_data["contents"] = all_contents
        shared_data["updated"] = True
        
        shared_data["crawling_complete"] = True
        
        print("\n===== 수집 완료 =====")
        print(f"총 {len(all_contents)}개 항목 발견")
        
        if all_contents:
            print("\n===== 1주일 이내 마감 예정 콘텐츠 목록 =====")
            for idx, content in enumerate(all_contents):
                deadline_date = datetime.datetime.strptime(content['due_date'], '%Y-%m-%d').date()
                deadline = datetime.datetime.combine(deadline_date, datetime.time(23, 59, 59))
                remaining = calculate_remaining_time(deadline)
                
                print(f"\n[{idx+1}] {content['course']} - {content['title']} ({content['type']})")
                print(f"마감일: {content['due_date']}")
                print(f"남은 시간: {remaining}")
                print(f"상태: {content['status']}")
                print(f"링크: {content['link']}")
                print("-" * 50)
            
            print(f"\n총 {len(all_contents)}개의 콘텐츠가 1주일 이내 마감 예정입니다.")
        else:
            print("\n1주일 이내 마감 예정인 콘텐츠가 없습니다.")
        
        print("\n크롤링이 완료되었습니다. 결과를 확인하세요.")
        
        while not shared_data["exit"]:
            if shared_data.get("crawling_complete") and shared_data.get("running") == False:
                print("크롤링이 완료되었으며, 브라우저를 종료합니다.")
                driver.quit()
                break
            time.sleep(0.5)  # 상태 확인 주기를 더 짧게 설정
    
    except Exception as e:
        print(f"프로그램 실행 중 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        shared_data["exit"] = True
        if driver.service.process:
            driver.quit()
        print("Selenium 브라우저가 종료되었습니다.")

def process_bulk_page(driver, url, course_title, content_type, all_contents, processed_items, shared_data):
    print(f"{content_type} 일괄 페이지 확인: {url}")
    driver.get(url)
    wait_for_page_load(driver, 5)
    
    tables = driver.find_elements(By.CSS_SELECTOR, "table.generaltable")
    
    if not tables:
        print(f"{content_type} 테이블을 찾을 수 없습니다.")
        return
        
    print(f"{content_type} 테이블 발견: {len(tables)}개")
    
    table = tables[0]
    rows = table.find_elements(By.TAG_NAME, "tr")
    
    if len(rows) <= 1:
        print(f"{content_type} 항목이 없습니다.")
        return
        
    headers = rows[0].find_elements(By.TAG_NAME, "th")
    header_texts = [h.text.strip().lower() for h in headers]
    
    name_idx = 0
    due_idx = 1
    status_idx = 2
    
    for i, header in enumerate(header_texts):
        if any(keyword in header for keyword in ["이름", "제목", "과제", "콘텐츠"]):
            name_idx = i
        elif any(keyword in header for keyword in ["기한", "마감", "종료", "due"]):
            due_idx = i
        elif any(keyword in header for keyword in ["상태", "제출", "시청", "status"]):
            status_idx = i
    
    print(f"컬럼 인덱스 - 이름: {name_idx}, 기한: {due_idx}, 상태: {status_idx}")
    
    today = datetime.date.today()
    found_content = False
    
    for row_idx, row in enumerate(rows[1:], 1):
        try:
            cells = row.find_elements(By.TAG_NAME, "td")
            
            if len(cells) <= name_idx:
                continue
                
            name_cell = cells[name_idx]
            links = name_cell.find_elements(By.TAG_NAME, "a")
            
            if not links:
                continue
                
            title = links[0].text.strip()
            link = links[0].get_attribute("href")
            
            if (title, link) in processed_items:
                continue
                
            processed_items.add((title, link))
            
            deadline = None
            due_text = "마감일 정보 없음"
            
            if due_idx < len(cells):
                due_cell = cells[due_idx]
                due_text = due_cell.text.strip()
                
                date_patterns = [
                    r'(\d{4})[-년/\.]\s*(\d{1,2})[-월/\.]\s*(\d{1,2})',
                    r'(\d{2})[-/\.]\s*(\d{1,2})[-/\.]\s*(\d{1,2})'
                ]
                
                for pattern in date_patterns:
                    date_match = re.search(pattern, due_text)
                    if date_match:
                        try:
                            if len(date_match.groups()) == 3:
                                year = int(date_match.group(1))
                                if year < 100:
                                    year += 2000
                                month = int(date_match.group(2))
                                day = int(date_match.group(3))
                                
                                deadline = datetime.date(year, month, day)
                                break
                        except:
                            continue
            
            if not deadline:
                print(f"날짜 정보 없음: {title}")
                continue
            
            diff_days = (deadline - today).days
            if not (0 <= diff_days <= 7):
                continue
            
            status = "확인필요"
            status_text = "상태 정보 없음"
            
            if status_idx < len(cells):
                status_cell = cells[status_idx]
                status_text = status_cell.text.strip()
                
                if content_type == "과제":
                    if "미제출" in status_text:
                        status = "미제출"
                    elif "제출" in status_text and "미제출" not in status_text:
                        status = "제출됨"
                else:
                    if any(kw in status_text for kw in ["미시청", "미완료", "0%"]):
                        status = "미제출"
                    elif any(kw in status_text for kw in ["완료", "100%", "시청"]):
                        status = "제출됨"
            
            print(f"{content_type} 발견: {title}, 마감일: {deadline}, 상태: {status}")
            
            all_contents.append({
                "course": course_title,
                "title": title,
                "link": link,
                "due_date": str(deadline),
                "status": status,
                "context": f"마감일: {due_text}, 상태: {status_text}",
                "type": content_type
            })
            found_content = True
        except Exception as e:
            print(f"행 처리 오류: {str(e)}")
            continue
    
    if found_content:
        all_contents.sort(key=lambda x: x['due_date'])
        shared_data["contents"] = all_contents
        shared_data["updated"] = True
        print(f"{content_type} 정보 업데이트 완료: {course_title}")
    else:
        print(f"마감 예정 {content_type}가 없습니다.")

if __name__ == "__main__":
    main()