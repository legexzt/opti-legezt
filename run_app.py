import uvicorn
import webbrowser
import threading
import time

def open_browser():
    time.sleep(1.5)
    webbrowser.open("http://localhost:8000")

if __name__ == "__main__":
    print("="*65)
    print("🚀 SMART ACADEMIC PERFORMANCE & REPORT STUDIO")
    print("   Starting Local Web Server on http://localhost:8000")
    print("="*65)
    threading.Thread(target=open_browser, daemon=True).start()
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
