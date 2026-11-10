"""
construir_web.py — genera la web estática de Euro a Euro a partir de los
artículos en Markdown (los mismos que producen tus agentes).

Uso (desde la carpeta euroaeuro):
    python construir_web.py                      -> usa ORIGEN por defecto
    python construir_web.py RUTA\\A\\LOS\\ARTICULOS -> otra carpeta de artículos

Resultado: la carpeta "web", lista para subir a Netlify.
Archivos opcionales junto a este script:
    excluir.txt        un slug por línea: artículos que NO deben salir
    clasificacion.csv  slug;pilar  (pilar = ordena | ahorra | invierte)
Además crea informe_web.csv con la clasificación y los avisos de cada artículo.
"""

import csv
import html
import json
import os
import re
import shutil
import sys
import time

import markdown

from limpieza import limpiar_articulo, parece_cortado
from legales import PAGINAS_LEGALES

# ---------------------------------------------------------------- AJUSTES
ORIGEN = os.path.join("contenido", "publicado")
DESTINO = "web"
SITIO = "https://euroaeuro.eu"
NOMBRE = "Euro a Euro"
AUTOR = "Sebastián Prat"
# Cuando elijas un servicio de correo, pega aquí la URL de su formulario.
# Mientras esté vacío, la web muestra "muy pronto" en lugar de un formulario falso.
FORMULARIO_ACTION = ""

# Formulario de MailerLite (cuenta 2784740, formulario 203766011908851480).
# El identificador 48368733 es el de la instancia del embed y lo usa el JavaScript
# de MailerLite para llamar a ml_webform_success_48368733 al terminar.
MAILERLITE_FORM = """
<div id="mlb2-48368733" class="ml-form-embedContainer ml-subscribe-form ml-subscribe-form-48368733">
  <div class="ml-form-embedWrapper embedForm">
    <div class="ml-form-embedBody row-form">
      <form class="ml-block-form"
            action="https://assets.mailerlite.com/jsonp/2784740/forms/203766011908851480/subscribe"
            method="post"
            style="display:flex;flex-wrap:wrap;gap:12px;align-items:end">
        <div style="flex:1;min-width:220px">
          <label for="ml-email" style="display:block;font-weight:600;margin-bottom:6px">Tu correo</label>
          <input id="ml-email" name="fields[email]" type="email" required
                 placeholder="nombre@correo.com" autocomplete="email"
                 class="ml-field-email ml-validate-email ml-validate-required">
        </div>
        <input type="hidden" name="ml-submit" value="1">
        <input type="hidden" name="anticsrf" value="true">
        <button class="btn" style="background:#14201A;color:#fff" type="submit">Suscribirme</button>
        <p id="ml-estado" style="flex-basis:100%;margin:4px 0 0;font-size:14px;display:none"></p>
        <p style="flex-basis:100%;font-size:13px;margin:0;opacity:.85">
          Al suscribirte aceptas la <a href="/privacidad/" style="color:inherit">política de privacidad</a>.
          Puedes darte de baja cuando quieras.
        </p>
      </form>
    </div>
    <div class="ml-form-successBody row-success" style="display:none">
      <p style="font-weight:600;margin:0 0 6px">Gracias. Te hemos enviado un correo para confirmar la suscripción.</p>
      <p style="margin:0;font-size:14px;opacity:.85">Revisa también la carpeta de spam. Hasta que no confirmes, no recibirás la newsletter.</p>
    </div>
  </div>
</div>
<script>
(function () {
  var caja = document.querySelector('.ml-subscribe-form-48368733');
  if (!caja) return;
  var form = caja.querySelector('.ml-block-form');
  var estado = caja.querySelector('#ml-estado');
  var boton = form.querySelector('button[type="submit"]');
  var textoBoton = boton.textContent;

  function aviso(texto) {
    estado.textContent = texto;
    estado.style.display = 'block';
    boton.disabled = false;
    boton.textContent = textoBoton;
  }

  form.addEventListener('submit', function (ev) {
    ev.preventDefault();
    var email = form.querySelector('input[name="fields[email]"]').value.trim();
    if (!email) return;
    boton.disabled = true;
    boton.textContent = 'Enviando…';
    estado.style.display = 'none';

    var datos = new URLSearchParams();
    datos.set('fields[email]', email);
    datos.set('ml-submit', '1');
    datos.set('anticsrf', 'true');

    fetch(form.action, {
      method: 'POST',
      body: datos,
      mode: 'cors',
      headers: { 'Accept': 'application/json' }
    })
      .then(function (r) { return r.json(); })
      .then(function (j) {
        if (j && j.success) {
          caja.querySelector('.row-form').style.display = 'none';
          caja.querySelector('.row-success').style.display = 'block';
        } else {
          var detalle = (j && j.errors && j.errors.fields && j.errors.fields.email)
            ? ' Revisa que el correo esté bien escrito.' : '';
          aviso('No hemos podido completar la suscripción.' + detalle);
        }
      })
      .catch(function () {
        aviso('No hemos podido conectar. Inténtalo de nuevo en unos segundos.');
      });
  });
})();
</script>
"""

PILARES = {
    "ordena": ("Ordena tu dinero", "ordena-tu-dinero",
               "Presupuesto, fondo de emergencia y control de deudas."),
    "ahorra": ("Ahorra mejor", "ahorra-mejor",
               "Cuentas y depósitos, inflación y objetivos de ahorro."),
    "invierte": ("Da el salto a invertir", "invertir",
                 "Fondos, ETF, riesgo y fiscalidad básica en España."),
}
PALABRAS_INVERTIR = [
    "inversi", "etf", "bolsa", "renta fija", "renta variable", "cartera", "bono",
    "diversific", "criptomon", "gestión activa", "gestión pasiva", "promedio de coste",
    "concentración", "plan de pensiones", "crowd",
]
PALABRAS_ORDENA = [
    "presupuesto", "gasto", "deuda", "endeud", "emergencia", "suscripci", "nómina",
    "hormiga", "préstamo", "tarjeta", "crédito", "revolving", "embargo", "alquil",
    "pareja", "compartid", "factura", "scoring", "avalar", "aplazamiento",
]
HERRAMIENTAS = [
    {"slug": "interes-compuesto", "nombre": "Interés compuesto",
     "desc": "Cuánto crece tu ahorro con el tiempo.",
     "campos": [("capital", "Capital inicial", 1000, "€"), ("aporte", "Aportación mensual", 100, "€"),
                ("rent", "Rentabilidad anual", 4, "%"), ("anos", "Años", 10, "años")],
     "como": "Convertimos la rentabilidad anual en una rentabilidad mensual equivalente y aplicamos las aportaciones al final de cada mes. Es una proyección con una rentabilidad constante: en la realidad varía cada año."},
    {"slug": "fondo-de-emergencia", "nombre": "Fondo de emergencia",
     "desc": "Cuánto necesitas tener a mano.",
     "campos": [("gastos", "Gastos mensuales esenciales", 1500, "€"), ("meses", "Meses de cobertura", 6, "sel:3,6,9,12"),
                ("actual", "Ahorro que ya tienes para emergencias", 2000, "€"), ("aporte", "Cuánto puedes apartar al mes", 200, "€")],
     "como": "Multiplicamos tus gastos esenciales por los meses de cobertura que elijas. Como orientación general, tres meses se asocian a ingresos muy estables y seis o más a ingresos variables o a una sola fuente de ingresos en casa."},
    {"slug": "objetivo-de-ahorro", "nombre": "Objetivo de ahorro",
     "desc": "Cuánto ahorrar al mes para llegar a una meta.",
     "campos": [("objetivo", "Objetivo", 10000, "€"), ("anos", "Plazo", 5, "años"),
                ("actual", "Lo que ya tienes ahorrado", 1000, "€"), ("rent", "Rentabilidad anual esperada", 0, "%")],
     "como": "Calculamos la aportación mensual constante que, junto con lo que ya tienes y la rentabilidad indicada, alcanza el objetivo en el plazo. Con una rentabilidad del 0 % es simplemente lo que falta dividido entre los meses."},
    {"slug": "reparto-del-presupuesto", "nombre": "Reparto del presupuesto",
     "desc": "Necesidades, deseos y ahorro.",
     "campos": [("ingresos", "Ingresos netos mensuales", 2000, "€"), ("p1", "Necesidades", 50, "%"),
                ("p2", "Deseos", 30, "%"), ("p3", "Ahorro e inversión", 20, "%")],
     "como": "Reparte tus ingresos netos con la regla 50/30/20, que puedes modificar. Es un punto de partida, no una norma: si tus gastos fijos son altos, ajusta los porcentajes a tu realidad."},
    {"slug": "rentabilidad-real", "nombre": "Rentabilidad real",
     "desc": "Tu rentabilidad descontando la inflación.",
     "campos": [("nominal", "Rentabilidad anual", 3, "%"), ("inflacion", "Inflación anual", 2.5, "%"),
                ("capital", "Capital", 10000, "€"), ("anos", "Años", 10, "años")],
     "como": "La rentabilidad real es (1 + rentabilidad) / (1 + inflación) − 1. Mide cuánto aumenta tu poder adquisitivo y no solo tu saldo."},
    {"slug": "brecha-de-jubilacion", "nombre": "Brecha de jubilación",
     "desc": "Cuánto ahorrar al mes para completar tu pensión.",
     "nota": "<strong>Todas las cifras son brutas (antes de impuestos) y en euros de hoy.</strong> Así comparamos igual lo que te pagará la Seguridad Social y lo que quieres cobrar.",
     "campos": [("edad", "Tu edad actual", 40, "años"), ("retiro", "Edad a la que te jubilarás", 67, "años"),
                ("pension", "Pensión de la Seguridad Social (bruta al mes)", 1200, "€",
                 "Lo que te pagará el Estado cada mes antes de impuestos. Búscala en el simulador oficial (enlace abajo). Si el simulador te da el importe por paga y cobras 14 al año, multiplícalo por 14 y divídelo entre 12."),
                ("deseado", "Ingreso total que quieres tener (bruto al mes)", 2000, "€",
                 "Pensión más lo que saques de tu ahorro, antes de impuestos. Es el nivel de vida que quieres mantener."),
                ("duracion", "Años que quieres vivir de ese ahorro", 25, "años",
                 "Piensa hasta qué edad quieres que dure: si te jubilas a 67 y cuentas con vivir hasta los 92, son 25 años."),
                ("rent", "Rentabilidad anual esperada del ahorro", 3, "%"),
                ("infl", "Inflación anual esperada", 2, "%"),
                ("actual", "Ahorro que ya tienes para la jubilación", 0, "€")],
     "como": 'Para la pensión pública, usa el Simulador de jubilación de la Seguridad Social, en su <a href="https://sede.seg-social.gob.es/" rel="noopener" target="_blank">sede electrónica</a> (hay que identificarse con Cl@ve, certificado digital o SMS). Calculamos el <strong>hueco mensual</strong> entre esa pensión y el ingreso que quieres, qué capital cubriría ese hueco durante los años que indiques y cuánto ahorrar cada mes para tenerlo. Se supone que la pensión mantiene su poder adquisitivo y que la cuota mensual sube cada año con la inflación. No incluye los impuestos de los retiros ni posibles cambios futuros en las pensiones.'},
]
DESCARGAS = [
    ("Presupuesto del hogar", "Ingresos, gastos fijos y variables, mes a mes.", "presupuesto-hogar.xlsx"),
    ("Seguimiento del patrimonio", "Qué tienes, qué debes y cómo evoluciona.", "patrimonio.xlsx"),
    ("Plan de ahorro por objetivos", "Una hoja para cada meta, con su calendario.", "plan-ahorro-objetivos.xlsx"),
]
GA_ID = "G-0QKFLMK0QW"  # Medición de Google Analytics 4. Vacío = no se carga analítica.

CONSENTIMIENTO = """
<style>
#cc{position:fixed;left:0;right:0;bottom:0;z-index:99;display:none;gap:16px 22px;align-items:center;
    justify-content:space-between;flex-wrap:wrap;padding:16px 22px;background:#14201A;color:#F5F1E8;
    font-size:14px;line-height:1.5;box-shadow:0 -6px 24px rgba(0,0,0,.22)}
#cc p{margin:0;max-width:660px}
#cc a{color:inherit;text-decoration:underline}
#cc .acciones{display:flex;gap:10px;flex-wrap:wrap}
#cc button{font-family:inherit;font-size:14px;font-weight:600;border-radius:8px;padding:10px 18px;
           cursor:pointer;border:1px solid #7E8C84;background:transparent;color:inherit}
#cc button.si{background:#C9A227;border-color:#C9A227;color:#14201A}
#cc button:hover{opacity:.88}
</style>
<div id="cc" role="dialog" aria-live="polite" aria-label="Aviso de cookies">
  <p>Uso cookies propias y de Google Analytics para saber qué contenido se lee.
     Si aceptas, se cargan; si no, la web funciona igual.
     <a href="/cookies/">Más información</a>.</p>
  <div class="acciones">
    <button id="cc-no" type="button">Solo lo necesario</button>
    <button id="cc-si" class="si" type="button">Aceptar</button>
  </div>
</div>
<script>
(function () {
  var ID = "__GA__";
  function cargar() {
    if (!ID) return;
    window.dataLayer = window.dataLayer || [];
    function gtag() { dataLayer.push(arguments); }
    gtag("consent", "default", {
      ad_storage: "denied",
      ad_user_data: "denied",
      ad_personalization: "denied",
      analytics_storage: "denied"
    });
    gtag("js", new Date());
    gtag("consent", "update", { analytics_storage: "granted" });
    var s = document.createElement("script");
    s.async = true;
    s.src = "https://www.googletagmanager.com/gtag/js?id=" + ID;
    document.head.appendChild(s);
    gtag("config", ID, { anonymize_ip: true });
  }
  var caja = document.getElementById("cc");
  if (!ID) { caja.style.display = "none"; return; }
  var guardado = null;
  try { guardado = localStorage.getItem("consentimiento"); } catch (e) {}
  if (guardado === "1") { cargar(); }
  else if (guardado !== "0") { caja.style.display = "flex"; }
  document.getElementById("cc-si").onclick = function () {
    try { localStorage.setItem("consentimiento", "1"); } catch (e) {}
    caja.style.display = "none";
    cargar();
  };
  document.getElementById("cc-no").onclick = function () {
    try { localStorage.setItem("consentimiento", "0"); } catch (e) {}
    caja.style.display = "none";
  };
})();
</script>
""".replace("__GA__", GA_ID)

PAGINAS_PENDIENTES = {
    "sobre-mi": "Sobre mí", "contacto": "Contacto", "aviso-legal": "Aviso legal",
    "privacidad": "Política de privacidad", "cookies": "Política de cookies",
}

# -------------------------------------------------------------------- CSS
CSS = """
:root{--tinta:#14201A;--crema:#F7F5EF;--verde:#1F6F4A;--ambar:#E0A526;--borde:#E4E0D4;--gris:#4C5A52}
*{box-sizing:border-box}
body{margin:0;background:var(--crema);color:var(--tinta);font-family:'Inter',system-ui,sans-serif;line-height:1.6}
h1,h2,h3{font-family:'Space Grotesk','Inter',sans-serif;margin:0;line-height:1.15}
p{margin:0}a{color:var(--verde)}a:hover{color:var(--tinta)}
.wrap{max-width:1160px;margin:0 auto;padding:0 24px}
.sec{padding:72px 0}
.btn{display:inline-block;padding:14px 22px;border-radius:10px;font-weight:600;text-decoration:none;border:0;font-size:16px;cursor:pointer;font-family:inherit}
.btn-p{background:var(--verde);color:#fff}.btn-p:hover{background:var(--tinta);color:#fff}
.btn-s{border:1.5px solid var(--tinta);color:var(--tinta)}.btn-s:hover{background:var(--tinta);color:#fff}
.grid{display:grid;gap:20px;grid-template-columns:repeat(auto-fit,minmax(250px,1fr))}
.card{background:#fff;border:1px solid var(--borde);border-radius:16px;padding:28px}
.card h3{font-size:21px;margin-bottom:8px}
a.card{text-decoration:none;color:var(--tinta);display:block}a.card:hover{border-color:var(--verde)}
.step{width:40px;height:40px;border-radius:50%;background:var(--ambar);display:flex;align-items:center;justify-content:center;font-weight:700;font-family:'Space Grotesk',sans-serif;margin-bottom:16px}
.muted{color:var(--gris)}
.kicker{font-size:14px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:var(--verde);margin-bottom:12px}
.opt{display:block;padding:16px 18px;border:1px solid var(--borde);border-radius:12px;text-decoration:none;color:var(--tinta);margin-top:12px;background:var(--crema)}
.opt:hover{border-color:var(--verde)}.opt b{display:block;color:var(--verde);font-size:14px;margin-top:2px}
.cabecera{display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:16px;padding-top:24px;padding-bottom:24px}
.logo{display:flex;align-items:center;gap:10px;text-decoration:none;color:var(--tinta);font-family:'Space Grotesk',sans-serif;font-weight:700;font-size:22px}
.logo span{width:36px;height:36px;border-radius:50%;background:var(--ambar);display:flex;align-items:center;justify-content:center}
.nav{display:flex;flex-wrap:wrap;align-items:center;gap:8px 24px}
.nav a{color:var(--tinta);text-decoration:none;font-weight:500}.nav a:hover{color:var(--verde)}
.nav a.btn{color:#fff}
.pronto{display:inline-block;font-size:12px;font-weight:600;background:var(--crema);border:1px solid var(--borde);border-radius:999px;padding:2px 10px;margin-top:10px;color:var(--gris)}
.oscuro{background:var(--tinta);color:var(--crema)}
.oscuro .card{background:#1D2C24;border-color:#2C4136;color:var(--crema)}.oscuro .muted{color:#C9D3CC}
.oscuro .pronto{background:#14201A;border-color:#2C4136;color:#C9D3CC}
.suscripcion{background:var(--ambar)}
.suscripcion input{width:100%;padding:14px;border:1.5px solid var(--tinta);border-radius:10px;font-size:16px;background:#fff}
.pie{padding-top:40px;padding-bottom:40px;font-size:14px}
.migas{font-size:14px;color:var(--gris);margin-bottom:20px}
.articulo{max-width:760px;margin:0 auto;padding:24px 24px 72px}
.articulo h1{font-size:44px;margin-bottom:16px}
.meta{color:var(--gris);font-size:15px;margin-bottom:32px}
.prose{font-size:18px}.prose h2{font-size:30px;margin:44px 0 14px}.prose h3{font-size:22px;margin:30px 0 10px}
.prose p,.prose ul,.prose ol{margin:0 0 18px}.prose li{margin-bottom:6px}
.prose hr{border:0;border-top:1px solid var(--borde);margin:36px 0}
.tabla{overflow-x:auto;margin:24px 0}
.prose table{border-collapse:collapse;width:100%;font-size:16px}
.prose th,.prose td{border:1px solid var(--borde);padding:10px 12px;text-align:left}
.prose th{background:#ECE8DB}
.nota{font-size:15px;font-style:italic;color:var(--gris);border-left:3px solid var(--ambar);padding:4px 0 4px 14px;margin:20px 0}
.nota p{margin:0}
.aviso{font-size:14px;color:var(--gris);border-top:1px solid var(--borde);margin-top:48px;padding-top:16px}
.relacionados{margin-top:48px}
@media(max-width:700px){.articulo h1{font-size:34px}.hero h1{font-size:40px!important}}
"""

# ------------------------------------------------------------- PLANTILLAS
FUENTES = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
           '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600'
           '&family=Space+Grotesk:wght@500;700&display=swap" rel="stylesheet">')


def e(texto):
    return html.escape(texto, quote=True)


def cabecera():
    return (f'<header class="wrap cabecera"><a class="logo" href="/"><span>€</span>{NOMBRE}</a>'
            '<nav class="nav" aria-label="Principal"><a href="/#ruta">La ruta</a>'
            '<a href="/#herramientas">Herramientas</a><a href="/#descargas">Descargas</a>'
            '<a href="/sobre-mi/">Sobre mí</a><a class="btn btn-p" href="/#suscribirme">Suscribirme</a></nav></header>')


def pie():
    return ('<footer class="wrap pie"><p class="muted" style="max-width:720px;margin-bottom:16px">'
            'Contenido informativo y educativo. No constituye asesoramiento financiero personalizado '
            'ni una recomendación de inversión.</p><p>'
            '<a href="/aviso-legal/">Aviso legal</a> · <a href="/privacidad/">Privacidad</a> · '
            f'<a href="/cookies/">Cookies</a> · <a href="/contacto/">Contacto</a> · © {time.strftime("%Y")} {NOMBRE}</p></footer>')


def suscripcion(clase="suscripcion"):
    if MAILERLITE_FORM.strip():
        form = MAILERLITE_FORM
    elif FORMULARIO_ACTION:
        form = (f'<form action="{e(FORMULARIO_ACTION)}" method="post" style="display:flex;flex-wrap:wrap;gap:12px;align-items:end">'
                '<div style="flex:1;min-width:220px"><label for="email" style="display:block;font-weight:600;margin-bottom:6px">Tu correo</label>'
                '<input id="email" name="email" type="email" required placeholder="nombre@correo.com"></div>'
                '<button class="btn" style="background:#14201A;color:#fff" type="submit">Suscribirme</button></form>')
    else:
        form = '<p style="font-weight:600">Muy pronto podrás suscribirte aquí.</p>'
    return (f'<section id="suscribirme" class="sec {clase}"><div class="wrap" style="display:grid;gap:28px;'
            'grid-template-columns:repeat(auto-fit,minmax(300px,1fr));align-items:center">'
            '<div><h2 style="font-size:34px;margin-bottom:8px">Una idea clara cada semana</h2>'
            '<p style="font-size:18px">Un correo corto con una guía, una herramienta o una plantilla. Sin spam.</p></div>'
            f'<div>{form}</div></div></section>')


def pagina(titulo, descripcion, url, cuerpo, noindex=False, extra_head=""):
    robots = '<meta name="robots" content="noindex">' if noindex else ""
    return (f'<!doctype html><html lang="es"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            f'<title>{e(titulo)}</title><meta name="description" content="{e(descripcion)}">{robots}'
            f'<link rel="canonical" href="{SITIO}{url}">'
            f'<meta property="og:title" content="{e(titulo)}"><meta property="og:description" content="{e(descripcion)}">'
            f'<meta property="og:type" content="website"><meta property="og:url" content="{SITIO}{url}">'
            f'<meta property="og:site_name" content="{NOMBRE}">{FUENTES}'
            f'<link rel="stylesheet" href="/assets/estilo.css">{extra_head}</head><body>'
            f'{cabecera()}{cuerpo}{pie()}{CONSENTIMIENTO}</body></html>')


# --------------------------------------------------------------- CONTENIDO
def leer_lista(nombre):
    if not os.path.exists(nombre):
        return set()
    with open(nombre, encoding="utf-8") as f:
        return {l.strip() for l in f if l.strip() and not l.startswith("#")}


def leer_clasificacion():
    manual = {}
    if os.path.exists("clasificacion.csv"):
        with open("clasificacion.csv", encoding="utf-8-sig") as f:
            for fila in csv.reader(f, delimiter=";"):
                if len(fila) >= 2 and fila[1].strip() in PILARES:
                    manual[fila[0].strip()] = fila[1].strip()
    return manual


def clasificar(titulo, categoria):
    t = f"{titulo} {categoria}".lower()
    if any(p in t for p in PALABRAS_INVERTIR):
        return "invierte"
    if any(p in t for p in PALABRAS_ORDENA):
        return "ordena"
    return "ahorra"


def a_html(cuerpo_md):
    h = markdown.markdown(cuerpo_md, extensions=["tables"])
    h = h.replace("<blockquote>", '<div class="nota">').replace("</blockquote>", "</div>")
    return h.replace("<table>", '<div class="tabla"><table>').replace("</table>", "</table></div>")


def texto_plano(h):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", h))).strip()


def recortar(texto, n=155):
    return texto if len(texto) <= n else texto[:n].rsplit(" ", 1)[0].rstrip(",;:") + "…"


def leer_articulos(origen, excluir, manual):
    articulos, avisos = [], []
    for nombre in sorted(os.listdir(origen)):
        if not nombre.endswith(".md"):
            continue
        slug = nombre[:-3]
        if slug in excluir:
            avisos.append((slug, "excluido (excluir.txt)"))
            continue
        ruta = os.path.join(origen, nombre)
        with open(ruta, encoding="utf-8") as f:
            limpio, meta, etiquetas = limpiar_articulo(f.read())
        if parece_cortado(limpio):
            avisos.append((slug, "OMITIDO: parece cortado"))
            continue
        lineas = limpio.strip().split("\n")
        titulo = lineas[0].lstrip("#").strip()
        cuerpo = a_html("\n".join(lineas[1:]))
        categoria = ""
        ruta_json = os.path.join(origen, slug + ".json")
        if os.path.exists(ruta_json):
            with open(ruta_json, encoding="utf-8") as f:
                categoria = json.load(f).get("categoria", "")
        m = re.search(r"<p>(.*?)</p>", cuerpo, re.S)
        descripcion = meta or recortar(texto_plano(m.group(1)) if m else titulo)
        articulos.append({
            "slug": slug, "titulo": titulo, "cuerpo": cuerpo, "descripcion": recortar(descripcion),
            "pilar": manual.get(slug) or clasificar(titulo, categoria), "categoria": categoria,
            "fecha": time.strftime("%Y-%m-%d", time.localtime(os.path.getmtime(ruta))),
            "palabras": len(limpio.split()), "etiquetas": etiquetas,
        })
    articulos.sort(key=lambda a: a["fecha"], reverse=True)
    return articulos, avisos


JS_CALC = """(function(){
var eur=function(n){return new Intl.NumberFormat('es-ES',{style:'currency',currency:'EUR',maximumFractionDigits:0}).format(n)};
var pct=function(n){return new Intl.NumberFormat('es-ES',{minimumFractionDigits:2,maximumFractionDigits:2}).format(n)+' %'};
var v=function(id){return parseFloat(String(document.getElementById(id).value).replace(',','.'))||0};
var mensual=function(r){return Math.pow(1+r/100,1/12)-1};
var CALC={
'interes-compuesto':function(){var P=v('capital'),A=v('aporte'),n=v('anos')*12,m=mensual(v('rent'));
 var f=m===0?P+A*n:P*Math.pow(1+m,n)+A*(Math.pow(1+m,n)-1)/m;var ap=P+A*n;
 return [['Capital final',eur(f)],['Total aportado',eur(ap)],['Intereses ganados',eur(f-ap)]]},
'fondo-de-emergencia':function(){var obj=v('gastos')*v('meses'),falta=Math.max(0,obj-v('actual')),a=v('aporte');
 var t=falta===0?'Ya lo has alcanzado':(a>0?Math.ceil(falta/a)+' meses':'Indica cuánto puedes apartar al mes');
 return [['Fondo recomendado',eur(obj)],['Te falta',eur(falta)],['Tiempo para completarlo',t]]},
'objetivo-de-ahorro':function(){var n=v('anos')*12,m=mensual(v('rent')),O=v('objetivo'),P=v('actual');
 if(n<=0)return [['Aportación mensual','Indica un plazo mayor que cero']];
 var q=m===0?(O-P)/n:(O-P*Math.pow(1+m,n))*m/(Math.pow(1+m,n)-1);q=Math.max(0,q);
 return [['Aportación mensual necesaria',eur(q)],['Total que aportarás',eur(q*n)],['Ya cubierto con lo que tienes',eur(Math.min(P,O))]]},
'reparto-del-presupuesto':function(){var i=v('ingresos'),p=[v('p1'),v('p2'),v('p3')],s=p[0]+p[1]+p[2];
 var r=[['Necesidades',eur(i*p[0]/100)],['Deseos',eur(i*p[1]/100)],['Ahorro e inversión',eur(i*p[2]/100)]];
 if(Math.abs(s-100)>0.01)r.push(['Aviso','Los porcentajes suman '+pct(s)+', no 100 %']);return r},
'brecha-de-jubilacion':function(){var n=v('retiro')-v('edad');
 if(n<=0)return [['Aviso','La edad de jubilación debe ser mayor que tu edad actual']];
 var hueco=Math.max(0,v('deseado')-v('pension'));
 if(hueco===0)return [['Hueco mensual a cubrir',eur(0)],['Resultado','Tu pensión ya alcanza el ingreso que quieres']];
 var rr=Math.pow((1+v('rent')/100)/(1+v('infl')/100),1/12)-1,m=v('duracion')*12,N=n*12;
 var cap=rr===0?hueco*m:hueco*(1-Math.pow(1+rr,-m))/rr;
 var q=rr===0?(cap-v('actual'))/N:(cap-v('actual')*Math.pow(1+rr,N))*rr/(Math.pow(1+rr,N)-1);q=Math.max(0,q);
 return [['Hueco mensual a cubrir (bruto, euros de hoy)',eur(hueco)],['Ahorro que necesitas al jubilarte (euros de hoy)',eur(cap)],['Cuánto ahorrar cada mes (euros de hoy)',eur(q)],['Ese capital, en euros de ese año',eur(cap*Math.pow(1+v('infl')/100,n))]]},
'rentabilidad-real':function(){var r=(1+v('nominal')/100)/(1+v('inflacion')/100)-1,n=v('anos'),C=v('capital');
 return [['Rentabilidad real anual',pct(r*100)],['Saldo dentro de '+n+' años',eur(C*Math.pow(1+v('nominal')/100,n))],['Equivale a, en euros de hoy',eur(C*Math.pow(1+r,n))]]}
};
document.addEventListener('DOMContentLoaded',function(){
 var f=document.querySelector('form[data-herramienta]');if(!f)return;
 var out=document.getElementById('resultado');
 var pintar=function(e){if(e)e.preventDefault();
  out.innerHTML=CALC[f.dataset.herramienta]().map(function(x){return '<div style="display:flex;justify-content:space-between;gap:16px;padding:12px 0;border-bottom:1px solid #E4E0D4"><span>'+x[0]+'</span><strong>'+x[1]+'</strong></div>'}).join('')};
 f.addEventListener('submit',pintar);pintar();
});
})();"""


def campo_html(c):
    idc, etiqueta, valor, extra, *resto = c
    ayuda = (f'<span class="muted" style="display:block;font-size:14px;margin:-2px 0 8px">{resto[0]}</span>' if resto else "")
    if extra.startswith("sel:"):
        opciones = "".join(f'<option value="{o}"{" selected" if str(o) == str(valor) else ""}>{o}</option>'
                           for o in extra[4:].split(","))
        control = f'<select id="{idc}" style="width:100%;padding:12px;border:1.5px solid var(--tinta);border-radius:10px;font-size:16px;background:#fff">{opciones}</select>'
    else:
        control = (f'<div style="display:flex;align-items:center;gap:8px"><input id="{idc}" type="number" step="any" min="0" '
                   f'inputmode="decimal" value="{valor}" style="width:100%;padding:12px;border:1.5px solid var(--tinta);'
                   f'border-radius:10px;font-size:16px;background:#fff"><span class="muted">{extra}</span></div>')
    return f'<div style="margin-bottom:18px"><label for="{idc}" style="display:block;font-weight:600;margin-bottom:6px">{etiqueta}</label>{ayuda}{control}</div>'


def pagina_herramienta(h):
    campos = "".join(campo_html(c) for c in h["campos"])
    cuerpo = (f'<main class="wrap sec" style="padding-top:24px"><p class="migas"><a href="/">Inicio</a> › <a href="/herramientas/">Herramientas</a> › {h["nombre"]}</p>'
              f'<h1 style="font-size:44px;margin-bottom:10px">Calculadora de {h["nombre"].lower()}</h1>'
              f'<p class="muted" style="font-size:19px;margin-bottom:{"12px" if h.get("nota") else "32px"}">{h["desc"]}</p>'
              + (f'<p style="background:#fff;border-left:4px solid var(--ambar);padding:12px 16px;margin-bottom:32px;max-width:760px">{h["nota"]}</p>' if h.get("nota") else '')
              +
              '<div style="display:grid;gap:28px;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));align-items:start">'
              f'<form class="card" data-herramienta="{h["slug"]}">{campos}<button class="btn btn-p" type="submit">Calcular</button></form>'
              '<div class="card"><h2 style="font-size:24px;margin-bottom:8px">Resultado</h2>'
              '<div id="resultado" aria-live="polite"></div></div></div>'
              f'<div class="prose" style="margin-top:40px;max-width:760px"><h2>Cómo se calcula</h2><p>{h["como"]}</p></div>'
              '<p class="aviso" style="max-width:760px">Resultado orientativo y con fines educativos. No tiene en cuenta impuestos ni comisiones, y no constituye asesoramiento financiero personalizado.</p>'
              '<script src="/assets/calculadoras.js" defer></script></main>')
    return pagina(f'Calculadora de {h["nombre"].lower()} | {NOMBRE}', h["desc"], f'/herramientas/{h["slug"]}/', cuerpo)


def pagina_herramientas():
    tarjetas = "".join(f'<a class="card" href="/herramientas/{h["slug"]}/"><h3>{h["nombre"]}</h3><p class="muted">{h["desc"]}</p></a>' for h in HERRAMIENTAS)
    cuerpo = ('<main class="wrap sec" style="padding-top:24px"><p class="migas"><a href="/">Inicio</a> › Herramientas</p>'
              '<h1 style="font-size:46px;margin-bottom:12px">Herramientas</h1>'
              '<p class="muted" style="font-size:19px;max-width:620px;margin-bottom:36px">Calculadoras sencillas para decidir con números. Funcionan en tu navegador: no guardamos lo que escribes.</p>'
              f'<div class="grid">{tarjetas}</div></main>')
    return pagina(f"Herramientas | {NOMBRE}", "Calculadoras de finanzas personales: interés compuesto, fondo de emergencia, objetivos de ahorro y más.", "/herramientas/", cuerpo)


# ------------------------------------------------------------- GENERACIÓN
def tarjeta_articulo(a):
    return (f'<a class="card" href="/guias/{a["slug"]}/"><h3>{e(a["titulo"])}</h3>'
            f'<p class="muted">{e(a["descripcion"])}</p><p style="margin-top:14px;color:var(--verde);font-weight:600">Leer guía →</p></a>')


def portada(articulos):
    pasos = "".join(
        f'<div class="card" style="background:var(--crema)"><div class="step">{i}</div>'
        f'<h3 style="font-size:24px">{p[0]}</h3><p class="muted" style="margin-bottom:16px">{p[2]}</p>'
        f'<a href="/ruta/{p[1]}/">Ver guías →</a></div>'
        for i, p in enumerate(PILARES.values(), 1))
    opciones = "".join(
        f'<a class="opt" href="/ruta/{PILARES[k][1]}/">{txt}<b>Paso {i} · {PILARES[k][0]}</b></a>'
        for i, (k, txt) in enumerate([("ordena", "Me cuesta llegar a fin de mes"),
                                       ("ahorra", "Ahorro, pero no sé dónde ponerlo"),
                                       ("invierte", "Quiero empezar a invertir")], 1))
    herr = "".join(f'<a class="card" href="/herramientas/{h["slug"]}/"><h3>{h["nombre"]}</h3><p class="muted">{h["desc"]}</p></a>'
                   for h in HERRAMIENTAS)
    def tarjeta_descarga(n, d, archivo):
        if os.path.isfile(os.path.join("descargas", archivo)):
            return (f'<div class="card"><h3>{n}</h3><p class="muted">{d}</p>'
                    f'<a class="btn" href="/descargas/{archivo}" download>Descargar Excel</a></div>')
        return (f'<div class="card"><h3>{n}</h3><p class="muted">{d}</p>'
                f'<span class="pronto">Próximamente</span></div>')

    desc = "".join(tarjeta_descarga(*x) for x in DESCARGAS)
    recientes = "".join(tarjeta_articulo(a) for a in articulos[:6])
    cuerpo = (
        '<section class="wrap sec hero" style="padding-top:40px;display:grid;gap:48px;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));align-items:center">'
        '<div><p class="kicker">Finanzas personales en España</p>'
        '<h1 style="font-size:56px;margin-bottom:20px">Del primer ahorro a tu primera inversión, euro a euro.</h1>'
        '<p class="muted" style="font-size:19px;max-width:520px;margin-bottom:28px">Guías claras, calculadoras y plantillas para ordenar tu dinero, ahorrar mejor y dar el salto a invertir con criterio.</p>'
        '<a class="btn btn-p" href="#ruta">Empieza por la ruta</a> <a class="btn btn-s" href="#herramientas" style="margin-left:8px">Ver herramientas</a></div>'
        '<div class="card" style="padding:32px"><h2 style="font-size:26px">¿Dónde estás hoy?</h2>'
        f'<p class="muted" style="margin-top:6px">Elige tu punto de partida y te llevamos a la guía adecuada.</p>{opciones}</div></section>'
        '<section id="ruta" class="sec" style="background:#fff;border-top:1px solid var(--borde);border-bottom:1px solid var(--borde)"><div class="wrap">'
        '<p class="kicker">La ruta</p><h2 style="font-size:38px;margin-bottom:12px">Tres pasos, en orden</h2>'
        '<p class="muted" style="max-width:600px;margin-bottom:36px">No hace falta saber de finanzas para empezar. Cada paso prepara el siguiente.</p>'
        f'<div class="grid">{pasos}</div></div></section>'
        f'<section class="wrap sec"><p class="kicker">Guías recientes</p><h2 style="font-size:34px;margin-bottom:28px">Lo último que hemos publicado</h2><div class="grid">{recientes}</div></section>'
        f'<section id="herramientas" class="sec" style="padding-top:0"><div class="wrap"><p class="kicker">Herramientas</p><h2 style="font-size:38px;margin-bottom:32px">Calculadoras para decidir con números</h2><div class="grid">{herr}</div></div></section>'
        f'<section id="descargas" class="sec oscuro"><div class="wrap"><p class="kicker" style="color:var(--ambar)">Descargas</p><h2 style="font-size:38px;margin-bottom:32px">Plantillas de Excel listas para usar</h2><div class="grid">{desc}</div></div></section>'
        + suscripcion())
    return pagina(f"{NOMBRE} — del ahorro a tu primera inversión",
                  "Guías claras, calculadoras y plantillas para ordenar tu dinero, ahorrar mejor y dar el salto a invertir en España.",
                  "/", cuerpo)


def pagina_pilar(clave, articulos):
    nombre, slug, desc = PILARES[clave]
    propios = [a for a in articulos if a["pilar"] == clave]
    lista = "".join(tarjeta_articulo(a) for a in propios) or '<p class="muted">Estamos preparando las primeras guías.</p>'
    cuerpo = (f'<main class="wrap sec" style="padding-top:24px"><p class="migas"><a href="/">Inicio</a> › {nombre}</p>'
              f'<p class="kicker">La ruta</p><h1 style="font-size:46px;margin-bottom:12px">{nombre}</h1>'
              f'<p class="muted" style="font-size:19px;max-width:620px;margin-bottom:36px">{desc}</p><div class="grid">{lista}</div></main>')
    return pagina(f"{nombre} — guías | {NOMBRE}", desc, f"/ruta/{slug}/", cuerpo)


def pagina_articulo(a, articulos):
    nombre, slug, _ = PILARES[a["pilar"]]
    rel = [x for x in articulos if x["pilar"] == a["pilar"] and x["slug"] != a["slug"]][:3]
    relacionados = ('<div class="relacionados"><h2 style="font-size:26px;margin-bottom:16px">Guías relacionadas</h2><div class="grid">'
                    + "".join(tarjeta_articulo(x) for x in rel) + "</div></div>") if rel else ""
    ld = json.dumps({
        "@context": "https://schema.org", "@type": "Article", "headline": a["titulo"],
        "description": a["descripcion"], "datePublished": a["fecha"], "dateModified": a["fecha"],
        "author": {"@type": "Person", "name": AUTOR},
        "publisher": {"@type": "Organization", "name": NOMBRE},
        "mainEntityOfPage": f"{SITIO}/guias/{a['slug']}/",
    }, ensure_ascii=False)
    cuerpo = (f'<main class="articulo"><p class="migas"><a href="/">Inicio</a> › <a href="/ruta/{slug}/">{nombre}</a></p>'
              f'<h1>{e(a["titulo"])}</h1><p class="meta">Por {e(AUTOR)} · {a["fecha"]} · {max(1, a["palabras"] // 200)} min de lectura</p>'
              f'<div class="prose">{a["cuerpo"]}</div>'
              '<p class="aviso">Este artículo tiene una finalidad informativa y educativa general. No constituye asesoramiento '
              'financiero personalizado. Para decisiones concretas sobre tus ahorros o inversiones, consulta con un profesional '
              f'que valore tu situación particular.</p>{relacionados}</main>' + suscripcion("suscripcion"))
    return pagina(f'{a["titulo"]} | {NOMBRE}', a["descripcion"], f'/guias/{a["slug"]}/', cuerpo,
                  extra_head=f'<script type="application/ld+json">{ld}</script>')


def main():
    origen = sys.argv[1] if len(sys.argv) > 1 else ORIGEN
    if not os.path.isdir(origen):
        print(f"❌ No existe la carpeta de artículos: {origen}")
        sys.exit(1)

    articulos, avisos = leer_articulos(origen, leer_lista("excluir.txt"), leer_clasificacion())
    if os.path.isdir(DESTINO) and os.path.basename(DESTINO) == "web":
        shutil.rmtree(DESTINO)

    def escribir(ruta, contenido):
        destino = os.path.join(DESTINO, *ruta.split("/"))
        os.makedirs(os.path.dirname(destino), exist_ok=True)
        with open(destino, "w", encoding="utf-8") as f:
            f.write(contenido)

    escribir("assets/estilo.css", CSS)

    if os.path.isdir("descargas"):
        os.makedirs(os.path.join(DESTINO, "descargas"), exist_ok=True)
        for nombre in sorted(os.listdir("descargas")):
            origen_f = os.path.join("descargas", nombre)
            if os.path.isfile(origen_f):
                shutil.copy2(origen_f, os.path.join(DESTINO, "descargas", nombre))

    # Archivos estáticos (imágenes, fuentes, lo que no genera el script)
    if os.path.isdir("estatico"):
        for raiz, _, archivos in os.walk("estatico"):
            for nombre in archivos:
                origen_f = os.path.join(raiz, nombre)
                relativo = os.path.relpath(origen_f, "estatico")
                destino_f = os.path.join(DESTINO, relativo)
                os.makedirs(os.path.dirname(destino_f), exist_ok=True)
                shutil.copy2(origen_f, destino_f)
    escribir("index.html", portada(articulos))
    for clave, (_, slug, _) in PILARES.items():
        escribir(f"ruta/{slug}/index.html", pagina_pilar(clave, articulos))
    for a in articulos:
        escribir(f"guias/{a['slug']}/index.html", pagina_articulo(a, articulos))
    escribir("assets/calculadoras.js", JS_CALC)
    escribir("herramientas/index.html", pagina_herramientas())
    for h in HERRAMIENTAS:
        escribir(f"herramientas/{h['slug']}/index.html", pagina_herramienta(h))
    ESTILO_LEGAL = (
        '<style>.sec table{border-collapse:collapse;width:100%;margin:14px 0;font-size:15px}'
        '.sec th,.sec td{border:1px solid var(--borde);padding:10px 12px;text-align:left;vertical-align:top}'
        '.sec th{background:#F3EDDD;font-weight:600}'
        '.sec h2{margin-top:28px;font-size:22px}'
        '.sec ul,.sec ol{margin:10px 0 10px 22px}'
        '.sec li{margin-bottom:6px}'
        '.sec p{line-height:1.65}</style>'
    )
    for slug, titulo in PAGINAS_PENDIENTES.items():
        if slug in PAGINAS_LEGALES:
            _, descripcion, cuerpo = PAGINAS_LEGALES[slug]
            escribir(f"{slug}/index.html",
                     pagina(f"{titulo} | {NOMBRE}", descripcion, f"/{slug}/", cuerpo,
                            extra_head=ESTILO_LEGAL))
            continue
        cuerpo = (f'<main class="wrap sec" style="padding-top:24px"><h1 style="font-size:42px;margin-bottom:16px">{titulo}</h1>'
                  '<p class="muted">Página en preparación.</p></main>')
        escribir(f"{slug}/index.html", pagina(f"{titulo} | {NOMBRE}", titulo, f"/{slug}/", cuerpo, noindex=True))
    escribir("404.html", pagina(f"Página no encontrada | {NOMBRE}", "Página no encontrada", "/404.html",
             '<main class="wrap sec"><h1 style="font-size:42px;margin-bottom:16px">No encontramos esa página</h1>'
             '<p><a class="btn btn-p" href="/">Volver al inicio</a></p></main>', noindex=True))

    urls = (["/", "/herramientas/"] + [f"/ruta/{p[1]}/" for p in PILARES.values()]
            + [f"/herramientas/{h['slug']}/" for h in HERRAMIENTAS] + [f"/guias/{a['slug']}/" for a in articulos])
    hoy = time.strftime("%Y-%m-%d")
    escribir("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
             + "".join(f"<url><loc>{SITIO}{u}</loc><lastmod>{hoy}</lastmod></url>" for u in urls) + "</urlset>")
    escribir("robots.txt", f"User-agent: *\nAllow: /\n\nSitemap: {SITIO}/sitemap.xml\n")

    with open("informe_web.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["slug", "pilar", "categoria_original", "palabras", "titulo"])
        for a in articulos:
            w.writerow([a["slug"], a["pilar"], a["categoria"], a["palabras"], a["titulo"]])

    print(f"✅ Web generada en '{DESTINO}': {len(articulos)} artículos, {len(urls)} páginas indexables.")
    for clave, (nombre, _, _) in PILARES.items():
        print(f"   {nombre}: {sum(1 for a in articulos if a['pilar'] == clave)} guías")
    for slug, motivo in avisos:
        print(f"   ⚠ {slug}: {motivo}")
    print("Revisa informe_web.csv. Para verla en tu PC:  python -m http.server 8000 --directory web")


if __name__ == "__main__":
    main()
