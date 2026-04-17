"""
generador_pdf.py — SERVIALAFT SAS
Genera certificados PDF profesionales para consultas individuales y masivas.
Dependencias: reportlab
"""

import io
from datetime import datetime, date
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import mm, inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, Image as RLImage
)

try:
    import qrcode
    _QR_OK = True
except ImportError:
    _QR_OK = False

# ─── Paleta corporativa ───────────────────────────────────────────────────────
AZUL_OSCURO  = colors.HexColor("#0F1B2D")
AZUL_MED     = colors.HexColor("#1E3A5F")
AZUL_CLARO   = colors.HexColor("#2563EB")
GRIS_TEXTO   = colors.HexColor("#374151")
GRIS_SUAVE   = colors.HexColor("#F3F4F6")
GRIS_BORDE   = colors.HexColor("#D1D5DB")
VERDE        = colors.HexColor("#065F46")
VERDE_BG     = colors.HexColor("#D1FAE5")
ROJO         = colors.HexColor("#991B1B")
ROJO_BG      = colors.HexColor("#FEE2E2")
AMARILLO     = colors.HexColor("#92400E")
AMARILLO_BG  = colors.HexColor("#FEF3C7")
BLANCO       = colors.white

W, H = letter  # 612 x 792 pts


# ─── QR helper ────────────────────────────────────────────────────────────────
def _qr_image(texto, size=38):
    if not _QR_OK:
        return None
    qr = qrcode.QRCode(version=1, box_size=2, border=1,
                       error_correction=qrcode.constants.ERROR_CORRECT_M)
    qr.add_data(texto)
    qr.make(fit=True)
    buf = io.BytesIO()
    qr.make_image(fill_color="black", back_color="white").save(buf, format="PNG")
    buf.seek(0)
    return RLImage(buf, width=size, height=size)


# ─── Estilos ─────────────────────────────────────────────────────────────────
def get_styles():
    base = getSampleStyleSheet()
    return {
        "titulo": ParagraphStyle(
            "titulo", fontSize=18, fontName="Helvetica-Bold",
            textColor=AZUL_OSCURO, alignment=TA_CENTER, spaceAfter=2
        ),
        "subtitulo": ParagraphStyle(
            "subtitulo", fontSize=10, fontName="Helvetica",
            textColor=GRIS_TEXTO, alignment=TA_CENTER, spaceAfter=4
        ),
        "seccion": ParagraphStyle(
            "seccion", fontSize=11, fontName="Helvetica-Bold",
            textColor=AZUL_MED, spaceBefore=10, spaceAfter=4
        ),
        "normal": ParagraphStyle(
            "normal", fontSize=9, fontName="Helvetica",
            textColor=GRIS_TEXTO, spaceAfter=4, leading=14
        ),
        "normal_bold": ParagraphStyle(
            "normal_bold", fontSize=9, fontName="Helvetica-Bold",
            textColor=AZUL_OSCURO, spaceAfter=4
        ),
        "certif": ParagraphStyle(
            "certif", fontSize=9.5, fontName="Helvetica",
            textColor=GRIS_TEXTO, alignment=TA_JUSTIFY,
            spaceAfter=6, leading=15
        ),
        "pie": ParagraphStyle(
            "pie", fontSize=7.5, fontName="Helvetica",
            textColor=colors.HexColor("#6B7280"), alignment=TA_CENTER
        ),
        "resultado_ok": ParagraphStyle(
            "resultado_ok", fontSize=11, fontName="Helvetica-Bold",
            textColor=VERDE, alignment=TA_CENTER
        ),
        "resultado_alerta": ParagraphStyle(
            "resultado_alerta", fontSize=11, fontName="Helvetica-Bold",
            textColor=ROJO, alignment=TA_CENTER
        ),
        "resultado_aprox": ParagraphStyle(
            "resultado_aprox", fontSize=11, fontName="Helvetica-Bold",
            textColor=AMARILLO, alignment=TA_CENTER
        ),
        "folio": ParagraphStyle(
            "folio", fontSize=8, fontName="Helvetica",
            textColor=colors.HexColor("#9CA3AF"), alignment=TA_RIGHT
        ),
    }


# ─── Header y footer ─────────────────────────────────────────────────────────
def make_header_footer(watermark=False):
    """Devuelve la función de header/footer, opcionalmente con sello DEMO."""
    def _hf(canvas, doc):
        canvas.saveState()

        # ── HEADER ────────────────────────────────────────────────────────────
        BAND = 66  # altura de la banda superior
        canvas.setFillColor(AZUL_OSCURO)
        canvas.rect(0, H - BAND, W, BAND, fill=1, stroke=0)

        canvas.setStrokeColor(colors.HexColor("#F59E0B"))
        canvas.setLineWidth(2)
        canvas.line(0, H - BAND, W, H - BAND)

        canvas.setFillColor(BLANCO)
        canvas.setFont("Helvetica-Bold", 16)
        canvas.drawString(32, H - 30, "SERVIALAFT SAS")
        canvas.setFont("Helvetica", 9)
        canvas.drawString(32, H - 46, "Sistema de Consulta de Listas Vinculantes · CruzaListas")

        canvas.setFont("Helvetica", 8.5)
        canvas.setFillColor(colors.HexColor("#93C5FD"))
        canvas.drawRightString(W - 32, H - 30, f"Fecha: {date.today():%d/%m/%Y}")
        canvas.drawRightString(W - 32, H - 46, f"Hora: {datetime.now():%H:%M} (hora local)")

        # ── FOOTER ────────────────────────────────────────────────────────────
        canvas.setFillColor(AZUL_OSCURO)
        canvas.rect(0, 0, W, 36, fill=1, stroke=0)

        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.HexColor("#93C5FD"))
        canvas.drawCentredString(W / 2, 22,
            "SERVIALAFT SAS  ·  NIT: 900.XXX.XXX-X  ·  Colombia")
        canvas.drawCentredString(W / 2, 12,
            "Este documento es generado automáticamente y tiene validez como certificado de consulta.")

        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(colors.HexColor("#6B7280"))
        canvas.drawRightString(W - 20, 22, f"Pág. {doc.page}")

        # ── WATERMARK DEMO ────────────────────────────────────────────────────
        if watermark:
            canvas.setFillColor(colors.Color(0.75, 0.75, 0.75, 0.18))
            canvas.setFont("Helvetica-Bold", 90)
            canvas.saveState()
            canvas.translate(W / 2, H / 2)
            canvas.rotate(45)
            canvas.drawCentredString(0, 0, "DEMO")
            canvas.restoreState()

        canvas.restoreState()
    return _hf


# ─── Tabla de datos del consultado ───────────────────────────────────────────
def tabla_consultado(tipo_id, nro_id, nombre, usuario, modulo):
    data = [
        ["TIPO ID", "NÚMERO DE IDENTIFICACIÓN", "NOMBRE COMPLETO"],
        [tipo_id,   nro_id,                      nombre.upper()],
        ["MÓDULO DE CONSULTA", "USUARIO CONSULTOR", "FECHA Y HORA"],
        [modulo,    usuario,
         datetime.now().strftime("%d/%m/%Y %H:%M:%S")],
    ]
    t = Table(data, colWidths=[100, 180, 236])
    t.setStyle(TableStyle([
        # Filas de encabezado
        ("BACKGROUND",  (0, 0), (-1, 0), AZUL_OSCURO),
        ("BACKGROUND",  (0, 2), (-1, 2), AZUL_MED),
        ("TEXTCOLOR",   (0, 0), (-1, 0), BLANCO),
        ("TEXTCOLOR",   (0, 2), (-1, 2), BLANCO),
        ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME",    (0, 2), (-1, 2), "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, 3), 8),
        # Filas de datos
        ("BACKGROUND",  (0, 1), (-1, 1), GRIS_SUAVE),
        ("BACKGROUND",  (0, 3), (-1, 3), GRIS_SUAVE),
        ("FONTNAME",    (0, 1), (-1, 1), "Helvetica-Bold"),
        ("FONTNAME",    (0, 3), (-1, 3), "Helvetica"),
        ("TEXTCOLOR",   (0, 1), (-1, 1), AZUL_OSCURO),
        ("TEXTCOLOR",   (0, 3), (-1, 3), GRIS_TEXTO),
        # Bordes y padding
        ("GRID",        (0, 0), (-1, -1), 0.4, GRIS_BORDE),
        ("ROWBACKGROUND", (0, 0), (-1, -1), [GRIS_SUAVE, BLANCO]),
        ("TOPPADDING",  (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",(0, 0), (-1, -1), 8),
    ]))
    return t


# ─── Tabla de coincidencias ───────────────────────────────────────────────────
def tabla_coincidencias(df_res):
    cols_show = []
    headers   = []
    for c, h in [("origen","LISTA"), ("nro_id","NÚMERO ID"),
                 ("nombre","NOMBRE EN LISTA"), ("nivel","NIVEL"),
                 ("sim_%","SIMILITUD"), ("detalle","DETALLE")]:
        if c in df_res.columns:
            cols_show.append(c); headers.append(h)

    data = [headers]
    for _, row in df_res.iterrows():
        fila = []
        for c in cols_show:
            val = row.get(c, "—")
            fila.append("—" if str(val) in ("nan","None","") else str(val))
        data.append(fila)

    n = len(cols_show)
    col_w = 516 / n
    t = Table(data, colWidths=[col_w] * n, repeatRows=1)

    style = [
        ("BACKGROUND",    (0, 0), (-1, 0),  AZUL_OSCURO),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  BLANCO),
        ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, -1), 7.5),
        ("GRID",          (0, 0), (-1, -1), 0.4, GRIS_BORDE),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]
    for i in range(1, len(data)):
        nivel = str(data[i][cols_show.index("nivel")] if "nivel" in cols_show else "")
        bg = (ROJO_BG if nivel == "EXACTA"
              else AMARILLO_BG if nivel in ("APROXIMADA","SOLO NOMBRE")
              else BLANCO)
        style.append(("BACKGROUND", (0, i), (-1, i), bg))

    t.setStyle(TableStyle(style))
    return t


# ─── Caja de resultado (SIN / CON coincidencia) ───────────────────────────────
def caja_resultado(tiene_coincidencia, nivel=None):
    if not tiene_coincidencia:
        texto  = "✔  SIN COINCIDENCIAS EN LISTAS VINCULANTES"
        fondo  = VERDE_BG
        borde  = colors.HexColor("#6EE7B7")
        color  = VERDE
        icono  = "RESULTADO: APROBADO"
    elif nivel == "EXACTA":
        texto  = "✘  COINCIDENCIA EXACTA — ALERTA CRÍTICA"
        fondo  = ROJO_BG
        borde  = colors.HexColor("#FCA5A5")
        color  = ROJO
        icono  = "RESULTADO: ALERTA"
    else:
        texto  = "⚠  COINCIDENCIA APROXIMADA — REQUIERE REVISIÓN"
        fondo  = AMARILLO_BG
        borde  = colors.HexColor("#FCD34D")
        color  = AMARILLO
        icono  = "RESULTADO: REVISIÓN MANUAL"

    t = Table(
        [[Paragraph(f"<b>{texto}</b>", ParagraphStyle(
            "rb", fontSize=11, fontName="Helvetica-Bold",
            textColor=color, alignment=TA_CENTER))]],
        colWidths=[516]
    )
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), fondo),
        ("BOX",           (0, 0), (-1, -1), 1.2, borde),
        ("TOPPADDING",    (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
        ("ROUNDEDCORNERS",(0, 0), (-1, -1), 4),
    ]))
    return t


# ─── Textos de certificación ─────────────────────────────────────────────────
CERT_SIN = (
    "SERVIALAFT SAS certifica que, en la fecha indicada en este documento, se realizó "
    "la consulta de las listas vinculantes nacionales e internacionales disponibles en el "
    "sistema CruzaListas, incluyendo OFAC SDN, Terroristas EE.UU., Resoluciones del Consejo "
    "de Seguridad de la ONU, Sanciones UE, Personas Expuestas Políticamente (PEPs Colombia) "
    "y búsqueda de noticias adversas en Google News y Fiscalía General de la Nación. "
    "<b>El resultado de dicha consulta es NEGATIVO: el sujeto NO figura en ninguna de las "
    "listas consultadas</b> con el nivel de similitud configurado (SimiliScore™). "
    "Este certificado es válido únicamente para la fecha y hora de expedición, y debe "
    "renovarse periódicamente según la política de debida diligencia de cada entidad."
)

CERT_CON = (
    "SERVIALAFT SAS certifica que, en la fecha indicada en este documento, se realizó "
    "la consulta de las listas vinculantes nacionales e internacionales disponibles en el "
    "sistema CruzaListas. <b>El resultado de dicha consulta es POSITIVO: el sujeto "
    "identificado FIGURA en una o más listas vinculantes</b>, tal como se detalla en la "
    "sección anterior. Se recomienda proceder conforme al Manual SARLAFT de la entidad, "
    "escalar al oficial de cumplimiento y abstenerse de iniciar o continuar la relación "
    "comercial hasta tanto se haya realizado la debida diligencia ampliada requerida."
)

# ─── Tabla de listas consultadas ─────────────────────────────────────────────
LISTAS_CONSULTADAS = [
    ("OFAC SDN",          "U.S. Department of the Treasury",    "NARCOTICS · SDGT · EO14059 · otros"),
    ("Terroristas EE.UU.","U.S. Dept. of Treasury — OFAC",      "SDGT · FTO · TALIBAN · DPRK2"),
    ("ONU",               "Consejo de Seguridad — Naciones Unidas","Res. 1267 · 1988 · 2341 · otros"),
    ("Sanciones UE",      "Comisión Europea",                   "Lista Consolidada UE"),
    ("PEPs Colombia",     "Función Pública — SIGEP Colombia",   "Decreto 830/2021"),
    ("Google News",       "Google News RSS",                    "Noticias adversas en tiempo real"),
    ("Fiscalía",          "Fiscalía General de la Nación",      "Boletines oficiales y capturas"),
]

def tabla_listas_consultadas():
    """Tabla con todas las fuentes consultadas."""
    _th = ParagraphStyle("lth", fontSize=7.5, fontName="Helvetica-Bold", textColor=BLANCO, leading=10)
    _tc = ParagraphStyle("ltc", fontSize=7.5, fontName="Helvetica",      textColor=GRIS_TEXTO, leading=10)
    _tn = ParagraphStyle("ltn", fontSize=7.5, fontName="Helvetica-Bold", textColor=AZUL_MED,  leading=10, alignment=TA_CENTER)

    data = [[Paragraph("#", _th), Paragraph("LISTA / FUENTE", _th),
             Paragraph("ENTIDAD EMISORA", _th), Paragraph("PROGRAMAS / ALCANCE", _th)]]
    for i, (lista, entidad, alcance) in enumerate(LISTAS_CONSULTADAS, 1):
        data.append([Paragraph(str(i), _tn), Paragraph(lista, _tc),
                     Paragraph(entidad, _tc), Paragraph(alcance, _tc)])

    t = Table(data, colWidths=[20, 110, 180, 206])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),  AZUL_OSCURO),
        ("FONTSIZE",      (0, 0), (-1, -1), 7.5),
        ("GRID",          (0, 0), (-1, -1), 0.4, GRIS_BORDE),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 5),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 5),
        ("ALIGN",         (0, 0), (0, -1),  "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUND", (0, 1), (-1, -1), [GRIS_SUAVE, BLANCO]),
    ]))
    return t


# ─── Sección de noticias en PDF ───────────────────────────────────────────────
def seccion_noticias_pdf(story, S, nombre, noticias_google, noticias_fiscalia, num_sec):
    """Agrega sección de noticias adversas al PDF."""
    story.append(Paragraph(f"{num_sec}. BÚSQUEDA DE NOTICIAS ADVERSAS", S["seccion"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=GRIS_BORDE, spaceAfter=6))

    # Parámetros de búsqueda
    terminos = "lavado · narcotrafico · corrupcion · fraude · capturado · investigado · condenado · sancionado · terrorismo · imputado · extorsion · peculado"
    params_data = [
        ["PARÁMETRO",          "VALOR"],
        ["Nombre buscado",      nombre.upper()],
        ["Método de búsqueda", 'Nombre completo entre comillas — coincidencia exacta de frase'],
        ["Términos de riesgo",  terminos],
        ["Fuentes consultadas", "Google News RSS · Fiscalía General (RSS WordPress)"],
        ["Cobertura temporal",  "Últimas noticias indexadas"],
    ]
    pt = Table(params_data, colWidths=[160, 356])
    pt.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),  AZUL_MED),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  BLANCO),
        ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, -1), 7.5),
        ("GRID",          (0, 0), (-1, -1), 0.4, GRIS_BORDE),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("ROWBACKGROUND", (0, 1), (-1, -1), [GRIS_SUAVE, BLANCO]),
    ]))
    story.append(pt)
    story.append(Spacer(1, 8))

    # Resultados Google News
    story.append(Paragraph("<b>Google News — Noticias adversas</b>", ParagraphStyle(
        "sh", fontSize=9, fontName="Helvetica-Bold", textColor=AZUL_MED, spaceAfter=4)))

    todas_noticias = list(noticias_google or [])
    adversas_g = [n for n in todas_noticias if n.get("riesgo")]
    neutras_g  = [n for n in todas_noticias if not n.get("riesgo")]

    if not todas_noticias:
        story.append(Paragraph(
            "Sin noticias adversas encontradas en Google News para el nombre consultado.",
            ParagraphStyle("ok", fontSize=8, fontName="Helvetica", textColor=VERDE, spaceAfter=4)
        ))
    else:
        if adversas_g:
            story.append(Paragraph(
                f"<b>🚨 {len(adversas_g)} noticia(s) con indicadores de riesgo:</b>",
                ParagraphStyle("alerta", fontSize=8.5, fontName="Helvetica-Bold",
                               textColor=ROJO, spaceAfter=3)
            ))
            for n in adversas_g:
                story.append(Paragraph(
                    f"• <b>{n.get('titulo','')}</b> | {n.get('fuente','—')} | {n.get('fecha','—')}",
                    ParagraphStyle("ni", fontSize=7.5, fontName="Helvetica",
                                   textColor=GRIS_TEXTO, spaceAfter=2, leftIndent=10)
                ))
        if neutras_g:
            story.append(Spacer(1, 4))
            story.append(Paragraph(
                f"Otras {len(neutras_g)} noticias encontradas sin palabras de riesgo directas.",
                ParagraphStyle("neu", fontSize=8, fontName="Helvetica",
                               textColor=GRIS_TEXTO, spaceAfter=2)
            ))

    story.append(Spacer(1, 8))

    # Resultados Fiscalía
    story.append(Paragraph("<b>Fiscalía General de la Nación — Boletines oficiales</b>",
        ParagraphStyle("sh2", fontSize=9, fontName="Helvetica-Bold",
                       textColor=AZUL_MED, spaceAfter=4)))

    nf = list(noticias_fiscalia or [])
    if not nf:
        story.append(Paragraph(
            "Sin resultados en boletines oficiales de la Fiscalía General para el nombre consultado.",
            ParagraphStyle("okf", fontSize=8, fontName="Helvetica",
                           textColor=VERDE, spaceAfter=4)
        ))
    else:
        story.append(Paragraph(
            f"<b>🚨 {len(nf)} resultado(s) en la Fiscalía General de la Nación:</b>",
            ParagraphStyle("alertaf", fontSize=8.5, fontName="Helvetica-Bold",
                           textColor=ROJO, spaceAfter=3)
        ))
        for n in nf:
            story.append(Paragraph(
                f"• <b>{n.get('titulo','')}</b> | {n.get('fecha','—')}",
                ParagraphStyle("nif", fontSize=7.5, fontName="Helvetica",
                               textColor=GRIS_TEXTO, spaceAfter=2, leftIndent=10)
            ))
            if n.get("desc"):
                story.append(Paragraph(
                    f"  {n['desc']}...",
                    ParagraphStyle("desc", fontSize=7, fontName="Helvetica",
                                   textColor=colors.HexColor("#6B7280"),
                                   spaceAfter=3, leftIndent=20)
                ))

    story.append(Spacer(1, 6))


# ═══════════════════════════════════════════════════════════════════════════════
# PDF INDIVIDUAL
# ═══════════════════════════════════════════════════════════════════════════════
def generar_pdf_individual(tipo_id, nro_id, nombre, df_resultado,
                           usuario="sistema", folio=None,
                           noticias_google=None, noticias_fiscalia=None,
                           watermark=False):
    """
    Genera el PDF de certificación individual.
    noticias_google: lista de dicts con keys titulo, fuente, fecha, riesgo
    noticias_fiscalia: lista de dicts con keys titulo, fuente, fecha, desc
    watermark: si True imprime sello DEMO diagonal en cada página.
    Retorna bytes del PDF.
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=letter,
        topMargin=86, bottomMargin=52,
        leftMargin=48, rightMargin=48,
        title="Certificado de Consulta — CruzaListas · SERVIALAFT SAS",
        author="SERVIALAFT SAS",
    )

    S = get_styles()
    folio = folio or f"CL-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    tiene = df_resultado is not None and not df_resultado.empty
    nivel_principal = df_resultado["nivel"].iloc[0] if tiene else None
    tiene_noticias  = bool(noticias_google) or bool(noticias_fiscalia)
    adversas_count  = len([n for n in (noticias_google or []) if n.get("riesgo")]) + \
                      len(noticias_fiscalia or [])

    story = []
    sec = 1  # contador de secciones

    # ── Folio ──────────────────────────────────────────────────────────────
    story.append(Paragraph(f"Folio: <b>{folio}</b>", S["folio"]))
    story.append(Spacer(1, 14))

    # ── Título ─────────────────────────────────────────────────────────────
    story.append(Paragraph("CERTIFICADO DE CONSULTA DE LISTAS VINCULANTES", S["titulo"]))
    story.append(Paragraph(
        "CruzaListas · OFAC SDN · Terroristas EE.UU. · ONU · Sanciones UE · PEPs Colombia · Noticias Adversas",
        S["subtitulo"]))
    story.append(HRFlowable(width="100%", thickness=1.5, color=AZUL_OSCURO, spaceAfter=10))

    # ── 1. Datos del consultado ────────────────────────────────────────────
    story.append(Paragraph(f"{sec}. DATOS DEL SUJETO CONSULTADO", S["seccion"])); sec += 1
    story.append(tabla_consultado(tipo_id, nro_id, nombre, usuario, "BÚSQUEDA UNIFICADA"))
    story.append(Spacer(1, 12))

    # ── 2. Resultado general ───────────────────────────────────────────────
    story.append(Paragraph(f"{sec}. RESULTADO DE LA CONSULTA", S["seccion"])); sec += 1
    story.append(caja_resultado(tiene, nivel_principal))
    if tiene_noticias and adversas_count > 0:
        story.append(Spacer(1, 6))
        t_not = Table([[Paragraph(
            f"<b>⚠  NOTICIAS ADVERSAS: {adversas_count} resultado(s) — Ver sección de noticias</b>",
            ParagraphStyle("na", fontSize=9, fontName="Helvetica-Bold",
                           textColor=AMARILLO, alignment=TA_CENTER))]],
            colWidths=[516])
        t_not.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), AMARILLO_BG),
            ("BOX",           (0, 0), (-1, -1), 1, colors.HexColor("#FCD34D")),
            ("TOPPADDING",    (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(t_not)
    story.append(Spacer(1, 10))

    # ── 3. Listas consultadas ──────────────────────────────────────────────
    story.append(Paragraph(f"{sec}. LISTAS Y FUENTES CONSULTADAS", S["seccion"])); sec += 1
    story.append(tabla_listas_consultadas())
    story.append(Spacer(1, 10))

    # ── 4. Detalle de coincidencias (condicional) ──────────────────────────
    if tiene:
        story.append(Paragraph(f"{sec}. DETALLE DE COINCIDENCIAS EN LISTAS", S["seccion"])); sec += 1
        story.append(tabla_coincidencias(df_resultado))
        story.append(Spacer(1, 10))

    # ── 5. Noticias adversas (condicional) ────────────────────────────────
    if tiene_noticias:
        seccion_noticias_pdf(story, S, nombre, noticias_google, noticias_fiscalia, str(sec))
        sec += 1

    # ── 6. Certificación ───────────────────────────────────────────────────
    story.append(Paragraph(f"{sec}. CERTIFICACIÓN Y ALCANCE", S["seccion"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=GRIS_BORDE, spaceAfter=6))
    story.append(Paragraph(CERT_CON if tiene else CERT_SIN, S["certif"]))

    _hf = make_header_footer(watermark)
    doc.build(story, onFirstPage=_hf, onLaterPages=_hf)
    return buf.getvalue()


# ═══════════════════════════════════════════════════════════════════════════════
# PDF MANUAL (Policía / Procuraduría)
# ═══════════════════════════════════════════════════════════════════════════════
def generar_pdf_manual(tipo_id, nro_id, nombre, modulo, resultado,
                       observacion="", usuario="sistema", folio=None,
                       watermark=False):
    """
    PDF para consultas manuales (Policía / Procuraduría / Otras Fuentes).
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=letter,
        topMargin=86, bottomMargin=52,
        leftMargin=48, rightMargin=48,
        title=f"Certificado {modulo} — SERVIALAFT SAS",
    )

    S = get_styles()
    folio = folio or f"SA-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    es_negativo = "SIN" in resultado.upper()
    es_positivo = "CON" in resultado.upper()

    story = []
    story.append(Paragraph(f"Folio: <b>{folio}</b>", S["folio"]))
    story.append(Spacer(1, 6))
    story.append(Paragraph(f"CERTIFICADO DE CONSULTA — {modulo.upper()}", S["titulo"]))
    story.append(Paragraph("Consulta manual registrada en el sistema SERVIALAFT SAS", S["subtitulo"]))
    story.append(HRFlowable(width="100%", thickness=1.5, color=AZUL_OSCURO, spaceAfter=10))

    story.append(Paragraph("1. DATOS DEL SUJETO CONSULTADO", S["seccion"]))
    story.append(tabla_consultado(tipo_id, nro_id, nombre, usuario, modulo))
    story.append(Spacer(1, 12))

    story.append(Paragraph("2. RESULTADO DE LA CONSULTA MANUAL", S["seccion"]))
    story.append(caja_resultado(es_positivo, "EXACTA" if es_positivo else None))
    story.append(Spacer(1, 10))

    if observacion:
        story.append(Paragraph("3. OBSERVACIONES DEL CONSULTOR", S["seccion"]))
        story.append(Paragraph(observacion, S["certif"]))
        story.append(Spacer(1, 8))

    sec_cert = 4 if observacion else 3
    story.append(Paragraph(f"{sec_cert}. CERTIFICACIÓN Y ALCANCE", S["seccion"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=GRIS_BORDE, spaceAfter=6))

    url_map = {
        "POLICÍA":      "https://antecedentes.policia.gov.co:7005/WebJudicial/",
        "PROCURADURÍA": "https://www.procuraduria.gov.co/Pages/Consulta-de-Antecedentes.aspx",
    }
    url = url_map.get(modulo.upper(), "portal oficial")
    cert = (
        f"SERVIALAFT SAS certifica que, en la fecha indicada, el usuario consultor "
        f"realizó la verificación del sujeto identificado en este documento "
        f"a través de: <i>{url}</i>. El resultado registrado es: <b>{resultado}</b>. "
        + ("Este resultado indica que el sujeto no presenta registros en la fuente consultada "
           "al momento de la verificación." if es_negativo else
           "Se recomienda escalar al Oficial de Cumplimiento y documentar el hallazgo en el "
           "expediente del cliente, aplicando el procedimiento de debida diligencia ampliada "
           "establecido en el Manual SARLAFT de la entidad.")
    )
    story.append(Paragraph(cert, S["certif"]))

    _hf = make_header_footer(watermark)
    doc.build(story, onFirstPage=_hf, onLaterPages=_hf)
    return buf.getvalue()


# ═══════════════════════════════════════════════════════════════════════════════
# PDF MASIVO (resumen ejecutivo)
# ═══════════════════════════════════════════════════════════════════════════════
def generar_pdf_masivo(df_resultados, umbral, usuario="sistema", folio=None,
                       watermark=False):
    """
    Resumen ejecutivo para carga masiva.
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=letter,
        topMargin=86, bottomMargin=52,
        leftMargin=48, rightMargin=48,
        title="Reporte Masivo — SERVIALAFT SAS",
    )

    S = get_styles()
    folio = folio or f"SA-M-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    total      = len(df_resultados)
    encontrados = (df_resultados.get("resultado", df_resultados.get("nivel","")) == "ENCONTRADO EN LISTA").sum() \
                  if "resultado" in df_resultados.columns else 0
    limpios    = total - encontrados

    story = []
    story.append(Paragraph(f"Folio: <b>{folio}</b>", S["folio"]))
    story.append(Spacer(1, 6))
    story.append(Paragraph("REPORTE EJECUTIVO — CONSULTA MASIVA DE LISTAS VINCULANTES", S["titulo"]))
    story.append(Paragraph("OFAC SDN · Resoluciones ONU · PEPs Colombia", S["subtitulo"]))
    story.append(HRFlowable(width="100%", thickness=1.5, color=AZUL_OSCURO, spaceAfter=10))

    # Parámetros de la consulta
    story.append(Paragraph("1. PARÁMETROS DE LA CONSULTA", S["seccion"]))
    param_data = [
        ["PARÁMETRO",           "VALOR"],
        ["Usuario consultor",   usuario.upper()],
        ["Fecha y hora",        datetime.now().strftime("%d/%m/%Y  %H:%M:%S")],
        ["Folio",               folio],
        ["SimiliScore™ umbral", f"{int(umbral * 100)}%"],
        ["Total registros",     str(total)],
    ]
    pt = Table(param_data, colWidths=[200, 316])
    pt.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),  AZUL_OSCURO),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  BLANCO),
        ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, -1), 8.5),
        ("GRID",          (0, 0), (-1, -1), 0.4, GRIS_BORDE),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("ROWBACKGROUND", (0, 1), (-1, -1), [GRIS_SUAVE, BLANCO]),
    ]))
    story.append(pt)
    story.append(Spacer(1, 12))

    # Resumen
    story.append(Paragraph("2. RESUMEN DE RESULTADOS", S["seccion"]))
    resumen_data = [
        ["TOTAL CONSULTADOS", "SIN COINCIDENCIA ✔", "CON ALERTA 🚨"],
        [str(total),           str(limpios),          str(encontrados)],
    ]
    rt = Table(resumen_data, colWidths=[172, 172, 172])
    rt.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),  AZUL_MED),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  BLANCO),
        ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTNAME",      (0, 1), (-1, 1),  "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, -1), 10),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("GRID",          (0, 0), (-1, -1), 0.4, GRIS_BORDE),
        ("BACKGROUND",    (0, 1), (0, 1),   GRIS_SUAVE),
        ("BACKGROUND",    (1, 1), (1, 1),   VERDE_BG),
        ("BACKGROUND",    (2, 1), (2, 1),   ROJO_BG),
        ("TEXTCOLOR",     (1, 1), (1, 1),   VERDE),
        ("TEXTCOLOR",     (2, 1), (2, 1),   ROJO),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(rt)
    story.append(Spacer(1, 12))

    # Detalle completo
    story.append(Paragraph("3. DETALLE DE REGISTROS CONSULTADOS", S["seccion"]))

    cols_det = ["tipo_id","nro_id","nombre","resultado","origen","nivel","sim_%"]
    headers_det = ["TIPO","NÚMERO","NOMBRE","RESULTADO","LISTA","NIVEL","SIM%"]
    widths_det  = [38, 70, 150, 80, 60, 60, 35]

    filas_det = [headers_det]
    for _, row in df_resultados.iterrows():
        fila = []
        for c in cols_det:
            v = row.get(c, "—")
            fila.append("—" if str(v) in ("nan","None","") else str(v))
        filas_det.append(fila)

    det_t = Table(filas_det, colWidths=widths_det, repeatRows=1)
    det_style = [
        ("BACKGROUND",    (0, 0), (-1, 0),  AZUL_OSCURO),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  BLANCO),
        ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, -1), 7),
        ("GRID",          (0, 0), (-1, -1), 0.3, GRIS_BORDE),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 4),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
    ]
    for i in range(1, len(filas_det)):
        res = filas_det[i][3]
        if "ENCONTRADO" in res:
            det_style.append(("BACKGROUND", (0, i), (-1, i), ROJO_BG))
        else:
            det_style.append(("BACKGROUND", (0, i), (-1, i),
                               GRIS_SUAVE if i % 2 == 0 else BLANCO))
    det_t.setStyle(TableStyle(det_style))
    story.append(det_t)
    story.append(Spacer(1, 12))

    # Certificación masiva
    story.append(Paragraph("4. CERTIFICACIÓN Y ALCANCE", S["seccion"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=GRIS_BORDE, spaceAfter=6))
    cert_mas = (
        f"SERVIALAFT SAS certifica que se realizó la consulta masiva de <b>{total}</b> "
        f"registros contra las listas vinculantes OFAC SDN, Resoluciones del Consejo de "
        f"Seguridad de la ONU y Personas Expuestas Políticamente (PEPs) de Colombia, "
        f"con un umbral de similitud (SimiliScore™) del <b>{int(umbral*100)}%</b>. "
        f"El resultado indica <b>{limpios} registros sin coincidencia</b> y "
        f"<b>{encontrados} registros con alerta</b>. Los registros con alerta deben ser "
        f"revisados por el Oficial de Cumplimiento antes de proceder con cualquier operación. "
        f"Este reporte es válido únicamente para la fecha y hora de expedición."
    )
    story.append(Paragraph(cert_mas, S["certif"]))

    _hf = make_header_footer(watermark)
    doc.build(story, onFirstPage=_hf, onLaterPages=_hf)
    return buf.getvalue()
