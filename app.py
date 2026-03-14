# 强制 UTF-8 放在最开头
import os
os.environ["PYTHONUTF8"] = "1"

import streamlit as st
from supabase import create_client, Client
from PIL import Image
import io

# -------------------------- 把你的信息填在这里 --------------------------
SUPABASE_URL = "https://dbxvhqhgfmychagktnmj.supabase.co"  # 你的 Supabase URL
SUPABASE_KEY = "sb_publishable_Y08Hy7lurYiXVMX3VUoOjw_nW2YZebG"  # 你的可发布密钥
APP_PASSWORD = "123456"  # 你想设置的登录密码
STORAGE_BUCKET = "item-images"  # 把中文桶名改成英文
# ----------------------------------------------------------------------

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Login check
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔐 Inventory Management System Login")
    password = st.text_input("Please enter login password", type="password")
    if st.button("Login"):
        if password == APP_PASSWORD:
            st.session_state.authenticated = True
            st.success("Login successful!")
            st.rerun()
        else:
            st.error("Password error, please try again!")
    st.stop()

# Main interface
st.title("📦 Cloud Inventory Management System")

# Sidebar: category filter
st.sidebar.title("Category Filter")
categories = supabase.table("categories").select("*").execute().data
category_names = ["All"] + [cat["name"] for cat in categories]
selected_category = st.sidebar.selectbox("Select category", category_names)

# Tabs
tab1, tab2, tab3 = st.tabs(["📋 View Inventory", "➕ Add Item", "📊 Statistics"])

with tab1:
    st.subheader("Current Inventory")
    query = supabase.table("items").select("*, categories(name)")
    if selected_category != "All":
        cat_id = next(c["id"] for c in categories if c["name"] == selected_category)
        query = query.eq("category_id", cat_id)
    items = query.execute().data

    if items:
        for item in items:
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"**{item['name']}** | Category: {item['categories']['name']}")
                st.write(f"Desc: {item['description'] or 'None'} | Qty: {item['quantity']}")
            with col2:
                if st.button(f"+ Add", key=f"add_{item['id']}"):
                    new_qty = item["quantity"] + 1
                    supabase.table("items").update({"quantity": new_qty}).eq("id", item["id"]).execute()
                    st.rerun()
            with col3:
                if st.button(f"- Sub", key=f"sub_{item['id']}"):
                    new_qty = max(0, item["quantity"] - 1)
                    supabase.table("items").update({"quantity": new_qty}).eq("id", item["id"]).execute()
                    st.rerun()
    else:
        st.info("No items yet, please add one first.")

with tab2:
    st.subheader("Add New Item")
    item_name = st.text_input("Item Name")
    cat_options = {cat["name"]: cat["id"] for cat in categories}
    selected_cat = st.selectbox("Select Category", list(cat_options.keys()))
    quantity = st.number_input("Quantity", min_value=1, value=1)
    description = st.text_area("Description")
    uploaded_file = st.file_uploader("Upload Photo", type=["png", "jpg", "jpeg"])

    if st.button("Add Item"):
        if item_name:
            new_item = supabase.table("items").insert({
                "name": item_name,
                "category_id": cat_options[selected_cat],
                "quantity": quantity,
                "description": description
            }).execute()
            item_id = new_item.data[0]["id"]

            if uploaded_file:
                image = Image.open(uploaded_file)
                buf = io.BytesIO()
                image.save(buf, format="PNG")
                buf.seek(0)
                supabase.storage.from_(STORAGE_BUCKET).upload(f"{item_id}.png", buf)
            st.success("Item added successfully!")
            st.rerun()
        else:
            st.error("Item name cannot be empty!")

with tab3:
    st.subheader("Inventory Statistics")
    all_items = supabase.table("items").select("*").execute().data
    if all_items:
        total_items = len(all_items)
        total_quantity = sum(item["quantity"] for item in all_items)
        st.metric(label="Total Items", value=total_items)
        st.metric(label="Total Quantity", value=total_quantity)

        cat_stats = {}
        for item in all_items:
            cat_name = next(c["name"] for c in categories if c["id"] == item["category_id"])
            cat_stats[cat_name] = cat_stats.get(cat_name, 0) + item["quantity"]
        st.bar_chart(cat_stats)
    else:
        st.info("No data available for statistics.")