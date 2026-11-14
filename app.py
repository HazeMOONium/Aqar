"""
Aqar - Real Estate Client Application (Streamlit Web App)
=========================================================
Client for the Aqar database hosted on a REMOTE MySQL server
(sql.freedb.tech - configured in .env, never localhost).

Features (Final Milestone):
  1. Register a user
  2. Add a new user review on a project
  3. View existing reviews of a project
  4. Top 10 projects: highest resale inventory / resale amount / gain over market, by property type
  5. Location of a given development + avg price/sqm and #listings per unit type
  6. All properties in a certain area + avg price/sqm per unit type
  7. Properties in an area by price range + amenities
  8. Top 5 developers by resale listings (avg price/sqm, avg down payment, gain)
  9. All properties filtered by area, property type and contract year
 10. Market analysis (avg installment, avg down payment, #properties, avg discount,
     avg contract age, avg market price) by area and development project

Run:  streamlit run app.py
"""
import hashlib
from datetime import datetime

import pandas as pd
import streamlit as st

from db import get_connection

CURRENT_YEAR = 2026

st.set_page_config(page_title="Aqar | عقار", page_icon="🏘️", layout="wide")

# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
@st.cache_data(ttl=300, show_spinner=False)
def run_query(sql: str, params: tuple = (), key_extra=None) -> pd.DataFrame:
    """Run a read-only query on the remote server and return a DataFrame.

    key_extra: optional extra value folded into the cache key (use it when the
    same SQL/params pair must yield different results for different inputs,
    e.g. an amenities filter that is only encoded in the HAVING clause).
    """
    cn = get_connection()
    try:
        return pd.read_sql(sql, cn, params=params)
    finally:
        cn.close()


def exec_query(sql: str, params: tuple = ()) -> None:
    """Run a write query (INSERT/UPDATE) with commit."""
    cn = get_connection()
    try:
        cur = cn.cursor()
        cur.execute(sql, params)
        cn.commit()
    finally:
        cn.close()


def fmt(df: pd.DataFrame) -> pd.DataFrame:
    """Round numeric columns for nicer display."""
    for c in df.columns:
        series = df[c]
        if hasattr(series, "dtype") and series.dtype.kind == "f":
            df[c] = series.round(0).map(lambda v: f"{v:,.0f}" if pd.notna(v) else "—")
    return df


def egp(v) -> str:
    return f"EGP {v:,.0f}" if pd.notna(v) else "—"


def hash_password(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


# --------------------------------------------------------------------------- #
# Schema notes (documented for the milestone report):
#  * Every listing in PROPERTY is a resale listing (secondary market platform),
#    so "resale inventory" = COUNT of listings and "resale amount" = SUM of the
#    estimated total value (Area x Price_per_m2).
#  * Down_payment column is empty in the dataset -> "required down payment"
#    metric uses Cash_required_now (cash required to take over the contract).
#  * Gain_over_current = gain in EGP over the current market value.
# --------------------------------------------------------------------------- #

PAGES = [
    "🏠 Home",
    "👤 Register",
    "🔑 Login",
    "💬 Project Reviews",
    "🏆 Top 10 Projects",
    "📍 Development Location",
    "🏘️ Properties by Area",
    "🔍 Area + Price + Amenities",
    "🏗️ Top 5 Developers",
    "📋 Browse Properties",
    "💰 Market Analysis",
]

page = st.sidebar.radio("Navigate", PAGES)

# Load basic dimensions once (cached)
PROJECTS = run_query("SELECT DISTINCT Project_name FROM PROPERTY ORDER BY Project_name")
AREAS = run_query("SELECT DISTINCT Location FROM PROPERTY ORDER BY Location")
TYPES = run_query("SELECT DISTINCT Type FROM PROPERTY ORDER BY Type")
YEARS = run_query("SELECT DISTINCT Contract_year FROM PROPERTY ORDER BY Contract_year")
AMENITIES = run_query("SELECT DISTINCT Amenity FROM Amenities ORDER BY Amenity")

with st.sidebar.expander("🌐 Connection"):
    st.caption("Remote MySQL server: `sql.freedb.tech:3306` — DB: `freedb_yiPKYe9K` (config in `.env`)")

# --------------------------------------------------------------------------- #
# Home
# --------------------------------------------------------------------------- #
if page == "🏠 Home":
    st.title("🏘️ Aqar — Real Estate Explorer")
    st.markdown(
        "A client application for the **Aqar** real-estate database hosted on a **remote MySQL server**. "
        "Use the sidebar to navigate between user features and analytical dashboards."
    )
    c1, c2, c3, c4 = st.columns(4)
    n_props = run_query("SELECT COUNT(*) n FROM PROPERTY")["n"][0]
    n_users = run_query("SELECT COUNT(*) n FROM users")["n"][0]
    c1.metric("Listings", f"{n_props:,}")
    c2.metric("Development Projects", f"{len(PROJECTS):,}")
    c3.metric("Areas", f"{len(AREAS):,}")
    c4.metric("Registered Users", f"{n_users:,}")
    st.divider()
    st.markdown(
        "**Quick start** — create an account in *👤 Register*, log in with *🔑 Login*, "
        "then leave a review under *💬 Project Reviews*. All other pages are read-only analytics."
    )

# --------------------------------------------------------------------------- #
# 1) Register a user
# --------------------------------------------------------------------------- #
elif page == "👤 Register":
    st.title("👤 Register a new user")
    with st.form("register", clear_on_submit=True):
        name = st.text_input("Full name")
        email = st.text_input("Email")
        pw = st.text_input("Password", type="password")
        pw2 = st.text_input("Confirm password", type="password")
        ok = st.form_submit_button("Register", use_container_width=True)
    if ok:
        if not name or not email or not pw:
            st.error("All fields are required.")
        elif pw != pw2:
            st.error("Passwords do not match.")
        else:
            try:
                exec_query(
                    "INSERT INTO users (name, email, password_hash) VALUES (%s, %s, %s)",
                    (name, email.strip().lower(), hash_password(pw)),
                )
                st.success(f"✅ User '{name}' registered successfully! You can now log in.")
            except Exception as e:
                if "Duplicate" in str(e) or "1062" in str(e):
                    st.error("This email is already registered.")
                else:
                    st.error(f"Error: {e}")

# --------------------------------------------------------------------------- #
# Login / Logout
# --------------------------------------------------------------------------- #
elif page == "🔑 Login":
    st.title("🔑 Login")
    if "user" in st.session_state:
        st.info(f"Logged in as **{st.session_state.user['name']}** ({st.session_state.user['email']})")
        if st.button("Logout"):
            del st.session_state["user"]
            st.rerun()
    else:
        with st.form("login"):
            email = st.text_input("Email")
            pw = st.text_input("Password", type="password")
            ok = st.form_submit_button("Login", use_container_width=True)
        if ok:
            row = run_query(
                "SELECT user_id, name, password_hash FROM users WHERE email = %s",
                (email.strip().lower(),),
            )
            if row.empty or row["password_hash"][0] != hash_password(pw):
                st.error("Invalid email or password.")
            else:
                st.session_state["user"] = {
                    "id": int(row["user_id"][0]),
                    "name": row["name"][0],
                    "email": email.strip().lower(),
                }
                st.success(f"Welcome back, {row['name'][0]}!")
                st.rerun()

# --------------------------------------------------------------------------- #
# 2) + 3) Project reviews (view + add)
# --------------------------------------------------------------------------- #
elif page == "💬 Project Reviews":
    st.title("💬 Project Reviews")
    project = st.selectbox("Select a development project", PROJECTS["Project_name"], index=None,
                           placeholder="Type to search a project…")

    if project:
        meta = run_query(
            "SELECT Developer, Location FROM DEVELOPMENT_PROJECT WHERE Name = %s", (project,))
        if not meta.empty:
            st.caption(f"Developer: {meta['Developer'][0]} · Location: {meta['Location'][0]}")

        reviews = run_query(
            """SELECT r.review_id, u.name AS Reviewer, r.rating AS Rating,
                      r.comment AS Comment, r.created_at AS Date
               FROM reviews r JOIN users u ON u.user_id = r.user_id
               WHERE r.project_name = %s
               ORDER BY r.created_at DESC""",
            (project,),
        )
        if reviews.empty:
            st.info("No reviews yet for this project — be the first!")
        else:
            c1, c2 = st.columns([1, 3])
            c1.metric("Average rating", f"{reviews['Rating'].mean():.1f} / 5")
            c2.metric("Number of reviews", len(reviews))
            st.table(reviews.drop(columns=["review_id"]))

        st.divider()
        st.subheader("➕ Add your review")
        if "user" not in st.session_state:
            st.warning("Please **log in** first (🔑 Login) to post a review.")
        else:
            with st.form("add_review", clear_on_submit=True):
                rating = st.slider("Rating", 1, 5, 5)
                comment = st.text_area("Comment")
                ok = st.form_submit_button("Submit review", use_container_width=True)
            if ok:
                try:
                    exec_query(
                        "INSERT INTO reviews (user_id, project_name, rating, comment) "
                        "VALUES (%s, %s, %s, %s)",
                        (st.session_state.user["id"], project, rating, comment),
                    )
                    st.success("✅ Review submitted!")
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    if "Duplicate" in str(e) or "1062" in str(e):
                        st.error("You already reviewed this project.")
                    else:
                        st.error(f"Error: {e}")

# --------------------------------------------------------------------------- #
# 4) Top 10 projects by resale metrics, per property type
# --------------------------------------------------------------------------- #
elif page == "🏆 Top 10 Projects":
    st.title("🏆 Top 10 Projects — Resale Performance")
    st.caption("All listings are resale listings. Resale amount = SUM(Area × Price/m²).")

    ptype = st.selectbox("Property type", TYPES["Type"])
    metric = st.radio(
        "Rank by",
        ["Resale inventory (listings)", "Resale amount (EGP)", "Gain over market value (EGP)"],
        horizontal=True,
    )
    order_col = {
        "Resale inventory (listings)": "resale_listings",
        "Resale amount (EGP)": "resale_amount",
        "Gain over market value (EGP)": "avg_gain",
    }[metric]

    df = run_query(
        """SELECT dp.Name AS Project, pr.Location AS Area,
                  COUNT(*) AS resale_listings,
                  SUM(pr.Area * pr.Price_per_m2) AS resale_amount,
                  AVG(pr.Gain_over_current) AS avg_gain
           FROM PROPERTY pr
           JOIN DEVELOPMENT_PROJECT dp ON dp.Name = pr.Project_name
           WHERE pr.Type = %s
           GROUP BY dp.Name, pr.Location
           ORDER BY """ + order_col + """ DESC
           LIMIT 10""",
        (ptype,),
    )
    st.dataframe(fmt(df), use_container_width=True, hide_index=True)
    st.caption(metric + " — highest first.")

# --------------------------------------------------------------------------- #
# 5) Development location + unit-type stats
# --------------------------------------------------------------------------- #
elif page == "📍 Development Location":
    st.title("📍 Development Location & Unit Types")
    project = st.selectbox("Select a development", PROJECTS["Project_name"], index=None,
                           placeholder="Type to search a development…")
    if project:
        meta = run_query(
            "SELECT Developer, Location FROM DEVELOPMENT_PROJECT WHERE Name = %s", (project,))
        locations = run_query(
            "SELECT DISTINCT Location FROM PROPERTY WHERE Project_name = %s", (project,))
        a1, a2, a3 = st.columns(3)
        if not meta.empty:
            a1.metric("Developer", meta["Developer"][0][:30])
        a2.metric("Area", ", ".join(locations["Location"].astype(str).tolist()[:2]) or "—")
        total = run_query("SELECT COUNT(*) n FROM PROPERTY WHERE Project_name = %s", (project,))
        a3.metric("Listings", f"{total['n'][0]:,}")

        st.subheader("Unit types in this development")
        df = run_query(
            """SELECT Type AS `Unit type`,
                      COUNT(*) AS `Listings`,
                      AVG(Price_per_m2) AS `Avg price / sqm (EGP)`
               FROM PROPERTY
               WHERE Project_name = %s
               GROUP BY Type
               ORDER BY `Listings` DESC""",
            (project,),
        )
        if df.empty:
            st.info("No listings found for this development.")
        else:
            st.dataframe(fmt(df), use_container_width=True, hide_index=True)
            st.bar_chart(df.set_index("Unit type")["Avg price / sqm (EGP)"])

        sample = run_query(
            """SELECT ID, Location, Type, Bedrooms, Bathrooms, Area, Price_per_m2,
                      Completion, Delivery, Contract_year
               FROM PROPERTY WHERE Project_name = %s LIMIT 10""",
            (project,),
        )
        st.subheader("Sample listings")
        st.dataframe(fmt(sample), use_container_width=True, hide_index=True)

# --------------------------------------------------------------------------- #
# 6) All properties in an area + avg price/sqm per unit type
# --------------------------------------------------------------------------- #
elif page == "🏘️ Properties by Area":
    st.title("🏘️ Properties by Area")
    area = st.selectbox("Select area", AREAS["Location"], index=None,
                        placeholder="e.g. التجمع الخامس")
    if area:
        n = run_query("SELECT COUNT(*) n FROM PROPERTY WHERE Location = %s", (area,))
        st.metric("Listings in area", f"{n['n'][0]:,}")

        st.subheader("Average price / sqm per unit type")
        df = run_query(
            """SELECT Type AS `Unit type`,
                      COUNT(*) AS `Listings`,
                      AVG(Price_per_m2) AS `Avg price / sqm (EGP)`,
                      AVG(Area * Price_per_m2) AS `Avg total price (EGP)`
               FROM PROPERTY WHERE Location = %s
               GROUP BY Type ORDER BY `Listings` DESC""",
            (area,),
        )
        st.dataframe(fmt(df), use_container_width=True, hide_index=True)
        st.bar_chart(df.set_index("Unit type")["Avg price / sqm (EGP)"])

        st.subheader("All listings in this area")
        props = run_query(
            """SELECT ID, Project_name AS Project, Type, Bedrooms, Bathrooms, Area,
                      Price_per_m2, Area * Price_per_m2 AS `Est. total price`,
                      Cash_required_now, Annual_installment, Completion, Delivery, Contract_year
               FROM PROPERTY WHERE Location = %s ORDER BY Price_per_m2""",
            (area,),
        )
        st.dataframe(fmt(props), use_container_width=True, hide_index=True, height=500)

# --------------------------------------------------------------------------- #
# 7) Area + price range + amenities
# --------------------------------------------------------------------------- #
elif page == "🔍 Area + Price + Amenities":
    st.title("🔍 Search by Area, Price Range & Amenities")
    st.caption("Price = estimated total value of the unit (Area × Price/m²).")

    c1, c2 = st.columns(2)
    area = c1.selectbox("Area", AREAS["Location"], index=None)
    amenities = c2.multiselect("Required amenities", AMENITIES["Amenity"])

    bounds = run_query(
        "SELECT MIN(Area * Price_per_m2) lo, MAX(Area * Price_per_m2) hi FROM PROPERTY")
    lo, hi = int(float(bounds["lo"][0])), int(float(bounds["hi"][0]))
    c1, c2 = st.columns(2)
    pmin = c1.slider("Min price (EGP)", lo, hi, lo, step=50_000)
    pmax = c2.slider("Max price (EGP)", lo, hi, hi, step=50_000)

    if area and pmin <= pmax:
        base_cols = """pr.ID, pr.Project_name AS Project, pr.Type, pr.Bedrooms,
                       pr.Area, pr.Price_per_m2, pr.Area * pr.Price_per_m2 AS `Total price`,
                       pr.Cash_required_now, pr.Annual_installment"""
        group_cols = """pr.ID, pr.Project_name, pr.Type, pr.Bedrooms, pr.Area,
                        pr.Price_per_m2, pr.Cash_required_now, pr.Annual_installment"""
        params = list(amenities)  # JOIN placeholders come first in the SQL text
        # Two joins on Amenities:
        #  - `am`  (restricted to the selected amenities) -> only used by HAVING
        #    so the filter means "has all selected amenities"
        #  - `amx` (unrestricted) -> feeds GROUP_CONCAT, so the table always
        #    shows each listing's FULL amenity list, not just the selected ones
        on_clause = ""
        filter_join = ""
        if amenities:
            on_clause = " AND am.Amenity IN (" + ", ".join(["%s"] * len(amenities)) + ")"
            filter_join = f" LEFT JOIN Amenities am ON am.Property_ID = pr.ID{on_clause}"
        sql = (f"""SELECT {base_cols},
                       GROUP_CONCAT(DISTINCT amx.Amenity SEPARATOR '، ') AS Amenities
                 FROM PROPERTY pr{filter_join}
                 LEFT JOIN Amenities amx ON amx.Property_ID = pr.ID
                 WHERE pr.Location = %s AND pr.Area * pr.Price_per_m2 BETWEEN %s AND %s
                 GROUP BY {group_cols}""")
        params += [area, pmin, pmax]
        if amenities:  # "has all selected amenities" filter
            sql += "\nHAVING COUNT(DISTINCT am.Amenity) = %s"
            params.append(len(amenities))
        sql += "\nORDER BY `Total price`"
        df = run_query(sql, tuple(params), key_extra=tuple(sorted(amenities)))
        if df.empty:
            st.warning("No listings match these criteria.")
        else:
            st.success(f"{len(df)} matching listings")
            st.dataframe(fmt(df), use_container_width=True, hide_index=True, height=450)

# --------------------------------------------------------------------------- #
# 8) Top 5 developers by resale listings
# --------------------------------------------------------------------------- #
elif page == "🏗️ Top 5 Developers":
    st.title("🏗️ Top 5 Developers — Resale Market")
    df = run_query(
        """SELECT dp.Developer AS Developer,
                  COUNT(*) AS `Resale listings`,
                  AVG(pr.Price_per_m2) AS `Avg price / sqm (EGP)`,
                  AVG(pr.Cash_required_now) AS `Avg required down payment (EGP)`,
                  AVG(pr.Gain_over_current) AS `Avg gain over market (EGP)`
           FROM PROPERTY pr
           JOIN DEVELOPMENT_PROJECT dp ON dp.Name = pr.Project_name
           GROUP BY dp.Developer
           ORDER BY `Resale listings` DESC
           LIMIT 5""")
    st.dataframe(fmt(df), use_container_width=True, hide_index=True)
    st.bar_chart(df.set_index("Developer")["Resale listings"])
    st.caption("Down payment = Cash_required_now (cash required to take over the contract).")

# --------------------------------------------------------------------------- #
# 9) Browse properties: area, property type, contract year
# --------------------------------------------------------------------------- #
elif page == "📋 Browse Properties":
    st.title("📋 Browse Properties")
    c1, c2, c3 = st.columns(3)
    area = c1.selectbox("Area (all)", ["— All —"] + AREAS["Location"].tolist())
    ptype = c2.selectbox("Property type (all)", ["— All —"] + TYPES["Type"].tolist())
    years = ["— All —"] + [str(int(y)) for y in YEARS["Contract_year"].dropna()]
    year = c3.selectbox("Contract year (all)", years)

    where, params = [], []
    if area != "— All —":
        where.append("Location = %s"); params.append(area)
    if ptype != "— All —":
        where.append("Type = %s"); params.append(ptype)
    if year != "— All —":
        where.append("Contract_year = %s"); params.append(int(year))
    sql = """SELECT ID, Project_name AS Project, Location AS Area, Type, Bedrooms, Bathrooms,
                    Area AS `Area (sqm)`, Price_per_m2, Area * Price_per_m2 AS `Est. total price`,
                    Contract_year, Completion, Delivery, Finishing
             FROM PROPERTY""" + (" WHERE " + " AND ".join(where) if where else "") + """
             ORDER BY ID LIMIT 300"""
    df = run_query(sql, tuple(params))
    st.caption(f"Showing {len(df)} listings (max 300)")
    st.dataframe(fmt(df), use_container_width=True, hide_index=True, height=520)

# --------------------------------------------------------------------------- #
# 10) Market analysis by area & development project
# --------------------------------------------------------------------------- #
elif page == "💰 Market Analysis":
    st.title("💰 Market Analysis — by Area & Development Project")
    df = run_query(
        f"""SELECT pr.Location AS Area, pr.Project_name AS Project,
                   COUNT(*) AS `Properties`,
                   AVG(pr.Annual_installment) AS `Avg installment price (EGP/yr)`,
                   AVG(pr.Cash_required_now) AS `Avg down payment (EGP)`,
                   AVG(pr.Gain_over_current) AS `Avg discount over market (EGP)`,
                   AVG({CURRENT_YEAR} - pr.Contract_year) AS `Avg contract age (yrs)`,
                   AVG(pr.Area * pr.Price_per_m2) AS `Avg market price (EGP)`
            FROM PROPERTY pr
            GROUP BY pr.Location, pr.Project_name
            ORDER BY `Properties` DESC""")
    st.dataframe(fmt(df), use_container_width=True, hide_index=True, height=560)
    st.caption(f"Contract age measured relative to {CURRENT_YEAR}. "
               "Discount = Gain_over_current (gain in EGP vs current market value).")

st.sidebar.divider()
st.sidebar.caption(f"Logged in: {st.session_state.user['name']}" if "user" in st.session_state
                   else "Not logged in — required to post reviews.")
