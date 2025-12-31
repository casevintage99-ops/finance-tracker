import plotly.express as px
import streamlit as st
import pandas as pd
from datetime import date
import os

# ✅ TARUH CSS DI SINI
st.markdown("""
<style>
.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
    max-width: 980px;
}

[data-testid="stVerticalBlockBorderWrapper"] {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 18px;
    padding: 20px 20px 8px 20px;
    box-shadow: 0 12px 32px rgba(0,0,0,0.35);
    margin-bottom: 20px;
}

.stButton > button,
.stDownloadButton > button {
    border-radius: 14px !important;
    padding: 0.55rem 1.1rem !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
}

input, textarea, select {
    border-radius: 12px !important;
}
</style>
""", unsafe_allow_html=True)
# ✅ SAMPAI SINI

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

st.markdown("""
<h1 style="margin-bottom:0.2rem;">💸 Finance Tracker</h1>
<p style="opacity:0.7; margin-top:0;">simple • clean • monthly</p>
""", unsafe_allow_html=True)


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
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("📊 Ringkasan Bulanan")

    if df.empty:
        st.info("Belum ada data")
    else:
        # pilih bulan
        df["bulan"] = pd.to_datetime(df["tanggal"]).dt.to_period("M").astype(str)
        bulan = st.selectbox(
            "Pilih bulan",
            sorted(df["bulan"].unique(), reverse=True)
        )
        df_bulan = df[df["bulan"] == bulan].copy()

        # total
        total = int(df_bulan["nominal"].sum())
        st.metric("Total Pengeluaran", f"Rp {total:,}".replace(",", "."))

        # ===== 🎯 BUDGET =====
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
            for k in ["Makan", "Transport", "Belanja", "Tagihan", "Hiburan", "Lainnya"]:
                budgets[k] = st.number_input(
                    f"Budget {k} (Rp)",
                    min_value=0,
                    step=50000,
                    value=int(default_budget.get(k, 0)),
                    key=f"budget_{bulan}_{k}"
                )

        spent = df_bulan.groupby("kategori")["nominal"].sum().to_dict()

        for k in ["Makan", "Transport", "Belanja", "Tagihan", "Hiburan", "Lainnya"]:
            s = int(spent.get(k, 0))
            b = int(budgets.get(k, 0))

            st.write(f"**{k}** — Rp {s:,}".replace(",", ".") + f" / Rp {b:,}".replace(",", "."))

            if b <= 0:
                st.progress(0)
                st.caption("Set budget dulu ya.")
            else:
                ratio = s / b
                st.progress(min(ratio, 1.0))
                st.caption(f"{int(ratio*100)}% terpakai")
                if ratio >= 1:
                    st.warning(f"{k}: over budget! 😵")

        st.divider()

        # ===== 🍩 DONUT CHART =====
        st.subheader("🍩 Komposisi Pengeluaran")
        by_kat = df_bulan.groupby("kategori", as_index=False)["nominal"].sum()

        fig = px.pie(by_kat, names="kategori", values="nominal", hole=0.55)
        fig.update_traces(textinfo="percent+label")
        st.plotly_chart(fig, use_container_width=True)

        st.divider()

        # ===== 🗑️ HAPUS TRANSAKSI =====
        st.subheader("🗑️ Hapus Transaksi (kalau salah input)")

        df_view = df_bulan.copy()
        df_view["deskripsi"] = df_view["deskripsi"].fillna("")

        # tampil list + tombol hapus per baris
        for i, row in df_view.sort_values("tanggal", ascending=False).reset_index(drop=True).iterrows():
            c1, c2, c3, c4, c5 = st.columns([2, 2, 3, 2, 1])
            c1.write(str(row["tanggal"]))
            c2.write(row["kategori"])
            c3.write(row["deskripsi"])
            c4.write(f"Rp {int(row['nominal']):,}".replace(",", "."))
            if c5.button("🗑️", key=f"del_{bulan}_{i}"):
                mask = (
                    (df["tanggal"] == row["tanggal"]) &
                    (df["kategori"] == row["kategori"]) &
                    (df["deskripsi"].fillna("") == row["deskripsi"]) &
                    (df["nominal"] == row["nominal"])
                )
                idx = df[mask].index
                if len(idx) > 0:
                    df = df.drop(idx[0]).reset_index(drop=True)
                    save_data(df)
                    st.success("Transaksi terhapus ✅")
                    st.rerun()
                else:
                    st.warning("Data tidak ditemukan untuk dihapus.")

        st.divider()

        # ===== 📋 TABEL + DOWNLOAD CSV =====
        st.subheader("📋 Data Bulan Ini")

        st.dataframe(
            df_bulan[["tanggal", "kategori", "deskripsi", "nominal"]].sort_values("tanggal", ascending=False),
            use_container_width=True,
            hide_index=True
        )

        st.download_button(
            "⬇️ Download CSV (backup data)",
            data=df.drop(columns=["bulan"], errors="ignore").to_csv(index=False).encode("utf-8"),
            file_name="transaksi.csv",
            mime="text/csv"
        )
