import plotly.express as px
import streamlit as st
import pandas as pd
from datetime import date
import os

st.set_page_config(page_title="Finance Tracker", page_icon="💸", layout="centered")

FILE = "transaksi.csv"

def load_data():
    if os.path.exists(FILE):
        df = pd.read_csv(FILE)
        df["tanggal"] = pd.to_datetime(df["tanggal"]).dt.date
        return df
    return pd.DataFrame(columns=["tanggal", "kategori", "deskripsi", "nominal"])

def save_data(df):
    out = df.copy()
    out["tanggal"] = pd.to_datetime(out["tanggal"]).astype(str)
    out.to_csv(FILE, index=False)

df = load_data()

st.title("💸 Finance Tracker")
st.caption("simple • clean • monthly")

tab1, tab2 = st.tabs(["➕ Input", "📊 Ringkasan"])

with tab1:
    with st.form("input_form", clear_on_submit=True):
        tgl = st.date_input("Tanggal", value=date.today())
        kategori = st.selectbox(
            "Kategori",
            ["Makan", "Transport", "Belanja", "Tagihan", "Hiburan", "Lainnya"]
        )
        deskripsi = st.text_input("Deskripsi")
        nominal = st.number_input("Nominal", min_value=0, step=1000)
        submit = st.form_submit_button("Simpan")

    if submit:
        if nominal <= 0:
            st.warning("Nominal harus > 0")
        else:
            df = pd.concat([df, pd.DataFrame([{
                "tanggal": tgl,
                "kategori": kategori,
                "deskripsi": deskripsi,
                "nominal": nominal
            }])], ignore_index=True)
            save_data(df)
            st.success("Tersimpan ✅")

with tab2:
    st.subheader("📊 Ringkasan Bulanan")

    if df.empty:
        st.info("Belum ada data")
    else:
        df["bulan"] = pd.to_datetime(df["tanggal"]).dt.to_period("M").astype(str)
        bulan = st.selectbox(
            "Pilih bulan",
            sorted(df["bulan"].unique(), reverse=True)
        )

        df_bulan = df[df["bulan"] == bulan].copy()

        # ===== TOTAL =====
        total = int(df_bulan["nominal"].sum())
        st.metric(
            "Total Pengeluaran",
            f"Rp {total:,}".replace(",", ".")
        )

        # ===== 🎯 BUDGET (TARUH DI SINI) =====
        st.subheader("🎯 Budget per Kategori")

        default_budget = {
            "Makan": 1500000,
            "Transport": 500000,
            "Belanja": 500000,
            "Tagihan": 1000000,
            "Hiburan": 300000,
            "Lainnya": 300000,
        }

        with st.expander("Atur budget", expanded=False):
            budgets = {}
            for k in ["Makan","Transport","Belanja","Tagihan","Hiburan","Lainnya"]:
                budgets[k] = st.number_input(
                    f"Budget {k} (Rp)",
                    min_value=0,
                    step=50000,
                    value=int(default_budget[k]),
                    key=f"budget_{bulan}_{k}"
                )

        spent = df_bulan.groupby("kategori")["nominal"].sum().to_dict()

        for k in budgets:
            s = int(spent.get(k, 0))
            b = int(budgets[k])

            st.write(
                f"**{k}** — Rp {s:,}".replace(",", ".")
                + f" / Rp {b:,}".replace(",", ".")
            )

            if b > 0:
                ratio = s / b
                st.progress(min(ratio, 1.0))
                st.caption(f"{int(ratio*100)}% terpakai")
                if ratio >= 1:
                    st.warning(f"{k}: over budget 😵")
            else:
                st.progress(0)
                st.caption("Set budget dulu")

        # ===== 🍩 DONUT CHART =====
        by_kat = df_bulan.groupby("kategori", as_index=False)["nominal"].sum()
        fig = px.pie(by_kat, names="kategori", values="nominal", hole=0.55)
        fig.update_traces(textinfo="percent+label")
        st.plotly_chart(fig, use_container_width=True)

        # ===== 📋 TABEL =====
        st.dataframe(
            df_bulan[["tanggal","kategori","deskripsi","nominal"]]
            .sort_values("tanggal", ascending=False),
            use_container_width=True,
            hide_index=True
        )
