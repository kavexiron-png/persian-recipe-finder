# -*- coding: utf-8 -*-
"""
سامانه هوشمند آشپزی و پیشنهاد غذا با پایتون (Python Recipe Engine)
توسعه داده شده توسط kavexiron
کاملاً خودکفا با کتابخانه‌های استاندارد پایتون (بدون نیاز به pip install خارجی)
شامل: پایگاه داده SQLite، وب‌سرور HTTP، موتور تطبیق مواد و پنل مدیریت ادمین
"""

import os
import sys
import json
import sqlite3
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

import tempfile
DB_PATH = os.path.join(tempfile.gettempdir(), "persian_recipes.sqlite")

# -------------------------------------------------------------
# 1. DATABASE & SEED DATA INITIALIZATION
# -------------------------------------------------------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ingredients (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        icon TEXT NOT NULL,
        category TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS recipes (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        emoji TEXT NOT NULL,
        cook_time TEXT NOT NULL,
        servings TEXT NOT NULL,
        difficulty TEXT NOT NULL,
        quantities TEXT NOT NULL,
        steps TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS recipe_ingredients (
        recipe_id TEXT NOT NULL,
        ingredient_id TEXT NOT NULL,
        PRIMARY KEY (recipe_id, ingredient_id),
        FOREIGN KEY (recipe_id) REFERENCES recipes(id),
        FOREIGN KEY (ingredient_id) REFERENCES ingredients(id)
    )
    """)

    # Seed Ingredients if empty
    cursor.execute("SELECT COUNT(*) FROM ingredients")
    if cursor.fetchone()[0] == 0:
        seed_ingredients = [
            ("chicken", "مرغ", "🍗", "protein"),
            ("meat", "گوشت قرمز / چرخ‌کرده", "🥩", "protein"),
            ("egg", "تخم‌مرغ", "🥚", "protein"),
            ("fish", "ماهی / تن ماهی", "🐟", "protein"),
            ("rice", "برنج", "🍚", "carb"),
            ("bread", "نان", "🥖", "carb"),
            ("lentil", "عدس", "🥣", "carb"),
            ("splitpea", "لپه", "🫘", "carb"),
            ("beans", "لوبیا قرمز / چیتی", "🫘", "carb"),
            ("barley", "جو پرک", "🌾", "carb"),
            ("walnut", "گردو", "🌰", "carb"),
            ("potato", "سیب‌زمینی", "🥔", "veg"),
            ("onion", "پیاز", "🧅", "veg"),
            ("tomato", "گوجه‌فرنگی", "🍅", "veg"),
            ("eggplant", "بادمجان", "🍆", "veg"),
            ("zucchini", "کدو سبز", "🥒", "veg"),
            ("mushroom", "قارچ", "🍄", "veg"),
            ("garlic", "سیر", "🧄", "veg"),
            ("ghormeh_sabzi", "سبزی قورمه", "🥬", "veg"),
            ("kashk", "کشک", "🥛", "dairy"),
            ("yogurt", "ماست", "🥣", "dairy"),
            ("paste", "رب گوجه‌فرنگی", "🥫", "staple"),
            ("pomegranate_paste", "رب انار", "🍯", "staple"),
            ("oil", "روغن و ادویه پایه", "🫒", "staple")
        ]
        cursor.executemany("INSERT INTO ingredients VALUES (?, ?, ?, ?)", seed_ingredients)

    # Seed Recipes if empty
    cursor.execute("SELECT COUNT(*) FROM recipes")
    if cursor.fetchone()[0] == 0:
        seed_recipes = [
            (
                "omlet", "املت گوجه‌فرنگی قهوه‌خانه‌ای", "🍳", "۱۵ دقیقه", "۲ نفر", "خیلی آسان",
                json.dumps(["تخم‌مرغ: ۳ عدد", "گوجه‌فرنگی رنده‌شده: ۳ عدد", "روغن و زردچوبه: به مقدار لازم"], ensure_ascii=False),
                json.dumps(["گوجه‌ها را در تابه تفت دهید تا آب آن کاملاً کشیده شود.", "تخم‌مرغ‌ها را روی گوجه شکسته و هم نزنید تا خودش را بگیرد.", "با نان تازه سرو کنید."], ensure_ascii=False),
                ["egg", "tomato", "oil"]
            ),
            (
                "kuku_sibzamini", "کوکو سیب‌زمینی برشته", "🥞", "۳۰ دقیقه", "۳ نفر", "آسان",
                json.dumps(["سیب‌زمینی آبپز: ۳ عدد", "تخم‌مرغ: ۲ عدد", "پیاز رنده شده: ۱ عدد", "ادویه و نمک: به مقدار لازم"], ensure_ascii=False),
                json.dumps(["سیب‌زمینی و پیاز رنده شده را با تخم‌مرغ و ادویه مخلوط کنید.", "مایه را در روغن داغ سرخ کنید تا دو طرف آن طلایی شود."], ensure_ascii=False),
                ["egg", "potato", "onion", "oil"]
            ),
            (
                "zereshk_polo", "زرشک پلو با مرغ مجلسی", "🍗", "۱ ساعت", "۴ نفر", "متوسط",
                json.dumps(["مرغ: ۴ تکه", "برنج: ۳ پیمانه", "پیاز: ۲ عدد", "رب گوجه: ۲ قاشق", "روغن و زعفران: به مقدار لازم"], ensure_ascii=False),
                json.dumps(["مرغ را با پیاز و ادویه تفت دهید و با سس رب بگذارید جا بیفتد.", "برنج را آبکش و دم کنید و با زرشک تزیین نمایید."], ensure_ascii=False),
                ["chicken", "rice", "onion", "paste", "oil"]
            ),
            (
                "adas_polo", "عدس پلو اصیل ایرانی", "🍛", "۵۰ دقیقه", "۴ نفر", "آسان",
                json.dumps(["برنج: ۳ پیمانه", "عدس پخته: ۱.۵ پیمانه", "پیاز داغ: ۱ پیمانه", "روغن و دارچین: کافی"], ensure_ascii=False),
                json.dumps(["عدس را پخته و با برنج آبکش شده مخلوط کنید.", "کمی دارچین زده و دم بگذارید."], ensure_ascii=False),
                ["rice", "lentil", "onion", "oil"]
            ),
            (
                "estamboli", "استانبولی پلو با سیب‌زمینی", "🥘", "۴۵ دقیقه", "۳ نفر", "آسان",
                json.dumps(["برنج: ۲.۵ پیمانه", "سیب‌زمینی نگینی: ۲ عدد", "پیاز: ۱ عدد", "رب گوجه: ۲ قاشق"], ensure_ascii=False),
                json.dumps(["سیب‌زمینی و پیاز را تفت دهید و رب اضافه کنید.", "برنج کته را با مایه مخلوط کرده و بگذارید دم بکشد."], ensure_ascii=False),
                ["rice", "potato", "onion", "paste", "oil"]
            ),
            (
                "kashk_bademjan", "کشک بادمجان سنتی", "🍆", "۳۵ دقیقه", "۳ نفر", "آسان",
                json.dumps(["بادمجان: ۴ عدد", "کشک غلیظ: نصف پیمانه", "پیاز: ۲ عدد", "سیر: ۳ حبه"], ensure_ascii=False),
                json.dumps(["بادمجان‌ها را سرخ کرده و بکوبید.", "سیرداغ و پیازداغ را اضافه کرده و کشک را ریخته و ۱۰ دقیقه حرارت دهید."], ensure_ascii=False),
                ["eggplant", "kashk", "onion", "garlic", "oil"]
            ),
            (
                "mirza_ghasemi", "میرزاقاسمی گیلانی", "🍅", "۳۰ دقیقه", "۲ نفر", "آسان",
                json.dumps(["بادمجان کبابی: ۳ عدد", "گوجه‌فرنگی رنده شده: ۳ عدد", "سیر: ۴ حبه", "تخم‌مرغ: ۲ عدد"], ensure_ascii=False),
                json.dumps(["سیرداغ بگیرید و گوجه را اضافه کنید تا غلیظ شود.", "بادمجان ساطوری را افزوده و تخم‌مرغ‌ها را روی آن بشکنید."], ensure_ascii=False),
                ["eggplant", "tomato", "garlic", "egg", "oil"]
            ),
            (
                "gheimeh", "خورش قیمه سیب‌زمینی", "🍛", "۲ ساعت", "۴ نفر", "متوسط",
                json.dumps(["گوشت خورشتی: ۳۰۰ گرم", "لپه خیس‌خورده: ۱ پیمانه", "سیب‌زمینی خلالی: ۲ عدد", "رب گوجه: ۲ قاشق"], ensure_ascii=False),
                json.dumps(["پیاز، گوشت و لپه را تفت دهید و رب گوجه بزنید.", "آب اضافه کرده تا آرام بپزد و با سیب‌زمینی سرخ‌شده سرو کنید."], ensure_ascii=False),
                ["meat", "splitpea", "potato", "onion", "paste", "oil"]
            ),
            (
                "kotlet", "کتلت گوشت و سیب‌زمینی", "🥩", "۴۰ دقیقه", "۴ نفر", "آسان",
                json.dumps(["گوشت چرخ‌کرده: ۳۰۰ گرم", "سیب‌زمینی خام رنده‌شده: ۲ عدد", "پیاز: ۱ عدد", "تخم‌مرغ: ۱ عدد"], ensure_ascii=False),
                json.dumps(["آب پیاز و سیب‌زمینی را بگیرید.", "با گوشت و تخم‌مرغ ورز دهید و در روغن سرخ کنید."], ensure_ascii=False),
                ["meat", "potato", "onion", "egg", "oil"]
            ),
            (
                "khorak_morgh", "خوراک مرغ و سیب‌زمینی", "🍲", "۴۰ دقیقه", "۳ نفر", "آسان",
                json.dumps(["سینه مرغ: ۳۵۰ گرم", "سیب‌زمینی: ۲ عدد", "پیاز: ۱ عدد", "رب گوجه: ۱.۵ قاشق"], ensure_ascii=False),
                json.dumps(["مرغ را با پیاز تفت دهید.", "سیب‌زمینی و رب و آب اضافه کنید تا غلیظ شود."], ensure_ascii=False),
                ["chicken", "potato", "onion", "paste", "oil"]
            )
        ]

        for r_id, title, emoji, c_time, servings, diff, q_json, steps_json, ings in seed_recipes:
            cursor.execute("INSERT INTO recipes VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (r_id, title, emoji, c_time, servings, diff, q_json, steps_json))
            for ing_id in ings:
                cursor.execute("INSERT INTO recipe_ingredients VALUES (?, ?)", (r_id, ing_id))

    conn.commit()
    conn.close()

# -------------------------------------------------------------
# 2. PYTHON MATCHING ALGORITHM ENGINE
# -------------------------------------------------------------
def suggest_recipes(selected_ingredient_ids):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get ingredients mapping
    cursor.execute("SELECT id, name, icon FROM ingredients")
    ing_map = {row[0]: {"name": row[1], "icon": row[2]} for row in cursor.fetchall()}

    # Get all recipes
    cursor.execute("SELECT id, title, emoji, cook_time, servings, difficulty, quantities, steps FROM recipes")
    all_recipes = cursor.fetchall()

    selected_set = set(selected_ingredient_ids)
    full_matches = []
    partial_matches = []

    for r in all_recipes:
        r_id, title, emoji, c_time, servings, diff, q_str, steps_str = r
        cursor.execute("SELECT ingredient_id FROM recipe_ingredients WHERE recipe_id = ?", (r_id,))
        required_ings = set([row[0] for row in cursor.fetchall()])

        if not required_ings:
            continue

        available = required_ings.intersection(selected_set)
        missing = required_ings.difference(selected_set)

        recipe_obj = {
            "id": r_id,
            "title": title,
            "emoji": emoji,
            "cook_time": c_time,
            "servings": servings,
            "difficulty": diff,
            "quantities": json.loads(q_str),
            "steps": json.loads(steps_str),
            "available_names": [ing_map[i]["name"] for i in available if i in ing_map],
            "missing_names": [ing_map[i]["name"] for i in missing if i in ing_map],
            "missing_count": len(missing)
        }

        if len(missing) == 0:
            full_matches.append(recipe_obj)
        elif len(missing) in (1, 2):
            partial_matches.append(recipe_obj)

    conn.close()
    return {
        "success": True,
        "selected_count": len(selected_set),
        "full_matches": full_matches,
        "partial_matches": partial_matches
    }

# -------------------------------------------------------------
# 3. HTTP SERVER & REST API HANDLER
# -------------------------------------------------------------
class RecipeHTTPHandler(BaseHTTPRequestHandler):
    def _set_headers(self, status=200, content_type="application/json; charset=utf-8"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers(200)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/" or path == "/index.html":
            self.serve_frontend()
        elif path == "/api/ingredients":
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, icon, category FROM ingredients")
            items = [{"id": r[0], "name": r[1], "icon": r[2], "cat": r[3]} for r in cursor.fetchall()]
            conn.close()
            self._set_headers(200)
            self.wfile.write(json.dumps({"success": True, "ingredients": items}, ensure_ascii=False).encode("utf-8"))
        elif path == "/api/recipes":
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT id, title, emoji, cook_time, servings, difficulty FROM recipes")
            items = [{"id": r[0], "title": r[1], "emoji": r[2], "time": r[3], "servings": r[4], "diff": r[5]} for r in cursor.fetchall()]
            conn.close()
            self._set_headers(200)
            self.wfile.write(json.dumps({"success": True, "recipes": items}, ensure_ascii=False).encode("utf-8"))
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Not Found"}).encode("utf-8"))

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
        try:
            payload = json.loads(body)
        except Exception:
            payload = {}

        if path == "/api/suggest":
            ings = payload.get("ingredients", [])
            result = suggest_recipes(ings)
            self._set_headers(200)
            self.wfile.write(json.dumps(result, ensure_ascii=False).encode("utf-8"))
        elif path == "/api/recipes":
            # Add new recipe (Admin action)
            r_id = payload.get("id")
            title = payload.get("title")
            emoji = payload.get("emoji", "🥘")
            c_time = payload.get("cook_time", "۳۰ دقیقه")
            servings = payload.get("servings", "۳ نفر")
            diff = payload.get("difficulty", "آسان")
            quantities = payload.get("quantities", [])
            steps = payload.get("steps", [])
            ing_ids = payload.get("ingredients", [])

            if not r_id or not title:
                self._set_headers(400)
                self.wfile.write(json.dumps({"success": False, "message": "ID and title required"}).encode("utf-8"))
                return

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO recipes VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                           (r_id, title, emoji, c_time, servings, diff, json.dumps(quantities, ensure_ascii=False), json.dumps(steps, ensure_ascii=False)))
            cursor.execute("DELETE FROM recipe_ingredients WHERE recipe_id = ?", (r_id,))
            for i_id in ing_ids:
                cursor.execute("INSERT INTO recipe_ingredients VALUES (?, ?)", (r_id, i_id))
            conn.commit()
            conn.close()

            self._set_headers(200)
            self.wfile.write(json.dumps({"success": True, "message": f"Recipe {title} saved successfully"}).encode("utf-8"))
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Endpoint not found"}).encode("utf-8"))

    def serve_frontend(self):
        # Read the generated food_recipe_finder.html
        base_dir = os.path.dirname(os.path.abspath(__file__))
        html_file = os.path.join(base_dir, "food_recipe_finder.html")
        if not os.path.exists(html_file):
            html_file = "/working_dir/c_6992d52b5d60b245/artifacts/file_generation/ttl=63d/output/food_recipe_finder.html"
        if os.path.exists(html_file):
            with open(html_file, "rb") as f:
                content = f.read()
            self._set_headers(200, "text/html; charset=utf-8")
            self.wfile.write(content)
        else:
            self._set_headers(200, "text/html; charset=utf-8")
            self.wfile.write("<h1>سامانه هوشمند پایتون فعال است</h1>".encode("utf-8"))

# -------------------------------------------------------------
# 4. CLI RUNNER
# -------------------------------------------------------------
def run_cli_test():
    init_db()
    print("=====================================================")
    print("kavexiron Python Recipe Matching Engine Test")
    print("=====================================================")
    test_cases = [
        (["egg", "tomato", "oil"], "املت سنتی"),
        (["egg", "potato", "onion", "oil"], "کوکو سیب‌زمینی"),
        (["chicken", "rice", "onion", "paste", "oil"], "زرشک پلو با مرغ")
    ]
    for test_ings, expected in test_cases:
        res = suggest_recipes(test_ings)
        print(f"\n[TEST] ورودی: {test_ings}")
        print(f"-> تعداد تطابق ۱۰۰٪: {len(res['full_matches'])}")
        for m in res['full_matches']:
            print(f"   ✓ {m['title']} ({m['cook_time']})")
        print(f"-> تعداد غذاهای با کسری ۱ یا ۲ قلم: {len(res['partial_matches'])}")
        for p in res['partial_matches'][:2]:
            print(f"   ⏳ {p['title']} (کسری: {', '.join(p['missing_names'])})")

if __name__ == "__main__":
    init_db()
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        run_cli_test()
    else:
        port = 8080
        server_address = ("127.0.0.1", port)
        httpd = HTTPServer(server_address, RecipeHTTPHandler)
        print(f"Server running on http://127.0.0.1:{port} (Press Ctrl+C to stop)")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")
