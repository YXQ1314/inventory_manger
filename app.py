import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
from supabase import create_client, Client  # 新增

# ---------------------- Supabase 配置 ----------------------
SUPABASE_URL = "https://rlydmitrxpmlsalqcent.supabase.co"
SUPABASE_KEY = "sb_publishable_1c_qAkFVr8uPMMX5SDUs6A_ta9b5lCG"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# ---------------------- 配置 ----------------------
if "APP_PASSWORD" not in st.session_state:
    st.session_state.APP_PASSWORD = "123456"

VERIFY_INFO = {
    "birthday": "2004.5.23",
    "school": "沿河中等职业学校"
}

UNIT_OPTIONS = [
    "个", "台", "部", "张", "把", "双", "斤", "颗", "根", "条",
    "箱", "桶", "包", "袋", "盒", "卷", "扇", "盏"
]

CATEGORY_OPTIONS = ["文具", "工具", "电子设备", "耗材", "器材", "其他"]
# ---------------------- 会话状态初始化 ----------------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "show_change_pwd" not in st.session_state:
    st.session_state.show_change_pwd = False

if "pwd_verified" not in st.session_state:
    st.session_state.pwd_verified = False

# ---------------------- 云端同步函数 ----------------------
def load_inventory_from_supabase():
    response = supabase.table("inventory").select("*").execute()
    data = response.data
    for row in data:
        room = row["room"]
        lyr = row["layer"]
        name = row["name"]
        cate = row["category"]
        qty = row["quantity"]
        unit = row["unit"]
        letter = lyr[0]
        items = st.session_state.inventory[room][letter][lyr]
        items.append({"name": name, "cate": cate, "qty": qty, "unit": unit, "img": None})

def save_inventory_to_supabase(room):
    supabase.table("inventory").delete().eq("room", room).execute()
    for ltr in [chr(ord('A')+i) for i in range(26)]:
        for j in range(1,11):
            lyr = f"{ltr}{j}"
            its = st.session_state.inventory[room][ltr][lyr]
            for it in its:
                supabase.table("inventory").insert({
                    "room": room, "layer": lyr, "name": it["name"],
                    "category": it.get("cate", "无分类"), "quantity": it["qty"], "unit": it["unit"]
                }).execute()

def save_log_to_supabase(operator, action, layer, name, quantity, reason):
    supabase.table("operation_log").insert({
        "operator": operator, "action": action, "layer": layer,
        "name": name, "quantity": quantity, "reason": reason
    }).execute()

# 初始化库存并加载云端数据
if "inventory" not in st.session_state:
    st.session_state.inventory = {
        "康养系库房": {chr(ord('A')+i): {f"{chr(ord('A')+i)}{j}": [] for j in range(1, 11)} for i in range(26)},
        "护理系库房": {chr(ord('A')+i): {f"{chr(ord('A')+i)}{j}": [] for j in range(1, 11)} for i in range(26)}
    }
    load_inventory_from_supabase()

# ------------------------------------------------

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "show_change_pwd" not in st.session_state:
    st.session_state.show_change_pwd = False

if "pwd_verified" not in st.session_state:
    st.session_state.pwd_verified = False

if "current_page" not in st.session_state:
    st.session_state.current_page = "home"

# 记住位置
if "last_room" not in st.session_state:
    st.session_state.last_room = "康养系库房"
if "last_letter" not in st.session_state:
    st.session_state.last_letter = "A"
if "last_layer" not in st.session_state:
    st.session_state.last_layer = "A1"

if "inventory" not in st.session_state:
    st.session_state.inventory = {
        "康养系库房": {chr(ord('A') + i): {f"{chr(ord('A') + i)}{j}": [] for j in range(1, 11)} for i in range(26)},
        "护理系库房": {chr(ord('A') + i): {f"{chr(ord('A') + i)}{j}": [] for j in range(1, 11)} for i in range(26)}
    }

if "operation_log" not in st.session_state:
    st.session_state.operation_log = []

if "operator_name" not in st.session_state:
    st.session_state.operator_name = ""

if "return_selected_name" not in st.session_state:
    st.session_state.return_selected_name = ""

# 入库表单重置标记
if "reset_in_form" not in st.session_state:
    st.session_state.reset_in_form = False


# ---------------------- 日志记录 ----------------------
def add_log(operation, layer, name, qty, reason=""):
    time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.operation_log.append({
        "时间": time_str,
        "操作人员": st.session_state.operator_name,
        "操作": operation,
        "位置": layer,
        "物品": name,
        "数量": qty,
        "原因": reason
    })


# ---------------------- 创作者显示 ----------------------
st.markdown(body="""
<div style="text-align: center; font-size:12px; color:#888; padding: 15px 0;">
创作人：杨旭强 | 专业库房管理系统 | 电话号码:19185676759
</div>
""", unsafe_allow_html=True)
# ---------------------- 登录 / 修改密码 ----------------------
if not st.session_state.authenticated:
    st.title("🔐 三中心库房管理系统登录")

    if not st.session_state.show_change_pwd:
        pwd = st.text_input("请输入密码", type="password")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("登录", use_container_width=True, type="primary"):
                if pwd == st.session_state.APP_PASSWORD:
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("密码错误")
        with col2:
            if st.button("修改密码", use_container_width=True):
                st.session_state.show_change_pwd = True
                st.session_state.pwd_verified = False
                st.rerun()
    else:
        st.subheader("修改密码")

        if not st.session_state.pwd_verified:
            st.markdown("### 请先完成身份验证")
            birthday = st.text_input("你的出生日期是？（格式：YYYY-MM-DD）")
            school = st.text_input("你以前的学校是？")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("下一步验证", use_container_width=True, type="primary"):
                    if birthday == VERIFY_INFO["birthday"] and school == VERIFY_INFO["school"]:
                        st.session_state.pwd_verified = True
                        st.success("验证成功！请设置新密码")
                        st.rerun()
                    else:
                        st.error("答案不正确，无法修改密码")
            with col2:
                if st.button("返回登录", use_container_width=True):
                    st.session_state.show_change_pwd = False
                    st.rerun()

        else:
            st.markdown("### 设置新密码")
            new_pwd = st.text_input("请输入新密码", type="password")
            confirm_pwd = st.text_input("请再次确认新密码", type="password")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("确认修改密码", use_container_width=True, type="primary"):
                    if not new_pwd:
                        st.error("新密码不能为空")
                    elif new_pwd != confirm_pwd:
                        st.error("两次输入密码不一致")
                    else:
                        st.session_state.APP_PASSWORD = new_pwd
                        st.success("密码修改成功！返回登录页面")
                        st.session_state.show_change_pwd = False
                        st.session_state.pwd_verified = False
                        st.rerun()
            with col2:
                if st.button("取消返回", use_container_width=True):
                    st.session_state.show_change_pwd = False
                    st.session_state.pwd_verified = False
                    st.rerun()
    st.stop()


# ---------------------- 通用 ----------------------
def back_button(target_page):
    cols = st.columns([10, 1])
    with cols[1]:
        if st.button("返回上一页", use_container_width=True):
            st.session_state.current_page = target_page
            st.rerun()


# ---------------------- 主页 ----------------------
if st.session_state.current_page == "home":
    st.title("📦 专业库房管理系统")
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        if st.button("📥 入库", use_container_width=True, type="primary"):
            st.session_state.current_page = "select_location_in"
            st.session_state.reset_in_form = True
    with col2:
        if st.button("📤 出库", use_container_width=True):
            st.session_state.current_page = "select_location_out"
    with col3:
        if st.button("♻️ 归还", use_container_width=True):
            st.session_state.current_page = "select_location_return"
    with col4:
        if st.button("📊 数据总库", use_container_width=True):
            st.session_state.current_page = "select_room_view"
    with col5:
        if st.button("📋 操作日志", use_container_width=True):
            st.session_state.current_page = "log_page"

    with st.sidebar:
        if st.button("退出登录", use_container_width=True, type="secondary"):
            st.session_state.authenticated = False
            st.rerun()

# ---------------------- 日志页面 + 导出CSV ----------------------
elif st.session_state.current_page == "log_page":
    st.title("📊 操作日志")
    back_button("home")
    # 新增：清空云端日志按钮
    if st.button("🗑️ 清空所有云端操作日志", type="secondary", use_container_width=True):
        try:
            supabase.table("operation_log").delete().neq("id", 0).execute()
            st.success("✅ 所有云端操作日志已清空！页面将刷新...")
            st.rerun()
        except Exception as e:
            st.error(f"❌ 清空失败：{e}")
    # 从云端加载操作日志
    try:
        log_response = supabase.table("operation_log")\
            .select("*")\
            .order("created_at", desc=True)\
            .execute()
        cloud_logs = log_response.data

        if cloud_logs:
            df = pd.DataFrame(cloud_logs)
            # 只展示需要的列，让界面更清爽
            df = df[["created_at", "operator", "action", "layer", "name", "quantity", "reason"]]
            st.dataframe(df, use_container_width=True)

            # 导出CSV
            csv_bytes = df.to_csv(index=False, encoding="utf-8-sig")
            st.download_button(
                label="📥 导出操作日志(CSV)",
                data=csv_bytes,
                file_name=f"操作日志_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        else:
            st.info("暂无云端操作记录")
    except Exception as e:
        st.error(f"加载云端日志失败: {e}")
        # 失败时 fallback 到展示本地日志
        if st.session_state.operation_log:
            df = pd.DataFrame(st.session_state.operation_log)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("暂无操作记录")

# ---------------------- 入库选择位置（记住上次选择） ----------------------
elif st.session_state.current_page == "select_location_in":
    st.title("📥 入库 - 选择位置")
    back_button("home")

    col1, col2, col3 = st.columns(3)
    with col1:
        room = st.selectbox("库房", ["康养系库房", "护理系库房"],
                            index=["康养系库房", "护理系库房"].index(st.session_state.last_room))
    with col2:
        letter = st.selectbox("货架", [chr(ord('A') + i) for i in range(26)],
                              index=[chr(ord('A') + i) for i in range(26)].index(st.session_state.last_letter))
    with col3:
        layer = st.selectbox("层号", [f"{letter}{j}" for j in range(1, 11)],
                             index=[f"{letter}{j}" for j in range(1, 11)].index(st.session_state.last_layer))

    if st.button("✅ 进入入库", use_container_width=True, type="primary"):
        st.session_state.last_room = room
        st.session_state.last_letter = letter
        st.session_state.last_layer = layer
        st.session_state.current_page = "in_form"
        st.session_state.reset_in_form = True
        st.rerun()

# ---------------------- 入库页面（已修复报错：入库后自动清空表单） ----------------------
elif st.session_state.current_page == "in_form":
    room = st.session_state.last_room
    letter = st.session_state.last_letter
    layer = st.session_state.last_layer
    items = st.session_state.inventory[room][letter][layer]

    st.title(f"📥 入库 - {layer}")
    back_button("select_location_in")

    st.session_state.operator_name = st.text_input("👤 工作人员姓名", value=st.session_state.operator_name)
    if not st.session_state.operator_name:
        st.warning("请填写姓名")
        st.stop()

    st.markdown("---")
    st.markdown("### ➕ 新增物品")

    # 控制表单是否重置
    reset_form = st.session_state.get("reset_in_form", False)

    # 表单值：如果需要重置，就清空；否则保持原样
    name = st.text_input("物品名称", value="" if reset_form else None)
    qty = st.number_input("入库数量", min_value=1, value=1 if reset_form else None)

    # 重置后，把标记关掉
    if reset_form:
        st.session_state["reset_in_form"] = False

    cate = st.selectbox("分类", CATEGORY_OPTIONS)
    unit = st.selectbox("单位", UNIT_OPTIONS)
    img = st.camera_input("📸 拍照上传")

    if st.button("✅ 确认入库", use_container_width=True, type="primary"):
        if not name:
            st.error("请填写物品名称")
        else:
            exist = False
            for i in items:
                if i["name"] == name:
                    i["qty"] += qty
                    exist = True
                    break
            if not exist:
                items.append({
                    "name": name, "cate": cate, "qty": qty,
                    "unit": unit, "img": img.getvalue() if img else None
                })
            add_log("入库", layer, name, qty)
            save_inventory_to_supabase(room)
            save_log_to_supabase(operator="", action="入库", layer=layer, name=name, quantity=qty, reason="入库")
            st.success("入库成功！")
            # ✅ 只设置重置标记，不直接修改 session_state
            st.session_state["reset_in_form"] = True
            st.rerun()

    st.markdown("---")
    for item in items:
        st.write(f"**{item['name']}**｜{item['qty']}{item['unit']}")
        if item.get("img"):
            st.image(item["img"], width=100)
        st.markdown("---")

# ---------------------- 出库选择位置 ----------------------
elif st.session_state.current_page == "select_location_out":
    st.title("📤 出库 - 选择位置")
    back_button("home")

    col1, col2, col3 = st.columns(3)
    with col1:
        room = st.selectbox("库房", ["康养系库房", "护理系库房"],
                            index=["康养系库房", "护理系库房"].index(st.session_state.last_room))
    with col2:
        letter = st.selectbox("货架", [chr(ord('A') + i) for i in range(26)],
                              index=[chr(ord('A') + i) for i in range(26)].index(st.session_state.last_letter))
    with col3:
        layer = st.selectbox("层号", [f"{letter}{j}" for j in range(1, 11)],
                             index=[f"{letter}{j}" for j in range(1, 11)].index(st.session_state.last_layer))

    if st.button("✅ 进入出库", use_container_width=True, type="primary"):
        st.session_state.last_room = room
        st.session_state.last_letter = letter
        st.session_state.last_layer = layer
        st.session_state.current_page = "out_ops"
        st.rerun()

# ---------------------- 出库页面 ----------------------
elif st.session_state.current_page == "out_ops":
    room = st.session_state.last_room
    letter = st.session_state.last_letter
    layer = st.session_state.last_layer
    items = st.session_state.inventory[room][letter][layer]

    st.title(f"📤 出库 - {layer}")
    back_button("select_location_out")

    st.session_state.operator_name = st.text_input("👤 工作人员姓名", value=st.session_state.operator_name)
    if not st.session_state.operator_name:
        st.warning("请填写姓名")
        st.stop()

    reason = st.selectbox(
        "出库原因",
        ["上课需要用", "比赛需要用", "借用", "其他"],
        index=0
    )

    if not items:
        st.info("暂无物品")
    else:
        for i, item in enumerate(items):
            st.markdown(f"### {item['name']}（库存：{item['qty']}{item['unit']}）")
            if item.get("img"):
                st.image(item["img"], width=100)
            out_num = st.number_input(f"出库数量：{item['name']}", min_value=1, max_value=item['qty'], value=1,
                                      key=f"out_{i}")
            if st.button(f"✅ 确认出库 {item['name']}", key=f"btn_out_{i}"):
                item["qty"] -= out_num
                add_log("出库", layer, item['name'], -out_num, reason)
                if item["qty"] == 0:
                    del items[i]
                    save_inventory_to_supabase(room)
                    save_log_to_supabase(operator="", action="出库", layer=layer, name=item['name'], quantity=out_num,
                                         reason="出库")
                st.success(f"出库成功：{out_num}{item['unit']}")
                st.rerun()
            st.markdown("---")# ---------------------- 归还选择位置 ----------------------
elif st.session_state.current_page == "select_location_return":
    st.title("♻️ 归还 - 选择位置")
    back_button("home")

    col1, col2, col3 = st.columns(3)
    with col1:
        room = st.selectbox("库房", ["康养系库房", "护理系库房"],
                           index=["康养系库房", "护理系库房"].index(st.session_state.last_room))
    with col2:
        letter = st.selectbox("货架", [chr(ord('A')+i) for i in range(26)],
                              index=[chr(ord('A')+i) for i in range(26)].index(st.session_state.last_letter))
    with col3:
        layer = st.selectbox("层号", [f"{letter}{j}" for j in range(1, 11)],
                             index=[f"{letter}{j}" for j in range(1, 11)].index(st.session_state.last_layer))

    if st.button("✅ 进入归还", use_container_width=True, type="primary"):
        st.session_state.last_room = room
        st.session_state.last_letter = letter
        st.session_state.last_layer = layer
        st.session_state.current_page = "return_form"
        st.rerun()

# ---------------------- 归还页面（最终锁死版） ----------------------
elif st.session_state.current_page == "return_form":
    room = st.session_state.last_room
    letter = st.session_state.last_letter
    layer = st.session_state.last_layer
    items = st.session_state.inventory[room][letter][layer]

    st.title(f"♻️ 归还 - {layer}")
    back_button("select_location_return")

    st.session_state.operator_name = st.text_input("👤 工作人员姓名", value=st.session_state.operator_name)
    if not st.session_state.operator_name:
        st.warning("请填写姓名")
        st.stop()

    recent_items = []
    for log in reversed(st.session_state.operation_log):
        if log["操作"] == "出库" and log["位置"] == layer:
            recent_items.append({"name": log["物品"], "qty": abs(log["数量"])})
            if len(recent_items) >= 3:
                break

    if recent_items:
        st.markdown("**🔁 最近出库（点击归还）**")
        cols = st.columns(len(recent_items))
        for i, (col, it) in enumerate(zip(cols, recent_items)):
            with col:
                if st.button(f"{it['name']}（最多还{it['qty']}）", key=f"q_{i}"):
                    st.session_state.return_selected_name = it['name']
                    st.rerun()

    return_name = st.text_input("归还物品名称", value=st.session_state.return_selected_name)

    total_out = 0
    total_returned = 0
    for log in st.session_state.operation_log:
        if log["位置"] == layer and log["物品"] == return_name:
            if log["操作"] == "出库":
                total_out += abs(log["数量"])
            elif log["操作"] == "归还":
                total_returned += log["数量"]

    max_return = total_out - total_returned

    if max_return < 1:
        st.info("ℹ️ 该物品已全部归还，无法再归还")
        return_qty = 0
    else:
        return_qty = st.number_input(
            "归还数量",
            min_value=1,
            max_value=max_return,
            value=1
        )

    return_reason = st.selectbox("归还原因", ["上课归还", "比赛归还", "借用归还", "其他"])

    if st.button("✅ 确认归还", use_container_width=True, type="primary"):
        if not return_name:
            st.error("请填写或选择归还物品")
        elif max_return < 1:
            st.error("已全部归还，不允许再归还！")
        elif return_qty > max_return:
            st.error(f"最多只能归还 {max_return} 个")
        else:
            exist = False
            for i in items:
                if i["name"] == return_name:
                    i["qty"] += return_qty
                    exist = True
                    break
            if not exist:
                items.append({"name": return_name, "cate": "耗材", "qty": return_qty, "unit": "个", "img": None})
            add_log("归还", layer, return_name, return_qty, return_reason)
            save_inventory_to_supabase(room)
            save_log_to_supabase(operator="", action="归还", layer=layer, name=return_name, quantity=return_qty,
                                 reason="归还")
            st.success("归还成功！")
            st.session_state.return_selected_name = ""
            st.rerun()

    st.markdown("---")
    st.markdown(f"### 📦 {layer} 物品列表")
    if not items:
        st.info("暂无物品")
    else:
        for item in items:
            st.write(f"**{item['name']}**｜{item.get('cate','无分类')}｜{item['qty']}{item['unit']}")
            if item.get("img"):
                st.image(item["img"], width=100)
            st.markdown("---")

# ---------------------- 数据总库 ----------------------
elif st.session_state.current_page == "select_room_view":
    st.title("📊 数据总库")
    back_button("home")
    room = st.radio("库房", ["康养系库房", "护理系库房"],
                    index=["康养系库房", "护理系库房"].index(st.session_state.last_room))
    if st.button("✅ 查看", use_container_width=True, type="primary"):
        st.session_state.last_room = room
        st.session_state.current_page = "all_view"
        st.rerun()

elif st.session_state.current_page == "all_view":
    room = st.session_state.last_room
    st.title(f"📊 库存总表 - {room}")
    back_button("select_room_view")

    all_items = []
    for ltr in [chr(ord('A')+i) for i in range(26)]:
        for j in range(1,11):
            lyr = f"{ltr}{j}"
            its = st.session_state.inventory[room][ltr][lyr]
            for it in its:
                all_items.append({
                    "位置": lyr,
                    "物品名称": it["name"],
                    "分类": it.get("cate", "无分类"),
                    "数量": it["qty"],
                    "单位": it["unit"]
                })
                st.write(f"📍{lyr}｜{it['name']}｜{it.get('cate','无分类')}｜{it['qty']}{it['unit']}")
                if it.get("img"):
                    st.image(it["img"], width=100)
                st.markdown("---")

    if all_items:
        df_export = pd.DataFrame(all_items)
        # 导出 CSV（无需安装 openpyxl）
        csv_bytes = df_export.to_csv(index=False, encoding="utf-8-sig")
        st.download_button(
            label="📥 导出库存总表(CSV)",
            data=csv_bytes,
            file_name=f"库存总表_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )