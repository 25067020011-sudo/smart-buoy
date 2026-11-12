"""
SMMB — Smart Marine Monitoring Buoy
Root Entrypoint for Streamlit Community Cloud
Memastikan aplikasi dapat berjalan baik jika "Main file path" diatur sebagai "app.py" maupun "dashboard/app.py".
"""

import os
import sys

dashboard_dir = os.path.join(os.path.dirname(__file__), "dashboard")
if dashboard_dir not in sys.path:
    sys.path.insert(0, dashboard_dir)

dashboard_app = os.path.join(dashboard_dir, "app.py")

if os.path.exists(dashboard_app):
    with open(dashboard_app, "r", encoding="utf-8") as f:
        code = f.read()
    exec(code, globals())
else:
    import streamlit as st
    st.error("File dashboard/app.py tidak ditemukan!")
