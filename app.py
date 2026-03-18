import streamlit as st
import pandas as pd
import unicodedata
import io
import json as _json
import os as _os
import urllib.parse as _uparse
import xml.etree.ElementTree as _ET
import urllib.request as _ureq
from datetime import datetime, date

try:
    from rapidfuzz import fuzz
except ImportError:
    st.error("Instala rapidfuzz: pip install rapidfuzz"); st.stop()

try:
    from generador_pdf import generar_pdf_individual, generar_pdf_manual, generar_pdf_masivo
    PDF_DISPONIBLE = True
except ImportError:
    PDF_DISPONIBLE = False

st.set_page_config(page_title="SERVIALAFT SAS", page_icon="🛡️",
                   layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
[data-testid="stSidebar"] { background:#0f1b2d; }
[data-testid="stSidebar"] * { color:#e2e8f0 !important; }
[data-testid="stSidebar"] .stRadio > label { display:none; }
[data-testid="stSidebar"] .stRadio label {
    display:flex !important; align-items:center; padding:10px 14px;
    border-radius:8px; margin:2px 0; cursor:pointer; font-size:15px; }
[data-testid="stSidebar"] .stRadio label:hover { background:rgba(255,255,255,0.1); }
.login-wrap { max-width:420px; margin:60px auto 0; padding:40px 36px 32px;
    background:#fff; border-radius:16px; box-shadow:0 4px 32px rgba(0,0,0,0.10); }
.login-title { font-size:26px; font-weight:700; color:#0f1b2d; text-align:center; margin-bottom:4px; }
.login-sub   { font-size:13px; color:#6c757d; text-align:center; margin-bottom:24px; }
.ext-link { display:block; padding:12px 16px; border-radius:10px;
    border:1px solid #e2e8f0; background:#f8faff;
    text-decoration:none !important; margin-bottom:8px; transition:box-shadow .2s; }
.ext-link:hover { box-shadow:0 4px 12px rgba(15,27,45,0.10); }
.ext-title { font-size:14px; font-weight:700; color:#0f1b2d; }
.ext-url   { font-size:11px; color:#2563eb; margin-top:3px; font-family:monospace; }
.metric-box { background:#f8faff; border:1px solid #e2e8f0;
    border-radius:12px; padding:20px 16px; text-align:center; }
.metric-num   { font-size:38px; font-weight:800; color:#0f1b2d; line-height:1; }
.metric-label { font-size:13px; color:#6c757d; margin-top:6px; }
footer { visibility:hidden; } #MainMenu { visibility:hidden; }
</style>
""", unsafe_allow_html=True)

for k, v in {"logged_in":False,"user":None,"menu":"UNIFICADA","logs":[]}.items():
    if k not in st.session_state: st.session_state[k] = v

USUARIOS = {
    "admin":     {"password":"admin123",    "rol":"Administrador","nombre":"Admin Principal"},
    "analista1": {"password":"sarlaft2024", "rol":"Analista",     "nombre":"Laura Gomez"},
    "consultor": {"password":"consulta01",  "rol":"Consultor",    "nombre":"Andres Martinez"},
}

def cargar_listas():
    if _os.path.exists("listas_vinculantes.json"):
        with open("listas_vinculantes.json","r",encoding="utf-8") as f:
            data = _json.load(f)
        rows = []
        for r in data.get("registros",[]):
            nom=r.get("nombre",""); lst=r.get("lista","OFAC SDN")
            prog=", ".join(r.get("programas",[])) or lst
            rows.append({"tipo_id":"N/A","nro_id":"N/A","nombre":nom,"origen":lst,"detalle":prog})
            for doc in r.get("documentos",[]):
                num=doc.get("numero","").strip()
                if num and num!="N/A":
                    rows.append({"tipo_id":doc.get("tipo","DOC"),"nro_id":num,"nombre":nom,"origen":lst,"detalle":prog})
            for aka in r.get("aka",[]):
                if aka: rows.append({"tipo_id":"N/A","nro_id":"N/A","nombre":aka,"origen":lst,"detalle":f"{prog} (AKA)"})
        return pd.DataFrame(rows), True, data.get("meta",{})
    # ── DATOS DEMO — Colombianos reales en listas vinculantes ────────────────
    demo = pd.DataFrame([
        # OFAC SDN — Narcotráfico Colombia
        {"tipo_id":"CC", "nro_id":"19400625","nombre":"PABLO ESCOBAR GAVIRIA","origen":"OFAC SDN","detalle":"NARCOTICS — Cartel de Medellín"},
        {"tipo_id":"CC", "nro_id":"16354146","nombre":"GILBERTO RODRIGUEZ OREJUELA","origen":"OFAC SDN","detalle":"NARCOTICS — Cartel de Cali"},
        {"tipo_id":"CC", "nro_id":"16354147","nombre":"MIGUEL ANGEL RODRIGUEZ OREJUELA","origen":"OFAC SDN","detalle":"NARCOTICS — Cartel de Cali"},
        {"tipo_id":"CC", "nro_id":"71612512","nombre":"DAIRO ANTONIO USUGA DAVID","origen":"OFAC SDN","detalle":"NARCOTICS — Clan del Golfo (Otoniel)"},
        {"tipo_id":"CC", "nro_id":"98530916","nombre":"JOSE GONZALO RODRIGUEZ GACHA","origen":"OFAC SDN","detalle":"NARCOTICS — El Mexicano"},
        {"tipo_id":"CC", "nro_id":"71700551","nombre":"DANIEL RENDON HERRERA","origen":"OFAC SDN","detalle":"NARCOTICS — Don Mario"},
        {"tipo_id":"CC", "nro_id":"77040924","nombre":"HENRY DE JESUS LOPEZ LONDONO","origen":"OFAC SDN","detalle":"NARCOTICS — Mi Sangre"},
        {"tipo_id":"NIT","nro_id":"800154059","nombre":"GRUPO EMPRESARIAL DAABON","origen":"OFAC SDN","detalle":"SDGT — Vínculos narcoactividad"},
        # ONU — Sanciones
        {"tipo_id":"CC", "nro_id":"19430101","nombre":"IVAN MARQUEZ","origen":"ONU","detalle":"RES. 2341 — FARC disidencias"},
        {"tipo_id":"CC", "nro_id":"19620303","nombre":"JESUS SANTRICH","origen":"ONU","detalle":"RES. 2341 — FARC narcotrafico"},
        # Terroristas
        {"tipo_id":"CC", "nro_id":"71359678","nombre":"TIMOLEON JIMENEZ","origen":"TERRORISTAS EE.UU.","detalle":"SDGT — FARC Timochenko"},
        {"tipo_id":"CC", "nro_id":"17030128","nombre":"RODRIGO LONDONO ECHEVERRI","origen":"TERRORISTAS EE.UU.","detalle":"SDGT — FARC Timochenko (AKA)"},
        # PEPs reconocidos
        {"tipo_id":"CC", "nro_id":"19494471","nombre":"ERNESTO SAMPER PIZANO","origen":"PEP","detalle":"Ex-Presidente de Colombia 1994-1998"},
        {"tipo_id":"CC", "nro_id":"19465122","nombre":"ALVARO URIBE VELEZ","origen":"PEP","detalle":"Ex-Presidente de Colombia 2002-2010"},
        {"tipo_id":"CC", "nro_id":"19427479","nombre":"JUAN MANUEL SANTOS CALDERON","origen":"PEP","detalle":"Ex-Presidente de Colombia 2010-2018"},
        {"tipo_id":"CC", "nro_id":"79945621","nombre":"GUSTAVO FRANCISCO PETRO URREGO","origen":"PEP","detalle":"Presidente de Colombia 2022-2026"},
        {"tipo_id":"CC", "nro_id":"55230826","nombre":"FRANCIA ELENA MARQUEZ MINA","origen":"PEP","detalle":"Vicepresidenta de Colombia 2022-2026"},
        {"tipo_id":"CC", "nro_id":"98530111","nombre":"PIEDAD ESNEDA CORDOBA RUIZ","origen":"PEP","detalle":"Ex-Senadora — Investigada FARC"},
        {"tipo_id":"CC", "nro_id":"42765432","nombre":"MARIA JOSE PIZARRO RODRIGUEZ","origen":"PEP","detalle":"Senadora de la República"},
        {"tipo_id":"CC", "nro_id":"79876543","nombre":"ROY LEONARDO BARRERAS MONTEALEGRE","origen":"PEP","detalle":"Senador — Ex-Presidente Senado"},
        {"tipo_id":"CC", "nro_id":"80345678","nombre":"IVAN DUQUE MARQUEZ","origen":"PEP","detalle":"Ex-Presidente de Colombia 2018-2022"},
        # Declarados PEP
        {"tipo_id":"CC", "nro_id":"71234567","nombre":"FEDERICO GUTIERREZ ZULUAGA","origen":"DECLARADO PEP","detalle":"Ex-Alcalde Medellín / Ex-candidato presidencial"},
        {"tipo_id":"CC", "nro_id":"79432109","nombre":"ENRIQUE PENALOSA LONDONO","origen":"DECLARADO PEP","detalle":"Ex-Alcalde Bogotá"},
        {"tipo_id":"NIT","nro_id":"900234567","nombre":"ODEBRECHT COLOMBIA","origen":"OFAC SDN","detalle":"SDGT — Sobornos y corrupción"},
    ])
    return demo, False, {}

TODAS, LISTAS_REALES, LISTAS_META = cargar_listas()

def norm(s):
    if not isinstance(s,str): return ""
    return "".join(c for c in unicodedata.normalize("NFD",s) if unicodedata.category(c)!="Mn").upper().strip()

def buscar(tipo_id, nro_id, nombre, umbral):
    res=[]; nombre_n=norm(nombre)
    solo_doc=bool(nro_id) and not nombre
    solo_nombre=bool(nombre) and not nro_id
    for _,row in TODAS.iterrows():
        tiene_doc=(str(row.get("nro_id","N/A")) not in ("N/A","") and str(row.get("tipo_id","N/A"))!="N/A")
        sim=0.0; nivel=""
        if solo_doc:
            if not tiene_doc: continue
            if row["tipo_id"]!=tipo_id: continue
            if str(row["nro_id"])==str(nro_id): nivel="EXACTA"
            elif fuzz.ratio(str(row["nro_id"]),str(nro_id))>=85: nivel="APROXIMADA"
            else: continue
            sim=100.0
        elif solo_nombre:
            sim=fuzz.token_sort_ratio(norm(str(row["nombre"])),nombre_n)/100
            if sim<umbral: continue
            nivel="SOLO NOMBRE"
        else:
            sim=fuzz.token_sort_ratio(norm(str(row["nombre"])),nombre_n)/100
            de=dc=False
            if tiene_doc and row["tipo_id"]==tipo_id:
                de=str(row["nro_id"])==str(nro_id)
                dc=fuzz.ratio(str(row["nro_id"]),str(nro_id))>=85
            if de and sim>=umbral: nivel="EXACTA"
            elif dc and sim>=umbral: nivel="APROXIMADA"
            elif sim>=umbral: nivel="SOLO NOMBRE"
            else: continue
        r=row.to_dict(); r["sim_%"]=round(sim*100,1) if sim<=1 else round(sim,1); r["nivel"]=nivel
        res.append(r)
    seen=set(); out=[]
    for r in res:
        k=(r["nombre"],r["origen"])
        if k not in seen: seen.add(k); out.append(r)
    return pd.DataFrame(out) if out else pd.DataFrame()

def log_q(modulo,tipo_id,nro_id,nombre,resultado):
    st.session_state.logs.append({"fecha_hora":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "usuario":st.session_state.user,"modulo":modulo,"tipo_id":tipo_id,
        "nro_id":str(nro_id),"nombre":nombre,"resultado":resultado})

def a_excel(df):
    buf=io.BytesIO()
    with pd.ExcelWriter(buf,engine="openpyxl") as w:
        df.to_excel(w,index=False,sheet_name="Datos")
        ws=w.sheets["Datos"]
        from openpyxl.styles import Font,PatternFill,Alignment
        for cell in ws[1]:
            cell.font=Font(bold=True,color="FFFFFF")
            cell.fill=PatternFill("solid",fgColor="0F1B2D")
            cell.alignment=Alignment(horizontal="center")
        for col in ws.columns:
            ws.column_dimensions[col[0].column_letter].width=max(len(str(col[0].value or "")),10)+4
    return buf.getvalue()

PALABRAS_RIESGO=["lavado de activos","narcotrafico","corrupcion","fraude","capturado","investigado",
    "condenado","sancionado","terrorismo","extorsion","contrabando","enriquecimiento ilicito",
    "peculado","cohecho","imputado","money laundering","fraud","corruption","arrested","sanctioned",
    "drug trafficking","terrorism","formulacion de cargos"]

def _rss_fetch(url,max_n=8):
    try:
        req=_ureq.Request(url,headers={"User-Agent":"Mozilla/5.0"})
        with _ureq.urlopen(req,timeout=10) as resp:
            root=_ET.fromstring(resp.read())
        items=[]
        for item in root.findall(".//item")[:max_n]:
            titulo=item.findtext("title","").strip()
            if not titulo: continue
            items.append({"titulo":titulo,"fuente":item.findtext("source","").strip(),
                "fecha":(item.findtext("pubDate","") or "")[:16],
                "link":item.findtext("link","").strip(),
                "riesgo":any(p in norm(titulo).lower() for p in PALABRAS_RIESGO)})
        return items,None
    except Exception as e: return [],str(e)

def buscar_noticias(nombre,pais="Colombia",max_n=8):
    t="lavado OR narcotrafico OR corrupcion OR fraude OR capturado OR investigado OR condenado OR sancionado OR terrorismo OR imputado"
    q=f'"{nombre}" ({t})'
    if pais: q+=f" {pais}"
    return _rss_fetch(f"https://news.google.com/rss/search?q={_uparse.quote(q)}&hl=es-419&gl=CO&ceid=CO:es-419",max_n)

def buscar_noticias_fiscalia(nombre, max_n=6):
    """Busca directamente en el sitio de la Fiscalía via RSS de búsqueda WordPress."""
    resultados = []

    # Método 1: RSS de búsqueda WordPress de fiscalia.gov.co
    try:
        url_rss = f"https://www.fiscalia.gov.co/colombia/?s={_uparse.quote(nombre)}&feed=rss2"
        req = _ureq.Request(url_rss, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/rss+xml, application/xml, text/xml",
        })
        with _ureq.urlopen(req, timeout=12) as resp:
            root = _ET.fromstring(resp.read())
        for item in root.findall(".//item")[:max_n]:
            titulo = item.findtext("title", "").strip()
            link   = item.findtext("link",  "").strip()
            fecha  = (item.findtext("pubDate", "") or "")[:16]
            desc   = item.findtext("description", "").strip()[:200]
            if titulo:
                resultados.append({
                    "titulo":  titulo,
                    "fuente":  "Fiscalía General de la Nación",
                    "fecha":   fecha,
                    "link":    link,
                    "desc":    desc,
                    "origen":  "Fiscalía",
                    "riesgo":  True,
                })
    except Exception:
        pass

    # Método 2: Google News filtrado a fiscalia.gov.co (fallback)
    if not resultados:
        try:
            q = f'site:fiscalia.gov.co "{nombre}"'
            url_gn = f"https://news.google.com/rss/search?q={_uparse.quote(q)}&hl=es-419&gl=CO&ceid=CO:es-419"
            req2 = _ureq.Request(url_gn, headers={"User-Agent": "Mozilla/5.0"})
            with _ureq.urlopen(req2, timeout=10) as resp:
                root2 = _ET.fromstring(resp.read())
            for item in root2.findall(".//item")[:max_n]:
                titulo = item.findtext("title", "").strip()
                link   = item.findtext("link",  "").strip()
                fecha  = (item.findtext("pubDate", "") or "")[:16]
                if titulo:
                    resultados.append({
                        "titulo": titulo,
                        "fuente": "Fiscalía (vía Google)",
                        "fecha":  fecha,
                        "link":   link,
                        "desc":   "",
                        "origen": "Fiscalía",
                        "riesgo": True,
                    })
        except Exception:
            pass

    return resultados

def mostrar_noticias(nom_label, tipo_id, id_label):
    nombre_enc = _uparse.quote(nom_label)
    url_fiscalia = f"https://www.fiscalia.gov.co/colombia/?s={nombre_enc}"

    st.markdown("### 📰 Noticias adversas y fuentes judiciales")

    # Link directo Fiscalía con nombre precargado
    st.markdown(f"""
    <a class="ext-link" href="{url_fiscalia}" target="_blank">
      <div class="ext-title">🏛️ Buscar en Fiscalía General de la Nación</div>
      <div style="font-size:12px;color:#374151;margin-top:2px">
        Búsqueda directa para: <b>{nom_label}</b>
      </div>
      <div class="ext-url">fiscalia.gov.co/colombia/?s={nom_label}</div>
    </a>
    """, unsafe_allow_html=True)

    col_g, col_f = st.columns(2)

    with col_g:
        st.markdown("**🌐 Google News — Noticias adversas**")
        with st.spinner("Buscando noticias..."):
            noticias, err = buscar_noticias(nom_label, "Colombia", 8)
        if err:
            st.caption(f"No disponible: {err}")
        elif not noticias:
            st.success("✅ Sin noticias adversas encontradas")
        else:
            adv = [n for n in noticias if n["riesgo"]]
            neu = [n for n in noticias if not n["riesgo"]]
            if adv:
                st.error(f"🚨 {len(adv)} noticia(s) con indicadores de riesgo")
                log_q("NOTICIAS", tipo_id, id_label, nom_label, f"{len(adv)} NOTICIAS ADVERSAS")
            else:
                st.info(f"📰 {len(noticias)} noticias — sin riesgo directo")
            for n in (adv + neu):
                e = "🔴" if n["riesgo"] else "🟡"
                with st.expander(f"{e} {n['titulo'][:75]}",
                                 expanded=n["riesgo"]):
                    c1, c2 = st.columns([2, 1])
                    c1.caption(f"📰 {n['fuente']}")
                    c2.caption(f"📅 {n['fecha']}")
                    st.markdown(f"[🔗 Ver noticia completa]({n['link']})")

    with col_f:
        st.markdown("**🏛️ Fiscalía — Resultados directos**")
        with st.spinner("Consultando Fiscalía..."):
            nf = buscar_noticias_fiscalia(nom_label)
        if not nf:
            st.success("✅ Sin resultados en Fiscalía General")
            st.markdown(f"[🔍 Verificar manualmente]({url_fiscalia})")
        else:
            st.error(f"🚨 {len(nf)} resultado(s) en Fiscalía General")
            for n in nf:
                with st.expander(f"🔴 {n['titulo'][:75]}", expanded=True):
                    c1, c2 = st.columns([2, 1])
                    c1.caption(f"🏛️ {n['fuente']}")
                    c2.caption(f"📅 {n['fecha']}")
                    if n.get("desc"):
                        st.caption(n["desc"] + "…")
                    st.markdown(f"[🔗 Ver en Fiscalía.gov.co]({n['link']})")
            st.markdown(f"[🔍 Ver todos los resultados en Fiscalía]({url_fiscalia})")

def pantalla_login():
    _,col,_=st.columns([1,1.3,1])
    with col:
        st.markdown("""<div class="login-wrap">
          <div class="login-title">🛡️ SERVIALAFT SAS</div>
          <div class="login-sub">Sistema de Consulta Listas Vinculantes<br>
          OFAC · ONU · Terroristas · PEPs · Noticias Adversas</div>
        </div>""",unsafe_allow_html=True)
        usuario=st.text_input("Usuario",placeholder="usuario")
        password=st.text_input("Contraseña",type="password",placeholder="contraseña")
        st.caption("Demo → **admin** / **admin123**")
        if st.button("Iniciar sesión →",type="primary",use_container_width=True):
            if usuario in USUARIOS and USUARIOS[usuario]["password"]==password:
                st.session_state.logged_in=True; st.session_state.user=usuario; st.rerun()
            else: st.error("Usuario o contraseña incorrectos.")

MENU_ITEMS=["🔍 Búsqueda Unificada","👮 Policía Nacional","⚖️ Procuraduría",
            "📋 Registros consultados","📊 Estadísticas de uso","🚪 Cerrar sesión"]

def sidebar():
    with st.sidebar:
        st.markdown("### 🛡️ SERVIALAFT SAS"); st.markdown("---")
        info=USUARIOS[st.session_state.user]
        st.markdown(f"**{info['nombre']}**"); st.caption(f"Rol: {info['rol']}"); st.markdown("---")
        idx=0
        for i,m in enumerate(MENU_ITEMS):
            if st.session_state.menu in m or m in st.session_state.menu: idx=i; break
        sel=st.radio("Menú",MENU_ITEMS,index=idx,label_visibility="collapsed")
        if "Cerrar" in sel:
            st.session_state.logged_in=False; st.session_state.user=None
            st.session_state.menu="UNIFICADA"; st.rerun()
        else: st.session_state.menu=sel

def mod_unificada():
    st.markdown("## 🔍 Búsqueda Unificada")
    st.caption("OFAC SDN · ONU · Terroristas EE.UU. · Terroristas UE · PEPs Colombia · Noticias Adversas · Fiscalía")
    if LISTAS_REALES:
        total=LISTAS_META.get("total",len(TODAS)); fecha=LISTAS_META.get("fecha_actualizacion","—")
        st.success(f"✅ Listas reales — **{total:,} registros** | Actualización: {fecha}")
    else:
        st.warning("⚠️ Datos de demo — corre `descargar_listas.py` para activar datos reales.")

    tab_ind,tab_mas=st.tabs(["🔎 Consulta individual","📂 Carga masiva (Excel)"])

    with tab_ind:
        c1,c2=st.columns([1,2])
        with c1:
            tipo_id=st.selectbox("Tipo ID",["CC","NIT","CE","PAS"])
            nro_id=st.text_input("Número de identificación",placeholder="Opcional")
            nombre=st.text_input("Nombre completo",placeholder="Opcional")
            st.caption("💡 Busca por nombre, documento o ambos.")
            umbral=st.slider("SimiliScore™ (%)",50,100,85)
            consultar=st.button("🔍 Consultar",type="primary",use_container_width=True)
            st.markdown("---"); st.markdown("**🔗 Verificación manual (CAPTCHA)**")
            st.markdown("""
            <a class="ext-link" href="https://antecedentes.policia.gov.co:7005/WebJudicial/" target="_blank">
              <div class="ext-title">👮 Policía Nacional</div>
              <div class="ext-url">antecedentes.policia.gov.co</div></a>
            <a class="ext-link" href="https://www.procuraduria.gov.co/Pages/Consulta-de-Antecedentes.aspx" target="_blank">
              <div class="ext-title">⚖️ Procuraduría General</div>
              <div class="ext-url">procuraduria.gov.co</div></a>
            <a class="ext-link" href="https://www.fiscalia.gov.co/colombia/busqueda/" target="_blank">
              <div class="ext-title">🏛️ Fiscalía General</div>
              <div class="ext-url">fiscalia.gov.co</div></a>""",unsafe_allow_html=True)
        with c2:
            if consultar:
                td=bool(nro_id.strip()); tn=bool(nombre.strip())
                if not td and not tn:
                    st.warning("Ingresa al menos un número de identificación o un nombre.")
                else:
                    il=nro_id.strip() if td else "N/A"
                    nl=nombre.strip() if tn else "(búsqueda por documento)"
                    with st.spinner("Consultando listas vinculantes..."):
                        df=buscar(tipo_id,nro_id.strip() if td else "",nombre.strip() if tn else "",umbral/100)
                    st.markdown("### 📋 Listas vinculantes")
                    if df.empty:
                        st.success("✅ Sin coincidencias en ninguna lista vinculante.")
                        log_q("UNIFICADA",tipo_id,il,nl,"NO ENCONTRADO")
                    else:
                        lh=df["origen"].unique().tolist()
                        st.error(f"🚨 Encontrado en {len(lh)} lista(s) — {len(df)} coincidencia(s)")
                        log_q("UNIFICADA",tipo_id,il,nl,df["nivel"].iloc[0])
                        cr=st.columns(min(len(lh),4))
                        for i,lst in enumerate(lh): cr[i%4].metric(lst,f"{len(df[df['origen']==lst])} hit(s)")
                        st.markdown("---")
                        for _,row in df.iterrows():
                            e="🔴" if row["nivel"]=="EXACTA" else "🟡"
                            with st.expander(f"{e} {row['nombre']}  —  {row['origen']}",expanded=True):
                                cc1,cc2,cc3=st.columns(3)
                                cc1.metric("Lista",row["origen"]); cc2.metric("SimiliScore™",f"{row['sim_%']}%"); cc3.metric("Nivel",row["nivel"])
                                if row.get("detalle"): st.write(f"**Detalle:** {row['detalle']}")
                    if tn:
                        st.markdown("---")
                        mostrar_noticias(nl,tipo_id,il)
                    st.markdown("---")
                    cx,cy=st.columns(2)
                    de=df if not df.empty else pd.DataFrame({"tipo_id":[tipo_id],"nro_id":[il],"nombre":[nl],"resultado":["SIN COINCIDENCIA"]})
                    cx.download_button("📥 Excel",data=a_excel(de),file_name=f"consulta_{il}_{date.today()}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",use_container_width=True)
                    if PDF_DISPONIBLE:
                        pb=generar_pdf_individual(tipo_id,il,nl,df if not df.empty else None,usuario=st.session_state.user)
                        cy.download_button("📄 Certificado PDF",data=pb,file_name=f"certificado_{il}_{date.today()}.pdf",
                            mime="application/pdf",use_container_width=True)
            else:
                st.info("Completa el formulario y presiona **Consultar**.")
                st.markdown("""
                **Esta búsqueda consulta simultáneamente:**
                - 🇺🇸 OFAC SDN — Nacionales Especialmente Designados
                - 🇺🇸 Terroristas EE.UU. — SDGT, TALIBAN y otros programas
                - 🇺🇳 ONU — Lista Consolidada Consejo de Seguridad
                - 🇪🇺 Terroristas UE — Lista Consolidada de Sanciones
                - 🇨🇴 PEPs Colombia — Personas Expuestas Políticamente
                - 📰 Google News — noticias adversas automático
                - 🏛️ Fiscalía General — noticias automático
                """)

    with tab_mas:
        c1,c2=st.columns([1,2])
        with c1:
            st.markdown("**Formato requerido:**"); st.code("tipo_id | nro_id | nombre")
            pt=pd.DataFrame({"tipo_id":["CC","NIT","CE"],"nro_id":["12345678","900123456","87654321"],
                             "nombre":["JUAN PEREZ GOMEZ","EMPRESA ABC SAS","CARLOS LOPEZ"]})
            st.download_button("📄 Plantilla",data=a_excel(pt),file_name="plantilla.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            archivo=st.file_uploader("Subir .xlsx",type=["xlsx"])
            umbral_m=st.slider("SimiliScore™ masivo (%)",50,100,85)
            procesar=st.button("⚙️ Procesar archivo",type="primary",use_container_width=True)
        with c2:
            if procesar and archivo:
                di=pd.read_excel(archivo); di.columns=[c.lower().strip() for c in di.columns]
                if not {"tipo_id","nro_id","nombre"}.issubset(di.columns):
                    st.error("El archivo debe tener columnas: tipo_id, nro_id, nombre")
                else:
                    res=[]; prog=st.progress(0)
                    for i,row in di.iterrows():
                        prog.progress((i+1)/len(di),f"Procesando {i+1}/{len(di)}…")
                        dr=buscar(str(row["tipo_id"]).upper().strip(),str(row["nro_id"]).strip(),str(row["nombre"]).strip(),umbral_m/100)
                        if dr.empty:
                            res.append({"tipo_id":row["tipo_id"],"nro_id":row["nro_id"],"nombre":row["nombre"],
                                        "resultado":"SIN COINCIDENCIA","origen":"—","nivel":"—","sim_%":"—"})
                            log_q("MASIVO",row["tipo_id"],row["nro_id"],row["nombre"],"NO ENCONTRADO")
                        else:
                            for _,r in dr.iterrows():
                                rd=r.to_dict(); rd["resultado"]="ENCONTRADO EN LISTA"; res.append(rd)
                            log_q("MASIVO",row["tipo_id"],row["nro_id"],row["nombre"],dr["nivel"].iloc[0])
                    prog.empty(); do=pd.DataFrame(res)
                    enc=(do["resultado"]=="ENCONTRADO EN LISTA").sum()
                    co1,co2,co3=st.columns(3)
                    co1.metric("Total",len(di)); co2.metric("🚨 Con coincidencia",enc); co3.metric("✅ Sin coincidencia",len(di)-enc)
                    st.dataframe(do,use_container_width=True,height=280)
                    bx,by=st.columns(2)
                    bx.download_button("📥 Excel",data=a_excel(do),file_name=f"masivo_{date.today()}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",use_container_width=True)
                    if PDF_DISPONIBLE:
                        pm=generar_pdf_masivo(do,umbral_m/100,usuario=st.session_state.user)
                        by.download_button("📄 Reporte PDF",data=pm,file_name=f"reporte_masivo_{date.today()}.pdf",
                            mime="application/pdf",use_container_width=True)
            elif procesar: st.warning("Sube primero un archivo .xlsx")
            else: st.info("Sube un archivo y presiona **Procesar archivo**.")

def mod_policia():
    st.markdown("## 👮 Antecedentes Judiciales — Policía Nacional")
    st.info("Esta fuente usa CAPTCHA. Accede al portal y registra el resultado aquí.",icon="ℹ️")
    st.markdown("""<a class="ext-link" href="https://antecedentes.policia.gov.co:7005/WebJudicial/" target="_blank">
      <div class="ext-title">🔗 Policía Nacional — Certificado Judicial</div>
      <div class="ext-url">https://antecedentes.policia.gov.co:7005/WebJudicial/</div></a>""",unsafe_allow_html=True)
    st.markdown("---"); st.markdown("### 📝 Registrar resultado de consulta manual")
    with st.form("frm_policia",clear_on_submit=True):
        c1,c2=st.columns(2)
        tid=c1.selectbox("Tipo ID",["CC","NIT","CE","PAS"]); nid=c2.text_input("Número de identificación")
        nom=st.text_input("Nombre completo")
        res=st.radio("Resultado",["SIN ANTECEDENTES","CON ANTECEDENTES","NO SE PUDO VERIFICAR"],horizontal=True)
        obs=st.text_area("Observaciones",height=80); ok=st.form_submit_button("💾 Guardar",type="primary")
    if ok:
        if not nid or not nom: st.warning("Completa todos los campos.")
        else:
            log_q("POLICÍA",tid,nid,nom,res)
            if res=="SIN ANTECEDENTES": st.success("✅ Sin antecedentes.")
            elif res=="CON ANTECEDENTES": st.error("🚨 Con antecedentes.")
            else: st.warning("⚠️ Verificación pendiente.")
            if PDF_DISPONIBLE:
                pp=generar_pdf_manual(tid,nid,nom,"POLICÍA",res,observacion=obs,usuario=st.session_state.user)
                st.download_button("📄 Certificado PDF",data=pp,file_name=f"policia_{nid}_{date.today()}.pdf",mime="application/pdf")

def mod_procuraduria():
    st.markdown("## ⚖️ Antecedentes Disciplinarios — Procuraduría General")
    st.info("Esta fuente usa CAPTCHA. Accede al portal y registra el resultado aquí.",icon="ℹ️")
    st.markdown("""<a class="ext-link" href="https://www.procuraduria.gov.co/Pages/Consulta-de-Antecedentes.aspx" target="_blank">
      <div class="ext-title">🔗 Procuraduría General — Antecedentes Disciplinarios</div>
      <div class="ext-url">https://www.procuraduria.gov.co/Pages/Consulta-de-Antecedentes.aspx</div></a>""",unsafe_allow_html=True)
    st.markdown("---"); st.markdown("### 📝 Registrar resultado de consulta manual")
    with st.form("frm_procu",clear_on_submit=True):
        c1,c2=st.columns(2)
        tid=c1.selectbox("Tipo ID",["CC","NIT","CE","PAS"]); nid=c2.text_input("Número de identificación")
        nom=st.text_input("Nombre completo")
        res=st.radio("Resultado",["SIN SANCIONES DISCIPLINARIAS","CON SANCIONES DISCIPLINARIAS","NO SE PUDO VERIFICAR"],horizontal=True)
        obs=st.text_area("Observaciones",height=80); ok=st.form_submit_button("💾 Guardar",type="primary")
    if ok:
        if not nid or not nom: st.warning("Completa todos los campos.")
        else:
            log_q("PROCURADURÍA",tid,nid,nom,res)
            if "SIN" in res: st.success("✅ Sin sanciones.")
            elif "CON" in res: st.error("🚨 Con sanciones disciplinarias.")
            else: st.warning("⚠️ Verificación pendiente.")
            if PDF_DISPONIBLE:
                pp=generar_pdf_manual(tid,nid,nom,"PROCURADURÍA",res,observacion=obs,usuario=st.session_state.user)
                st.download_button("📄 Certificado PDF",data=pp,file_name=f"procuraduria_{nid}_{date.today()}.pdf",mime="application/pdf")

LOGS_DEMO=[
    {"fecha_hora":"2024-06-10 08:14","usuario":"analista1","modulo":"UNIFICADA","tipo_id":"CC","nro_id":"12345678","nombre":"JUAN CARLOS RODRIGUEZ GOMEZ","resultado":"EXACTA"},
    {"fecha_hora":"2024-06-10 09:02","usuario":"consultor","modulo":"POLICÍA","tipo_id":"CC","nro_id":"98765432","nombre":"MARIA JOSE ALVAREZ RUIZ","resultado":"SIN ANTECEDENTES"},
    {"fecha_hora":"2024-06-10 09:48","usuario":"analista1","modulo":"MASIVO","tipo_id":"NIT","nro_id":"900123456","nombre":"INVERSIONES DELTA SAS","resultado":"EXACTA"},
    {"fecha_hora":"2024-06-10 10:15","usuario":"admin","modulo":"PROCURADURÍA","tipo_id":"CC","nro_id":"55443322","nombre":"LUCIA PATRICIA MORA VARGAS","resultado":"SIN SANCIONES DISCIPLINARIAS"},
    {"fecha_hora":"2024-06-10 10:58","usuario":"analista1","modulo":"UNIFICADA","tipo_id":"CC","nro_id":"11223344","nombre":"CARLOS ANDRES PEREZ","resultado":"APROXIMADA"},
    {"fecha_hora":"2024-06-10 11:22","usuario":"consultor","modulo":"NOTICIAS","tipo_id":"CC","nro_id":"87654321","nombre":"ANDRES FELIPE LOPEZ","resultado":"2 NOTICIAS ADVERSAS"},
]

def mod_logs():
    st.markdown("## 📋 Registros de consultas")
    todos=LOGS_DEMO+st.session_state.logs; df=pd.DataFrame(todos)
    if df.empty: st.info("No hay registros aún."); return
    c1,c2,c3=st.columns(3)
    fm=c1.selectbox("Módulo",["Todos"]+sorted(df["modulo"].unique().tolist()))
    fu=c2.selectbox("Usuario",["Todos"]+sorted(df["usuario"].unique().tolist()))
    ft=c3.text_input("Buscar nombre o número")
    dff=df.copy()
    if fm!="Todos": dff=dff[dff["modulo"]==fm]
    if fu!="Todos": dff=dff[dff["usuario"]==fu]
    if ft:
        q=ft.upper()
        dff=dff[dff["nombre"].str.upper().str.contains(q,na=False)|dff["nro_id"].str.contains(q,na=False)]
    dff=dff.sort_values("fecha_hora",ascending=False).reset_index(drop=True)
    st.caption(f"Mostrando {len(dff)} de {len(df)} registros")
    st.dataframe(dff,use_container_width=True,height=400)
    st.download_button("📥 Exportar",data=a_excel(dff),file_name=f"logs_{date.today()}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

def mod_stats():
    st.markdown("## 📊 Estadísticas de uso")
    c1,c2,c3,c4=st.columns(4)
    c1.markdown('<div class="metric-box"><div class="metric-num">172</div><div class="metric-label">Consultas este mes</div></div>',unsafe_allow_html=True)
    c2.markdown('<div class="metric-box"><div class="metric-num">38</div><div class="metric-label">🚨 Alertas generadas</div></div>',unsafe_allow_html=True)
    c3.markdown('<div class="metric-box"><div class="metric-num">3</div><div class="metric-label">Usuarios activos</div></div>',unsafe_allow_html=True)
    c4.markdown('<div class="metric-box"><div class="metric-num">16</div><div class="metric-label">Cargas masivas</div></div>',unsafe_allow_html=True)
    st.markdown("---")
    dia=pd.DataFrame({"Fecha":pd.date_range("2024-06-01",periods=10,freq="D"),
        "Búsqueda Unificada":[12,18,9,22,15,30,8,25,19,14],"Policía":[5,8,4,9,6,12,3,10,7,6],
        "Procuraduría":[3,5,2,6,4,8,2,7,5,4],"Noticias":[8,12,6,14,10,18,5,16,11,9]}).set_index("Fecha")
    res=pd.DataFrame({"Resultado":["Sin coincidencia","Exacta","Aproximada","Antecedentes","Noticias adversas"],
                      "Cantidad":[134,18,12,8,14]}).set_index("Resultado")
    co1,co2=st.columns(2)
    with co1: st.markdown("#### Consultas diarias"); st.line_chart(dia,height=220)
    with co2: st.markdown("#### Distribución resultados"); st.bar_chart(res,height=220)
    st.markdown("---")
    co1,co2=st.columns(2)
    with co1:
        st.markdown("#### Por usuario")
        st.dataframe(pd.DataFrame({"Usuario":["analista1","consultor","admin"],"Consultas":[87,42,23],"Alertas":[21,9,8]}),
            use_container_width=True,hide_index=True)
    with co2:
        st.markdown("#### Listas con más alertas")
        st.dataframe(pd.DataFrame({"Lista":["OFAC SDN","ONU","TERRORISTAS UE","PEP","DECLARADO PEP"],"Alertas":[22,8,4,5,3]}),
            use_container_width=True,hide_index=True)
    st.markdown("---")
    st.download_button("📥 Exportar reporte",data=a_excel(dia.reset_index()),
        file_name=f"estadisticas_{date.today()}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

if not st.session_state.logged_in:
    pantalla_login()
else:
    sidebar()
    m=st.session_state.menu
    if   "Unificada"    in m: mod_unificada()
    elif "Policia" in m or "Policía" in m: mod_policia()
    elif "Procuraduria" in m or "Procuraduría" in m: mod_procuraduria()
    elif "Registros"    in m: mod_logs()
    elif "Estadisticas" in m or "Estadísticas" in m: mod_stats()