from flask import Flask, render_template, request
import datetime, re, random, sqlite3
try:
    from zoneinfo import ZoneInfo
except ImportError:
    pass 

app = Flask(__name__)
DB_NAME = "liuyao.db"

# ====================================================================
# --- 数据库初始化 ---
# ====================================================================
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS hexagram_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            create_time TEXT,
            question TEXT,
            hex_lines TEXT,
            result_text TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_to_db(q, lines_str, result):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    now_str = datetime.datetime.now(ZoneInfo("America/New_York")).strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('''
        INSERT INTO hexagram_history (create_time, question, hex_lines, result_text)
        VALUES (?, ?, ?, ?)
    ''', (now_str, q, lines_str, result))
    conn.commit()
    conn.close()

init_db()

# ====================================================================
# --- 易学基础常数 ---
# ====================================================================
GAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
ZHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
SHEN = ["青龙", "朱雀", "勾陈", "腾蛇", "白虎", "玄武"]

BAGUA_MAP = {
    (1,1,1): ("乾", "金"), (0,0,0): ("坤", "土"),
    (0,0,1): ("震", "木"), (1,1,0): ("巽", "木"),
    (0,1,0): ("坎", "水"), (1,0,1): ("离", "火"),
    (1,0,0): ("艮", "土"), (0,1,1): ("兑", "金")
}

GONG_DATA = {
    "乾": [("乾为天", [1,1,1,1,1,1]), ("天风姤", [1,1,1,1,1,0]), ("天山遁", [1,1,1,1,0,0]),
           ("天地否", [1,1,1,0,0,0]), ("风地观", [1,1,0,0,0,0]), ("山地剥", [1,0,0,0,0,0]),
           ("火地晋", [1,0,1,0,0,0]), ("火天大有", [1,0,1,1,1,1])],
    "兑": [("兑为泽", [0,1,1,0,1,1]), ("泽水困", [0,1,1,0,1,0]), ("泽地萃", [0,1,1,0,0,0]),
           ("泽山咸", [0,1,1,1,0,0]), ("水山蹇", [0,1,0,1,0,0]), ("地山谦", [0,0,0,1,0,0]),
           ("雷山小过", [0,0,1,1,0,0]), ("雷泽归妹", [0,0,1,0,1,1])],
    "离": [("离为火", [1,0,1,1,0,1]), ("火山旅", [1,0,1,1,0,0]), ("火风鼎", [1,0,1,1,1,0]),
           ("火水未济", [1,0,1,0,1,0]), ("山水蒙", [1,0,0,0,1,0]), ("风水涣", [1,1,0,0,1,0]),
           ("天水讼", [1,1,1,0,1,0]), ("天火同人", [1,1,1,1,0,1])],
    "震": [("震为雷", [0,0,1,0,0,1]), ("雷地豫", [0,0,1,0,0,0]), ("雷水解", [0,0,1,0,1,0]),
           ("雷风恒", [0,0,1,1,1,0]), ("地风升", [0,0,0,1,1,0]), ("水风井", [0,1,0,1,1,0]),
           ("泽风大过", [0,1,1,1,1,0]), ("泽雷随", [0,1,1,0,0,1])],
    "巽": [("巽为风", [1,1,0,1,1,0]), ("风天小畜", [1,1,0,1,1,1]), ("风火家人", [1,1,0,1,0,1]),
           ("风雷益", [1,1,0,0,0,1]), ("天雷无妄", [1,1,1,0,0,1]), ("火雷噬嗑", [1,0,1,0,0,1]),
           ("山雷颐", [1,0,0,0,0,1]), ("山风蛊", [1,0,0,1,1,0])],
    "坎": [("坎为水", [0,1,0,0,1,0]), ("水泽节", [0,1,0,0,1,1]), ("水雷屯", [0,1,0,0,0,1]),
           ("水火既济", [0,1,0,1,0,1]), ("泽火革", [0,1,1,1,0,1]), ("雷火丰", [0,0,1,1,0,1]),
           ("地火明夷", [0,0,0,1,0,1]), ("地水师", [0,0,0,0,1,0])],
    "艮": [("艮为山", [1,0,0,1,0,0]), ("山火贲", [1,0,0,1,0,1]), ("山天大畜", [1,0,0,1,1,1]),
           ("山泽损", [1,0,0,0,1,1]), ("火泽睽", [1,0,1,0,1,1]), ("天泽履", [1,1,1,0,1,1]),
           ("风泽中孚", [1,1,0,0,1,1]), ("风山渐", [1,1,0,1,0,0])],
    "坤": [("坤为地", [0,0,0,0,0,0]), ("地雷复", [0,0,0,0,0,1]), ("地泽临", [0,0,0,0,1,1]),
           ("地天泰", [0,0,0,1,1,1]), ("雷天大壮", [0,0,1,1,1,1]), ("泽天夬", [0,1,1,1,1,1]),
           ("水天需", [0,1,0,1,1,1]), ("水地比", [0,1,0,0,0,0])]
}

NAJIA = {
    "乾": (["甲子", "甲寅", "甲辰"], ["壬午", "壬申", "壬戌"]),
    "坤": (["乙未", "乙巳", "乙卯"], ["癸丑", "癸亥", "癸酉"]),
    "震": (["庚子", "庚寅", "庚辰"], ["庚午", "庚申", "庚戌"]),
    "巽": (["辛丑", "辛亥", "辛酉"], ["辛未", "辛巳", "辛卯"]),
    "坎": (["戊寅", "戊辰", "戊午"], ["戊申", "戊戌", "戊子"]),
    "离": (["己卯", "己丑", "己亥"], ["己酉", "己未", "己巳"]),
    "艮": (["丙辰", "丙午", "丙申"], ["丙戌", "丙子", "丙寅"]),
    "兑": (["丁巳", "丁卯", "丁丑"], ["丁亥", "丁酉", "丁未"])
}

WX_REL = {"金": {"生": "水", "克": "木"}, "木": {"生": "火", "克": "土"}, "水": {"生": "木", "克": "火"}, "火": {"生": "土", "克": "金"}, "土": {"生": "金", "克": "水"}}
ZHI_WX = {"子":"水", "丑":"土", "寅":"木", "卯":"木", "辰":"土", "巳":"火", "午":"火", "未":"土", "申":"金", "酉":"金", "戌":"土", "亥":"水"}

def get_relation_short(me_wx, target_wx):
    if me_wx == target_wx: return "兄"
    if WX_REL[me_wx]["生"] == target_wx: return "子"
    if WX_REL[target_wx]["生"] == me_wx: return "父"
    if WX_REL[me_wx]["克"] == target_wx: return "财"
    return "官"

# ====================================================================
# --- 干支历法 ---
# ====================================================================
class PreciseGanzhi:
    def __init__(self, dt):
        self.dt = dt
        year, month, day, hour, minute = dt.year, dt.month, dt.day, dt.hour, dt.minute

        y_idx = year - 4
        if month < 2 or (month == 2 and day < 4): y_idx -= 1
        y_stem_idx, y_branch_idx = y_idx % 10, y_idx % 12
        self.year_gz = GAN[y_stem_idx] + ZHI[y_branch_idx]

        solar_terms_day = [4, 6, 5, 5, 6, 7, 7, 7, 8, 8, 7, 6]
        m_branch_idx = (month - 2) if day >= solar_terms_day[month-1] else (month - 3)
        m_branch_idx %= 12
        tiger_start = ((y_stem_idx % 5) * 2 + 2) % 10
        self.month_gz = GAN[(tiger_start + m_branch_idx) % 10] + ZHI[(m_branch_idx + 2) % 12]

        bazi_date = dt.date()
        if hour == 23:
            bazi_date += datetime.timedelta(days=1)
            
        anchor_date = datetime.date(2000, 1, 1)
        delta_days = (bazi_date - anchor_date).days
        d_stem_idx, d_branch_idx = (4 + delta_days) % 10, (6 + delta_days) % 12
        self.day_gz = GAN[d_stem_idx] + ZHI[d_branch_idx]

        h_branch_idx = ((hour + 1) // 2) % 12
        rat_start = ((d_stem_idx % 5) * 2) % 10
        h_stem_idx = (rat_start + h_branch_idx) % 10
        self.hour_gz = GAN[h_stem_idx] + ZHI[h_branch_idx]

        minutes_from_23 = minute if hour == 23 else ((hour + 1) * 60 + minute)
        ke_offset = minutes_from_23 // 10
        fen_offset = minutes_from_23 % 10

        base_ke_idx = (d_stem_idx % 5) * 12
        ke_idx = (base_ke_idx + ke_offset) % 60
        k_stem_idx = ke_idx % 10
        self.xun_gz = GAN[k_stem_idx] + ZHI[ke_idx % 12]

        base_fen_idx = (k_stem_idx % 5) * 12
        fen_idx = (base_fen_idx + fen_offset) % 60
        self.fen_gz = GAN[fen_idx % 10] + ZHI[fen_idx % 12]

        xun_branch_idx = (d_branch_idx - d_stem_idx) % 12
        self.kongwang = f"{ZHI[(xun_branch_idx - 2) % 12]} {ZHI[(xun_branch_idx - 1) % 12]}"

# ====================================================================
# --- 排盘渲染 (动爻及静卦0标记版) ---
# ====================================================================
class Hexagram:
    def __init__(self, lines, gz, question=""):
        self.lines = lines
        self.gz = gz
        self.question = question or "未填写"
        self.base_bits = [1 if x in [7, 9] else 0 for x in lines]
        self.change_flags = [1 if x in [6, 9] else 0 for x in lines]
        self.changed_bits = [1-b if c else b for b, c in zip(self.base_bits, self.change_flags)]
        
        # 优化点：若无动爻则显示 "0"，有动爻则显示具体爻位数字
        moving_indices = [str(i + 1) for i, x in enumerate(self.lines) if x in [6, 9]]
        self.moving_lines_str = " ".join(moving_indices) if moving_indices else "0"

        self.main_name, self.gong, self.gong_wx, self.shi_pos, self.ying_pos, self.gong_num = self._parse_gua(self.base_bits)
        if any(self.change_flags):
            self.changed_name, self.c_gong, self.c_gong_wx, self.c_shi, self.c_ying, self.c_gong_num = self._parse_gua(self.changed_bits)
        else:
            self.changed_name = ""

    def _parse_gua(self, bits):
        top_to_bottom = bits[::-1]
        for gong, g_list in GONG_DATA.items():
            for idx, (name, pattern) in enumerate(g_list):
                if top_to_bottom == pattern:
                    shi_map = [6, 1, 2, 3, 4, 5, 4, 3]
                    shi = shi_map[idx]
                    return name, gong, BAGUA_MAP[tuple(pattern[3:])][1] if idx < 6 else BAGUA_MAP[tuple(pattern[:3])][1], shi, (shi + 3) if shi <= 3 else (shi - 3), idx + 1
        return "未知卦", "乾", "金", 6, 3, 1

    def _get_najia(self, bits):
        inner_tb, outer_tb = tuple(bits[:3][::-1]), tuple(bits[3:][::-1])
        return NAJIA[BAGUA_MAP[inner_tb][0]][0] + NAJIA[BAGUA_MAP[outer_tb][0]][1]

    def render_text(self):
        m_najia = self._get_najia(self.base_bits)
        has_change = any(self.change_flags)
        c_najia = self._get_najia(self.changed_bits) if has_change else [""] * 6
        
        day_stem = self.gz.day_gz[0]
        start_idx = {"甲":0, "乙":0, "丙":1, "丁":1, "戊":2, "己":3, "庚":4, "辛":4, "壬":5, "癸":5}[day_stem]
        six_gods = SHEN[start_idx:] + SHEN[:start_idx]

        fushen = {}
        if self.shi_pos != 6:
            ben_najia = self._get_najia(GONG_DATA[self.gong][0][1][::-1])
            m_rels = [get_relation_short(self.gong_wx, ZHI_WX[gz[1]]) for gz in m_najia]
            for r in ["父", "兄", "子", "财", "官"]:
                if r not in m_rels:
                    ben_rels = [get_relation_short(self.gong_wx, ZHI_WX[gz[1]]) for gz in ben_najia]
                    if r in ben_rels:
                        idx = ben_rels.index(r)
                        fushen[idx] = f"{r} {ben_najia[idx]} {ZHI_WX[ben_najia[idx][1]]}"

        res = [f"问：{self.question}", f"公历：{self.gz.dt.strftime('%Y年%m月%d日 %H:%M')}", 
               f"干支：{self.gz.year_gz}年 {self.gz.month_gz}月 {self.gz.day_gz}日 {self.gz.hour_gz}时 {self.gz.xun_gz}旬 {self.gz.fen_gz}分 (空亡: {self.gz.kongwang})\n"]

        m_name_disp = f"{self.main_name} {self.moving_lines_str}".strip()
        
        def get_dw(s):
            return sum(2 if ord(c) > 127 else 1 for c in str(s))

        def pad_dw(s, w):
            s_str = str(s)
            curr = get_dw(s_str)
            if curr >= w:
                return s_str
            return s_str + " " * (w - curr)

        if has_change:
            res.append(f"{pad_dw('六神', 4)} {pad_dw('伏神', 14)}  {self.gong}宫{self.gong_num}: {m_name_disp:<8}   {self.c_gong}宫{self.c_gong_num}: {self.changed_name}")
        else:
            res.append(f"{pad_dw('六神', 4)} {pad_dw('伏神', 14)}  {self.gong}宫{self.gong_num}: {m_name_disp}")

        symbols = {6: "‖×", 7: "│ ", 8: "‖ ", 9: "│◯"}
        for i in range(5, -1, -1):
            line_num = i + 1
            wx = ZHI_WX[m_najia[i][1]]
            shi_ying = "世" if line_num == self.shi_pos else ("应" if line_num == self.ying_pos else "")
            
            fs_str = fushen.get(i, "")
            
            col_god = pad_dw(six_gods[i], 4)
            col_fs = pad_dw(fs_str, 14)
            col_line = pad_dw(str(line_num), 2)
            col_rel = pad_dw(get_relation_short(self.gong_wx, wx), 2)
            col_najia = pad_dw(m_najia[i], 4)
            col_wx = pad_dw(wx, 2)
            col_sym = pad_dw(symbols[self.lines[i]], 3)
            col_shi = pad_dw(shi_ying, 2)

            main_str = f"{col_god} {col_fs} {col_line} {col_rel} {col_najia} {col_wx} {col_sym} {col_shi}"

            if has_change:
                c_wx = ZHI_WX[c_najia[i][1]]
                c_shi_ying = "世" if line_num == self.c_shi else ("应" if line_num == self.c_ying else "")
                
                c_rel = pad_dw(get_relation_short(self.c_gong_wx, c_wx), 2)
                c_najia_col = pad_dw(c_najia[i], 4)
                c_wx_col = pad_dw(c_wx, 2)
                c_sym_col = pad_dw(('│' if self.changed_bits[i] == 1 else '‖'), 2)
                c_shi_col = pad_dw(c_shi_ying, 2)

                main_str += f"    {c_rel} {c_najia_col} {c_wx_col} {c_sym_col} {c_shi_col}"
                
            res.append(main_str)
        return "\n".join(res)

# ====================================================================
# --- 路由 ---
# ====================================================================
@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@app.route('/calculate', methods=['GET', 'POST'])
def calculate():
    if request.method == 'GET':
        return render_template('index.html')

    q = request.form.get('question', '').strip()
    hex_raw = request.form.get('hex_lines', '').strip()
    manual_time_str = request.form.get('manual_time', '').strip()
    is_dst = str(request.form.get('is_dst', '')).strip().lower()

    if manual_time_str:
        try:
            dt = datetime.datetime.strptime(manual_time_str, '%Y-%m-%dT%H:%M')
            if is_dst in ['1', 'on', 'true', 'yes', 'checked']:
                dt = dt - datetime.timedelta(hours=1)
                q += " (手动扣减夏令时1小时)"
        except ValueError:
            dt, q = get_auto_time(q)
    else:
        dt, q = get_auto_time(q)

    if hex_raw:
        try:
            lines = [int(x) for x in re.sub(r'[a-zA-Z]', '', hex_raw).replace(',', ' ').split()]
            if len(lines) != 6 or not all(x in [6, 7, 8, 9] for x in lines): raise ValueError
        except ValueError:
            return render_template('index.html', result="输入错误：爻象必须是6个数字 (6, 7, 8, 9)，用空格隔开。")
    else:
        lines = [sum([random.choice([2, 3]) for _ in range(3)]) for _ in range(6)]

    try:
        lines_str = " ".join(map(str, lines))
        result_text = Hexagram(lines, PreciseGanzhi(dt), q).render_text()
        save_to_db(q, lines_str, result_text)
        return render_template('index.html', result=result_text)
    except Exception as e:
        return render_template('index.html', result=f"运算异常: {e}")

def get_auto_time(q_str):
    now_ny = datetime.datetime.now(ZoneInfo("America/New_York"))
    auto_dt = now_ny.replace(tzinfo=None)
    if now_ny.dst(): 
        auto_dt = auto_dt - datetime.timedelta(hours=1)
        q_str += " (系统已自动扣减夏令时1小时)"
    return auto_dt, q_str.strip()

@app.route('/history', methods=['GET'])
def history():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT id, create_time, question, result_text FROM hexagram_history ORDER BY id DESC LIMIT 20')
    records = cursor.fetchall()
    conn.close()
    return render_template('history.html', records=records)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)