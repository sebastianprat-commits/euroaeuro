# Textos legales de euroaeuro.eu (persona física)
# Se insertan en construir_web.py como constante PAGINAS_LEGALES.

TITULAR = "Sebastián Prat"
NIF = "09004397N"
DOMICILIO = "Avda. Utretch 22, 28514 Nuevo Baztán (Madrid)"
EMAIL = "sebastian.prat@gmail.com"
SITIO = "euroaeuro.eu"
ACTUALIZADO = "10 de noviembre de 2026"

PAGINAS_LEGALES = {}

PAGINAS_LEGALES["aviso-legal"] = (
    "Aviso legal",
    "Titular, condiciones de uso y limitación de responsabilidad de euroaeuro.eu.",
    f"""
<main class="wrap sec" style="padding-top:24px">
<h1>Aviso legal</h1>
<p class="muted">Última actualización: {ACTUALIZADO}</p>

<h2>Titular del sitio</h2>
<p>En cumplimiento del artículo 10 de la Ley 34/2002 de Servicios de la Sociedad de la
Información y de Comercio Electrónico (LSSI-CE), se informa:</p>
<ul>
  <li><strong>Titular:</strong> {TITULAR}</li>
  <li><strong>NIF:</strong> {NIF}</li>
  <li><strong>Domicilio:</strong> {DOMICILIO}</li>
  <li><strong>Correo electrónico:</strong> {EMAIL}</li>
  <li><strong>Sitio web:</strong> {SITIO}</li>
</ul>
<p>Se trata de una persona física que actúa como particular. No es una sociedad mercantil,
no presta servicios de inversión, no gestiona dinero de terceros y no capta fondos del público.</p>

<h2>Objeto</h2>
<p>Este sitio publica contenido informativo y educativo sobre finanzas personales: guías,
calculadoras y plantillas descargables. El acceso es libre y gratuito, salvo el coste de la
conexión a internet del usuario.</p>

<h2>Condiciones de uso</h2>
<p>El acceso a {SITIO} atribuye la condición de usuario e implica la aceptación de este aviso
legal. El usuario se compromete a hacer un uso diligente de los contenidos y a no emplearlos
para actividades ilícitas, contrarias a la buena fe o que puedan dañar los derechos de terceros.</p>

<h2>Propiedad intelectual</h2>
<p>Los textos, las calculadoras, las plantillas y el diseño del sitio son de su titular o se
utilizan con autorización. Se permite su consulta y el uso personal de las plantillas
descargables. No se permite su reproducción masiva, su redistribución comercial ni su uso para
entrenar modelos sin autorización expresa.</p>

<h2>Exclusión de responsabilidad</h2>
<p>El contenido tiene <strong>carácter informativo y educativo</strong> y <strong>no constituye
asesoramiento financiero, fiscal, jurídico ni una recomendación de inversión personalizada</strong>.
No se adapta a la situación concreta de ninguna persona. Las decisiones que se tomen a partir de
este contenido son responsabilidad exclusiva del usuario.</p>
<p>Las simulaciones y ejemplos son ilustrativos, se basan en supuestos simplificados y no
garantizan resultados futuros. La rentabilidad pasada no asegura rentabilidad futura. La
normativa fiscal y financiera cambia: comprueba siempre la vigencia de los datos antes de actuar.</p>
<p>El titular no se responsabiliza de interrupciones del servicio, errores de terceros ni del
contenido de los sitios enlazados.</p>

<h2>Enlaces</h2>
<p>El sitio puede incluir enlaces a páginas de terceros. El titular no controla ni responde de
su contenido, sus políticas de privacidad o sus prácticas.</p>

<h2>Legislación aplicable</h2>
<p>Esta relación se rige por la legislación española. Para cualquier controversia serán
competentes los juzgados y tribunales de Madrid, salvo que la ley disponga otro fuero.</p>
</main>
""",
)

PAGINAS_LEGALES["privacidad"] = (
    "Política de privacidad",
    "Qué datos se recogen en euroaeuro.eu, para qué, durante cuánto tiempo y cómo ejercer tus derechos.",
    f"""
<main class="wrap sec" style="padding-top:24px">
<h1>Política de privacidad</h1>
<p class="muted">Última actualización: {ACTUALIZADO}</p>

<h2>Quién es el responsable</h2>
<p>{TITULAR}, con NIF {NIF} y domicilio en {DOMICILIO}. Puedes escribir a
<strong>{EMAIL}</strong> para cualquier cuestión sobre tus datos.</p>

<h2>Qué datos se tratan y para qué</h2>
<table>
  <tr><th>Finalidad</th><th>Datos</th><th>Base legal</th><th>Conservación</th></tr>
  <tr>
    <td>Enviarte la newsletter</td>
    <td>Dirección de correo electrónico y fecha de alta</td>
    <td>Tu consentimiento</td>
    <td>Hasta que te des de baja</td>
  </tr>
  <tr>
    <td>Medir las visitas con Google Analytics</td>
    <td>Datos de navegación: páginas vistas, dispositivo, ubicación aproximada e identificadores
        de cookie</td>
    <td>Tu consentimiento</td>
    <td>Hasta 14 meses</td>
  </tr>
  <tr>
    <td>Responder a tus mensajes</td>
    <td>Tu correo y el contenido del mensaje</td>
    <td>Consentimiento o interés legítimo en atenderte</td>
    <td>Mientras dure la conversación</td>
  </tr>
</table>
<p>No se elaboran perfiles comerciales con tus datos, no se usan para decisiones automatizadas
y no se venden a terceros.</p>

<h2>Quién más los ve</h2>
<p>Para que el sitio funcione, estos proveedores tratan datos por cuenta del responsable:</p>
<ul>
  <li><strong>MailerLite Limited</strong> (Irlanda) — envío de la newsletter y gestión de la lista.
      Actúa como encargado del tratamiento. <a href="https://www.mailerlite.com/legal/privacy-policy" rel="noopener" target="_blank">Su política</a>.</li>
  <li><strong>Google Ireland Limited</strong> — analítica web (Google Analytics 4). Actúa como
      encargado. <a href="https://policies.google.com/privacy" rel="noopener" target="_blank">Su política</a>.</li>
  <li><strong>GitHub, Inc.</strong> — alojamiento del sitio estático. No recibe datos de formularios;
      solo registra peticiones técnicas como cualquier servidor.</li>
</ul>
<p>Algunos de estos proveedores están fuera del Espacio Económico Europeo. Las transferencias se
amparan en el Marco de Privacidad de Datos UE-EEUU o en cláusulas contractuales tipo aprobadas
por la Comisión Europea.</p>

<h2>Tus derechos</h2>
<p>Puedes solicitar el acceso, la rectificación, la supresión, la limitación, la oposición y la
portabilidad de tus datos. Escribe a <strong>{EMAIL}</strong> indicando qué derecho ejercitas.
Responderemos en el plazo máximo de un mes.</p>
<p>Puedes retirar tu consentimiento en cualquier momento: con el enlace de baja que acompaña a
cada correo o escribiendo al mismo email. La retirada no afecta al tratamiento hecho hasta ese
momento.</p>
<p>Si consideras que no te hemos atendido correctamente, puedes reclamar ante la
<strong>Agencia Española de Protección de Datos</strong>
(<a href="https://www.aepd.es" rel="noopener" target="_blank">aepd.es</a>).</p>

<h2>Menores</h2>
<p>El contenido no está dirigido a menores de 14 años y no se recogen datos de menores de esa
edad de forma consciente. Si eres madre, padre o tutor y crees que un menor se ha suscrito,
escríbenos y lo eliminamos.</p>

<h2>Seguridad</h2>
<p>El sitio se sirve por HTTPS. Los datos de suscripción se alojan en MailerLite, que aplica
cifrado y controles de acceso. Ningún sistema es infalible, pero se aplican medidas razonables
y proporcionadas al tamaño de este proyecto.</p>

<h2>Cambios</h2>
<p>Si cambia esta política, se actualizará la fecha del encabezado. Los cambios sustanciales se
avisarán por correo a las personas suscritas.</p>
</main>
""",
)

PAGINAS_LEGALES["cookies"] = (
    "Política de cookies",
    "Qué cookies usa euroaeuro.eu, para qué y cómo aceptarlas o rechazarlas.",
    f"""
<main class="wrap sec" style="padding-top:24px">
<h1>Política de cookies</h1>
<p class="muted">Última actualización: {ACTUALIZADO}</p>

<h2>Qué son</h2>
<p>Una cookie es un archivo pequeño que un sitio guarda en tu navegador. Sirve para recordar
cosas entre visitas: por ejemplo, que ya has aceptado el aviso de cookies.</p>

<h2>Cuáles usa este sitio</h2>
<p><strong>Necesarias.</strong> Guardan tu decisión sobre el aviso de cookies en el
almacenamiento local del navegador. Sin ellas, el aviso aparecería en cada página. No se
comparten con nadie y no identifican a la persona.</p>
<p><strong>Analíticas (solo si las aceptas).</strong></p>
<table>
  <tr><th>Cookie</th><th>Titular</th><th>Finalidad</th><th>Duración</th></tr>
  <tr><td>_ga</td><td>Google</td><td>Distinguir usuarios para contar visitas</td><td>2 años</td></tr>
  <tr><td>_ga_*</td><td>Google</td><td>Mantener el estado de la sesión de analítica</td><td>2 años</td></tr>
</table>
<p>No se usan cookies publicitarias, ni de redes sociales, ni de perfilado.</p>
<p><strong>Al enviar el formulario</strong>, el envío se procesa en MailerLite, que puede dejar
cookies técnicas propias en su dominio para confirmar la operación. No se activan por el simple
hecho de visitar la web.</p>

<h2>Cómo decidir</h2>
<p>Al entrar por primera vez verás un aviso con dos botones: <strong>Aceptar</strong> o
<strong>Solo lo necesario</strong>. Mientras no aceptes, Google Analytics <strong>no se carga</strong>:
no se envía ningún dato.</p>
<p>Puedes cambiar de opinión borrando los datos del sitio en tu navegador. El aviso volverá a
aparecer y podrás elegir otra vez.</p>
<ul>
  <li><a href="https://support.google.com/chrome/answer/95647" rel="noopener" target="_blank">Chrome</a></li>
  <li><a href="https://support.mozilla.org/es/kb/borrar-cookies-y-datos-sitios-firefox" rel="noopener" target="_blank">Firefox</a></li>
  <li><a href="https://support.apple.com/es-es/guide/safari/sfri11471/mac" rel="noopener" target="_blank">Safari</a></li>
  <li><a href="https://support.microsoft.com/es-es/microsoft-edge" rel="noopener" target="_blank">Edge</a></li>
</ul>
<p>También puedes instalar la
<a href="https://tools.google.com/dlpage/gaoptout" rel="noopener" target="_blank">extensión de
inhabilitación de Google Analytics</a>.</p>

<h2>Más información</h2>
<p>El detalle de qué datos se tratan y cómo ejercer tus derechos está en la
<a href="/privacidad/">política de privacidad</a>.</p>
</main>
""",
)

PAGINAS_LEGALES["contacto"] = (
    "Contacto",
    "Cómo escribir a Euro a Euro para dudas, sugerencias o ejercicio de derechos.",
    f"""
<main class="wrap sec" style="padding-top:24px">
<h1>Contacto</h1>
<p>Para dudas, sugerencias, correcciones o para ejercer tus derechos sobre datos personales:</p>
<p style="font-size:22px;font-weight:600;margin:18px 0">
  <a href="mailto:{EMAIL}">{EMAIL}</a>
</p>
<p>Titular: {TITULAR} · NIF {NIF} · {DOMICILIO}</p>

<h2>Qué puedes escribirme</h2>
<ul>
  <li>Errores o imprecisiones en una guía o en una calculadora. Se agradecen especialmente.</li>
  <li>Dudas sobre el funcionamiento de una plantilla descargable.</li>
  <li>Bajas de la newsletter (aunque es más rápido con el enlace del propio correo).</li>
  <li>Ejercicio de derechos de acceso, rectificación, supresión u oposición.</li>
</ul>

<h2>Qué no puedo hacer por email</h2>
<p>No respondo consultas de asesoramiento financiero personalizado: ni qué producto contratar,
ni cómo invertir tu dinero, ni qué hacer con tu situación fiscal concreta. Este sitio es
divulgación, no asesoramiento, y responder por correo a un caso particular sería justo lo
contrario de lo que defiende.</p>
<p>Si tu consulta es de ese tipo, lo razonable es acudir a un profesional que pueda analizar tu
caso con los datos completos y asumir la responsabilidad de la recomendación.</p>

<h2>Plazo de respuesta</h2>
<p>Intento contestar en dos o tres días laborables. En periodos de mucho trabajo puede tardar
algo más; si es urgente, dilo en el asunto.</p>
</main>
""",
)
