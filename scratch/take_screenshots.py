import asyncio
import os
import sys
import time
import subprocess
from PIL import Image, ImageDraw
from playwright.async_api import async_playwright

# Configuration
os.environ["PLAYWRIGHT_BROWSERS_PATH"] = r"C:\Users\Admin\OneDrive\Desktop\Projects\cotton-disease-detection\.playwright"
BASE_DIR = r"C:\Users\Admin\OneDrive\Desktop\Projects\cotton-disease-detection"
DB_PATH = os.path.join(BASE_DIR, "instance", "screenshot.db")
LOG_PATH = os.path.join(BASE_DIR, "scratch", "flask_server.log")

def create_mock_images():
    """Create mockup cotton leaves for the analysis."""
    print("Creating mock leaf images...")
    # Healthy leaf (Green)
    img_healthy = Image.new("RGB", (300, 300), (34, 139, 34))
    draw = ImageDraw.Draw(img_healthy)
    # Draw leaf veins
    draw.line([(150, 0), (150, 300)], fill=(50, 205, 50), width=4)
    draw.line([(150, 200), (50, 100)], fill=(50, 205, 50), width=3)
    draw.line([(150, 200), (250, 100)], fill=(50, 205, 50), width=3)
    draw.line([(150, 100), (80, 40)], fill=(50, 205, 50), width=3)
    draw.line([(150, 100), (220, 40)], fill=(50, 205, 50), width=3)
    img_healthy.save("scratch_healthy.jpg", "JPEG")

    # Diseased leaf (Yellowish brown with spots)
    img_diseased = Image.new("RGB", (300, 300), (184, 134, 11))
    draw_d = ImageDraw.Draw(img_diseased)
    # Veins
    draw_d.line([(150, 0), (150, 300)], fill=(139, 69, 19), width=4)
    draw_d.line([(150, 200), (50, 100)], fill=(139, 69, 19), width=3)
    draw_d.line([(150, 200), (250, 100)], fill=(139, 69, 19), width=3)
    # Add dark blight spots
    draw_d.ellipse([(80, 80), (100, 100)], fill=(40, 20, 0))
    draw_d.ellipse([(200, 70), (220, 90)], fill=(40, 20, 0))
    draw_d.ellipse([(140, 120), (170, 150)], fill=(40, 20, 0))
    draw_d.ellipse([(100, 180), (120, 200)], fill=(40, 20, 0))
    img_diseased.save("scratch_diseased.jpg", "JPEG")
    print("Mock leaf images created.")

async def run_screenshots():
    # 1. Start Flask app
    print("Starting Flask app in background...")
    env = os.environ.copy()
    env["DATABASE_URL"] = f"sqlite:///{DB_PATH}"
    env["FLASK_ENV"] = "development"
    env["FLASK_DEBUG"] = "0"
    
    # Delete old screenshot db if exists
    if os.path.exists(DB_PATH):
        try:
            os.remove(DB_PATH)
            print("Deleted old screenshot database.")
        except Exception as e:
            print("Failed to delete old screenshot DB:", e)

    # Ensure scratch dir exists
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    log_file = open(LOG_PATH, "w")

    # Launch flask server
    app_proc = subprocess.Popen(
        [sys.executable, "app.py"],
        env=env,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        text=True
    )
    
    # Wait for flask to start
    print("Waiting 6 seconds for Flask to initialize...")
    time.sleep(6)
    
    try:
        async with async_playwright() as p:
            print("Launching Edge browser...")
            browser = await p.chromium.launch(channel="msedge", headless=True)
            context = await browser.new_context(viewport={"width": 1280, "height": 850})
            page = await context.new_page()

            # 2. Register Admin User
            print("Navigating to registration...")
            await page.goto("http://127.0.0.1:5000/auth/register")
            await page.wait_for_selector('input[name="username"]')
            
            print("Filling registration form...")
            await page.fill('input[name="username"]', "admin")
            await page.fill('input[name="email"]', "admin@example.com")
            await page.fill('input[name="password"]', "Password123!")
            await page.fill('input[name="confirm_password"]', "Password123!")
            await page.click('button[type="submit"]')
            
            # Wait for redirect to index
            print("Waiting for login redirect...")
            await page.wait_for_url("http://127.0.0.1:5000/")
            await page.wait_for_selector("#dropZone")
            
            # 3. Screenshot 1: App Preview
            print("Capturing Screenshot 1 (App Preview)...")
            # Scroll to make sure drop zone is visible
            await page.evaluate("window.scrollTo(0, 400);")
            time.sleep(1.5)
            await page.screenshot(path="image (1).png")
            print("Saved image (1).png")

            # 4. Perform analysis on diseased leaf
            print("Uploading mock diseased leaf image...")
            await page.locator('input[type="file"]').set_input_files("scratch_diseased.jpg")
            await page.wait_for_selector("#panelReady", state="visible")
            
            print("Clicking analyze...")
            await page.click("#analyzeBtn")
            
            print("Waiting for results...")
            try:
                await page.wait_for_selector("#resultCard, #errorCard", state="visible", timeout=25000)
            except Exception as wait_err:
                print("Wait for resultCard timed out. Reading server logs...")
                raise wait_err
            
            # Check if error is displayed
            if await page.is_visible("#errorCard"):
                error_text = await page.inner_text("#errorMsg")
                print(f"Analysis failed on frontend: {error_text}")
                raise Exception(f"Frontend error during prediction: {error_text}")
                
            # Scroll to show results card nicely
            await page.evaluate("window.scrollTo(0, 600);")
            # Wait for chart animation
            time.sleep(2)
            
            # 5. Screenshot 3: Detection Comparison (Results)
            print("Capturing Screenshot 3 (Detection Results)...")
            await page.screenshot(path="image (3).png")
            print("Saved image (3).png")

            # 6. Go to Dashboard
            print("Navigating to Dashboard...")
            await page.goto("http://127.0.0.1:5000/dashboard")
            await page.wait_for_selector(".stats-grid")
            await page.evaluate("window.scrollTo(0, 0);")
            time.sleep(1.5)
            
            # Screenshot 2: Detection Summary (Dashboard)
            print("Capturing Screenshot 2 (Dashboard)...")
            await page.screenshot(path="image (2).png")
            print("Saved image (2).png")

            # 7. Go to Admin Panel
            print("Navigating to Admin Panel...")
            await page.goto("http://127.0.0.1:5000/admin/")
            await page.wait_for_selector(".stats-grid")
            time.sleep(1.5)
            
            # Screenshot 4: Class Lists + Metrics (Admin Panel)
            print("Capturing Screenshot 4 (Admin Panel)...")
            await page.screenshot(path="image (4).png")
            print("Saved image (4).png")

            print("Closing browser...")
            await browser.close()
            
    except Exception as run_err:
        print("Error during execution:", run_err)
        # Read and print flask logs
        log_file.close()
        if os.path.exists(LOG_PATH):
            print("\n--- FLASK SERVER LOGS ---")
            with open(LOG_PATH, "r") as f_log:
                print(f_log.read())
            print("-------------------------\n")
        raise run_err
    finally:
        print("Stopping Flask app server...")
        log_file.close()
        app_proc.terminate()
        try:
            app_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            app_proc.kill()
        print("Flask app server stopped.")

        # Cleanup mock files
        for f in ["scratch_healthy.jpg", "scratch_diseased.jpg"]:
            if os.path.exists(f):
                os.remove(f)
        if os.path.exists(DB_PATH):
            try:
                os.remove(DB_PATH)
            except:
                pass

if __name__ == "__main__":
    create_mock_images()
    asyncio.run(run_screenshots())
