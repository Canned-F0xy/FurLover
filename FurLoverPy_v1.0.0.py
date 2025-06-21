import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import requests
import os
import threading
import time
import webbrowser
import base64
import urllib3
import random

class FurLoverPy:
    def __init__(self, root):
        self.root = root
        self.root.title("FurLoverPy v1.0")
        self.root.geometry("800x600")

        self.cancel_requested = False

        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Button(main_frame, text="e621.net 홈페이지", command=self.open_e621).pack(fill=tk.X, pady=2)

        user_info_frame = ttk.LabelFrame(main_frame, text="사용자 정보 (User-Agent에 사용됩니다)", padding="10")
        user_info_frame.pack(fill=tk.X, pady=5)
        ttk.Label(user_info_frame, text="Username:").grid(row=0, column=0, sticky=tk.W)
        self.username_entry = ttk.Entry(user_info_frame, width=40)
        self.username_entry.grid(row=0, column=1, sticky=tk.EW)
        ttk.Label(user_info_frame, text="API Key:").grid(row=1, column=0, sticky=tk.W)
        self.apikey_entry = ttk.Entry(user_info_frame, width=40, show="*")
        self.apikey_entry.grid(row=1, column=1, sticky=tk.EW)
        user_info_frame.columnconfigure(1, weight=1)

        folder_frame = ttk.LabelFrame(main_frame, text="저장 경로", padding="10")
        folder_frame.pack(fill=tk.X, pady=5)
        self.folder_entry = ttk.Entry(folder_frame, state="readonly")
        self.folder_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=2)
        ttk.Button(folder_frame, text="경로 선택", command=self.select_folder).pack(side=tk.RIGHT)

        tags_frame = ttk.LabelFrame(main_frame, text="태그 (쉼표랑 공백으로 구분, 제외는 - 사용)", padding="10")
        tags_frame.pack(fill=tk.BOTH, pady=5, expand=True)
        self.tags_text = tk.Text(tags_frame, height=5, wrap=tk.WORD)
        self.tags_text.pack(fill=tk.BOTH, expand=True)
        self.tags_text.insert(tk.END, "female, kemono, -scat")
        ttk.Button(tags_frame, text="인기 태그 불러오기", command=self.load_tags).pack(fill=tk.X, pady=(5,0))

        options_frame = ttk.Frame(main_frame)
        options_frame.pack(fill=tk.X, pady=5)
        self.mode_var = tk.StringVar(value="image")
        ttk.Radiobutton(options_frame, text="이미지", variable=self.mode_var, value="image").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(options_frame, text="이미지 + 영상", variable=self.mode_var, value="both").pack(side=tk.LEFT, padx=5)

        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill=tk.X, pady=5)
        self.start_button = ttk.Button(action_frame, text="저장 시작", command=self.start_download)
        self.start_button.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.stop_button = ttk.Button(action_frame, text="저장 중지", command=self.stop_download, state="disabled")
        self.stop_button.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.progress = ttk.Progressbar(main_frame, orient=tk.HORIZONTAL, length=100, mode='determinate')
        self.progress.pack(fill=tk.X, pady=5)
        self.speed_label = ttk.Label(main_frame, text="")
        self.speed_label.pack(fill=tk.X)

        log_frame = ttk.LabelFrame(main_frame, text="로그", padding="10")
        log_frame.pack(fill=tk.BOTH, pady=5, expand=True)
        log_scrollbar = ttk.Scrollbar(log_frame)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text = tk.Text(log_frame, state="disabled", wrap=tk.WORD, yscrollcommand=log_scrollbar.set)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        log_scrollbar.config(command=self.log_text.yview)

    def _log(self, message):
        def append():
            self.log_text.config(state="normal")
            self.log_text.insert(tk.END, message + "\n")
            self.log_text.config(state="disabled")
            self.log_text.see(tk.END)
        self.root.after(0, append)

    def _update_progress(self, value, speed_text=""):
        def update():
            self.progress['value'] = value
            self.speed_label.config(text=speed_text)
        self.root.after(0, update)

    def _toggle_controls(self, is_running):
        state = "disabled" if is_running else "normal"
        self.start_button.config(state=state)
        self.stop_button.config(state="normal" if is_running else "disabled")
        self.username_entry.config(state=state)
        self.apikey_entry.config(state=state)
        self.tags_text.config(state=state)

    def open_e621(self):
        webbrowser.open("https://e621.net")
        self._log("e621.net 홈페이지를 열었습니다.")

    def select_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.folder_entry.config(state="normal")
            self.folder_entry.delete(0, tk.END)
            self.folder_entry.insert(0, folder_selected)
            self.folder_entry.config(state="readonly")
            self._log(f"저장 경로가 '{folder_selected}'로 설정되었습니다.")

    def load_tags(self):
        self._log("[태그 목록 불러오기 시작]")
        def fetch():
            try:
                username = self.username_entry.get().strip() or "anonymous"
                suffix = random.randint(1000, 9999)
                user_agent = f'FurLoverPy/1.0 (by {username} on e621)'
                headers = {'User-Agent': user_agent}
                time.sleep(0.2)
                res = requests.get('https://e621.net/tags/popular.json', headers=headers, timeout=10)
                res.raise_for_status()
                tags_data = res.json().get('tags', [])
                tag_names = [tag['name'] for tag in tags_data]
                self.root.after(0, lambda: self.tags_text.delete('1.0', tk.END))
                self.root.after(0, lambda: self.tags_text.insert('1.0', ", ".join(tag_names)))
                self._log("[태그 목록 불러오기 완료]")
            except requests.exceptions.RequestException as e:
                self._log(f"태그 불러오기 실패: {e}")
        threading.Thread(target=fetch, daemon=True).start()

    def stop_download(self):
        self.cancel_requested = True
        self._log("⛔ 다운로드 중지를 요청했습니다...")

    def start_download(self):
        folder = self.folder_entry.get()
        if not folder:
            messagebox.showerror("오류", "저장 경로를 선택해주세요.")
            return
        self.cancel_requested = False
        self._toggle_controls(is_running=True)
        self._update_progress(0, "")
        download_thread = threading.Thread(
            target=self._download_worker,
            args=(
                self.username_entry.get().strip(),
                self.apikey_entry.get().strip(),
                self.tags_text.get("1.0", tk.END).strip(),
                folder,
                self.mode_var.get() == "both"
            ),
            daemon=True
        )
        download_thread.start()

    def _download_worker(self, username, api_key, tags, folder, include_video):
        try:
            self._log("다운로드를 시작합니다...")

            user_agent = f'FurLoverPy/1.0 (by {username or "anonymous"} on e621)'
            self._log(f"[DEBUG] User-Agent: {user_agent}")

            session = requests.Session()
            retries = urllib3.util.retry.Retry(total=3, backoff_factor=2)
            adapter = requests.adapters.HTTPAdapter(max_retries=retries)
            session.mount("https://", adapter)
            session.headers.update({'User-Agent': user_agent})

            if username and api_key:
                auth_str = f"{username}:{api_key}"
                auth_b64 = base64.b64encode(auth_str.encode()).decode()
                session.headers.update({'Authorization': f'Basic {auth_b64}'})

            formatted_tags = ' '.join(
                tag.strip().replace(' ', '_') for tag in tags.replace('\n', '').split(',')
                if tag.strip()
            )
            time.sleep(0.2)
            res = session.get(
                'https://e621.net/posts.json',
                params={'tags': formatted_tags, 'limit': 100}
            )
            res.raise_for_status()
            posts = res.json().get('posts', [])

            if not posts:
                self._log("다운로드할 게시물을 찾을 수 없습니다. 태그를 확인해주세요.")
                return

            total_posts = len(posts)
            self._log(f"총 {total_posts}개의 게시물을 찾았습니다.")
            for i, post in enumerate(posts):
                if self.cancel_requested:
                    self._log("⛔ 다운로드가 사용자에 의해 중지되었습니다.")
                    return

                time.sleep(0.2)

                file_info = post.get('file')
                if not file_info or not file_info.get('url'):
                    continue

                file_url = file_info['url']
                ext = file_info['ext']
                is_video = ext in ['webm', 'mp4']

                if not include_video and is_video:
                    continue

                save_path = os.path.join(folder, f"{post['id']}.{ext}")
                self._log(f"({i+1}/{total_posts}) Post {post['id']} 다운로드 중...")

                try:
                    time.sleep(0.2)
                    with session.get(file_url, stream=True, timeout=30) as r:
                        r.raise_for_status()
                        downloaded_bytes = 0
                        start_time = time.time()
                        with open(save_path, 'wb') as f:
                            for chunk in r.iter_content(chunk_size=8192):
                                if self.cancel_requested:
                                    if os.path.exists(save_path): os.remove(save_path)
                                    self._log("⛔ 다운로드가 사용자에 의해 중지되었습니다.")
                                    return
                                f.write(chunk)
                                downloaded_bytes += len(chunk)
                                time.sleep(0.2)

                        elapsed_time = time.time() - start_time
                        speed_kbps = (downloaded_bytes / 1024 / elapsed_time) if elapsed_time > 0 else 0
                        progress_percent = ((i + 1) / total_posts) * 100
                        self._update_progress(progress_percent, f"{speed_kbps:.2f} KB/s")
                        self._log(f"✅ Post {post['id']} 저장완료.")

                except requests.exceptions.RequestException as e:
                    self._log(f"❌ 오류: Post {post['id']} 다운로드 실패 - {e}")

            self._log("🎉 모든 저장 완료.")

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                self._log("❌ 오류 발생: 인증 실패 (401). Username과 API Key를 확인해주세요.")
            else:
                self._log(f"❌ 오류 발생: HTTP 오류 - {e} (응답: {e.response.text})")
        except requests.exceptions.RequestException as e:
            self._log(f"❌ 오류 발생: 네트워크 오류 - {e}")
        except Exception as e:
            self._log(f"❌ 알 수 없는 오류 발생: {e}")
        finally:
            self.root.after(0, lambda: self._toggle_controls(is_running=False))
            self.root.after(0, lambda: self._update_progress(0, ""))

if __name__ == "__main__":
    root = tk.Tk()
    app = FurLoverPy(root)
    root.mainloop()
