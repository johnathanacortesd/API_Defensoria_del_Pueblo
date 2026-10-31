# Defensoría del Pueblo — Limpieza y Análisis de Noticias

App Streamlit basada en **API_2_Grill v4.67**, adaptada a un solo cliente,
con una función nueva en la **v1.0**: **Resumen para informe** a partir de
un xlsx corregido.

## Cliente y enfoque

| Campo | Valor |
|---|---|
| Marca | Defensoría del Pueblo |
| Alias / palabras relacionadas | Defensoría, la Defensoría, Defensoría del Pueblo de Colombia, defensoría delegada, defensor regional |
| Voceros | Iris Marín Ortiz (defensora del Pueblo, verificada en 2026) |
| Criterio de tono | Aspectual estricto (recomendado) |
| Perfil | `clientes/defensoria_del_pueblo.json` |

Enfoque: el análisis mide el tono **solo sobre la marca, sus alias y sus
voceros**, no sobre la noticia en general, y con especial atención a lo
que dicen para la Defensoría y para las palabras similares relacionadas
(defensoría delegada, defensor regional). No confundir con defensorías
de otros países ni con la Procuraduría o las personerías: son entidades
distintas. El resto del motor (agrupación, tono/tema/subtema, guarda
positiva, anti-copia) es el de Grill v4.67 sin cambios.

## Resumen para informe (lo nuevo en v1.0)

Al final de la página, en **📝 Resumen para informe**:

1. Resube el **xlsx corregido** (el que ya trae `Tono_IA`, `Subtema_IA` y
   `Contexto analizado`).
2. Solo se lee la **primera hoja, sin importar su nombre**. Si el archivo
   trae más hojas, se ignoran y la app avisa cuántas ignoró.
3. La app calcula, sin IA:
   - el **tono dominante** de `Tono_IA` (el que más apariciones tiene) y
     su porcentaje sobre el total de filas con `Tono_IA`, con el formato
     pedido: `51 %` (espacio antes del símbolo, entero redondeado);
   - el **subtema con más apariciones** de `Subtema_IA` (desempate: el que
     aparece primero en el archivo).
4. Con la API (`gpt-6-luna`, la misma de Grill) redacta dos párrafos:
   - **Párrafo 1**, con plantilla fija:
     > En el reciente periodo, la visibilidad de la Defensoría del Pueblo
     > en medios tradicionales registró un tono neutro del 51 %,
     > impulsado por noticias relacionadas a […].
     
     El fragmento entre corchetes se redacta con la API a partir de los
     `Contexto analizado` del subtema principal y **debe medir entre 140
     y 160 caracteres** (la app muestra el conteo y reintenta hasta 3
     veces si no cae en rango).
   - **Párrafo 2**, también con la API, que empieza siempre con
     “En términos generales, la agenda mediática se centró en …” y
     resume los subtemas destacados siguientes (puestos 2 a 5; si solo
     hay un subtema, se usa ese).
5. El texto queda en un cuadro para copiar y se puede descargar como
   `.txt`. Las tablas de conteos quedan visibles para auditar el
   porcentaje y el subtema principal.

Sin `OPENAI_API_KEY` la sección no falla: genera un resumen extractivo
(recorte de `Contexto analizado`, sin inventar texto) y lo marca
claramente como “sin IA”. La vía principal, con clave, es la API.

La lógica vive en `resumen_informe.py` (funciones puras, probables sin
Streamlit) y la interfaz en `app.py` (`render_resumen_tab`).

## Conexión manual en Streamlit

1. En Streamlit Cloud, **New app → Deploy** apuntando a este repo, rama
   `main`, archivo principal `app.py`.
2. En **Settings → Secrets**, configura los mismos Secrets que usa
   API_2_Grill (`APP_PASSWORD`, `OPENAI_API_KEY`, y los de configuración
   de regiones/internet). Para usar **solo** el Resumen para informe
   bastan `APP_PASSWORD` y `OPENAI_API_KEY`.
3. El resto del flujo (dossier estándar / columnas personalizadas) es
   el de API_2_Grill: elige el perfil único de este cliente antes de
   procesar.

## Archivos

- `app.py` — interfaz (Grill v4.67 + sección Resumen, versión visible v1.13)
- `resumen_informe.py` — lectura de primera hoja, conteos y redacción
- `clientes/` — solo el perfil de este cliente
- `analyzer_tono_tema.py`, `pipeline.py`, `ai_analyzer.py`,
  `catalogo_tono_tema.py`, `perfil_cliente.py`, `pkl_classifier.py`,
  `historial_cliente.py`, `auditoria_mail.py` — motor Grill v4.67
- `SPEC_TONO_TEMA.md` — especificación de tono/tema heredada de Grill
- `requirements.txt` — dependencias (Streamlit, pandas, openpyxl, openai…)

## Novedades v1.1 (2026-10-30, pendiente de push)

- Sigla **DP** agregada como alias; "la Defensoría" ya estaba como alias
  y se mantiene como forma habitual de mención.
- La comparación de marca/alias/vocero ya era sin mayúsculas ni acentos
  (se normaliza antes de comparar); se verificó con pruebas: valen
  "iris marín" en minúsculas, "IRIS MARÍN ORTIZ" y "Iris Marín"
  (nombre + primer apellido), además del nombre completo.
- Corrección general en estos dos repos (no en Grill): las siglas de 2
  letras ya cuentan en título y en Contexto analizado (antes se exigían
  3 caracteres y "DP" se caía); los bordes de palabra evitan que "DP"
  cuente dentro de otra palabra, y Procuraduría/Personerías siguen sin
  contar.
- **Alertas Tempranas como subtema clave**: el perfil trae
  `guia_subtema` y el prompt del modelo la recibe como guía propia de
  este cliente. Cuando el hecho principal sea que la Defensoría emite,
  actualiza o advierte mediante una Alerta Temprana, el subtema debe
  identificarla explícitamente (ej. "Alerta Temprana en Cauca"), sin
  inventar número ni zona que no aparezcan en el cuerpo.

## Novedades v1.2 (2026-10-30, pendiente de push)

- Aviso de cliente en todas las pantallas: en la pantalla de contraseña
  ("Sistema de Limpieza y Análisis") aparece "📍 App de: Defensoría del
  Pueblo", y tras ingresar queda un aviso permanente con el mismo texto
  (fuera del contenedor que se borra al procesar, así que también se ve
  durante el procesamiento y en la vista de resultados) y en el pie de
  página. Las dos apps comparten diseño y título de sistema, por eso el
  aviso es explícito y no depende solo del encabezado.

## Novedades v1.3 (2026-10-30, pendiente de push)

- Corrección de la v1.2: el aviso permanente tras ingresar se había
  escrito como texto plano sin `f`, así que en pantalla salía literal
  "{CLIENTE_NOMBRE}" en vez del nombre. Ahora es f-string en los tres
  sitios (contraseña, aviso permanente y pie) y se verifica el texto
  renderizado, no solo el código fuente.

## Novedades v1.4 (2026-10-30, pendiente de push)

- El selector "Perfil de cliente" de la pestaña "Dossier estándar" ahora
  sale por defecto con el perfil de esta app ("Defensoría del Pueblo"),
  en vez de "Sin perfil (configuración manual)". Al abrir, la marca, los
  alias, los voceros, el criterio y la guía de Alertas Tempranas quedan
  precargados; "Sin perfil" sigue disponible si se quiere configurar a
  mano.

## Novedades v1.5 (2026-10-30, pendiente de push)

- Alertas Tempranas, subtema unificado: toda noticia cuyo hecho principal
  sea una Alerta Temprana de la Defensoría —incluida la Alerta Temprana
  028 de 2026 y cualquier otra similar, sin importar número, año o
  zona— queda con el subtema exacto "Alertas Defensoría del Pueblo".
  Ya no se parte por zona ("Alerta Temprana en Cauca" / "en Chocó").
  La regla es doble: la guía del perfil le dice al modelo que use ese
  texto exacto, y un pase determinista del motor lo impone después del
  etiquetado aunque el modelo devuelva variantes. Como el subtema queda
  unificado antes de asignar temas, el Tema_IA también queda igual para
  todas esas noticias. Las noticias sin Alerta Temprana no se tocan.
- Ajuste general del motor (no atado a este cliente): "alerta" pasa a
  ser sustantivo de hecho, así que una etiqueta que empieza por ella ya
  no se marca como "lista de nombres sin hecho" ni cae a "Hecho
  informativo" en la puerta final. Sin este ajuste, la etiqueta fija
  habría sido descartada por esa puerta.

## Novedades v1.6 (2026-10-30, pendiente de push; incluye la v1.5, aún sin publicar)

- Incluye la v1.5 (Alertas Tempranas con subtema fijo) que estaba
  pendiente de push.
- Soporte de motor para TIPO y GÉNERO (nuevo en v1.6), desactivado en
  este repo: la salida de Defensoría no cambia.

## Novedades v1.7 (2026-10-31, pendiente de push; solo Defensoría)

- Comparativo con Google Sheets (igual que Secretaría v1.8): antes de
  procesar, la app compara la columna NoticiaId del dossier con la
  columna ID de la hoja de notas ya analizadas de Defensoría
  (primera hoja) y solo procesa las notas que NO están en la hoja.
  La hoja se lee en cada corrida vía exportación CSV pública (sin
  inicio de sesión) y solo se parsea la columna ID; la detección de
  la columna acepta "ID", "ID Noticia" y "NoticiaId". Opción "Excluir
  notas ya analizadas (Google Sheets)" en ambas pestañas (activada por
  defecto); si la hoja no se puede leer, el proceso se detiene con un
  mensaje claro y desmarcando la opción se procesan todas las notas.
  El límite de 1.000 filas aplica a las notas NUEVAS.
- Orden del xlsx final para el boletín (por perfil "formato_boletin"):
  ID Noticia, Fecha, Medio, Región, Tipo de Medio, Sección - Programa,
  Título, Duración - Nro. Caracteres, CPE, Audiencia, Tier, Tono_IA,
  Subtema_IA, Link Nota, texto, Link (Streaming - Imagen), Link Ext,
  FECHA INFORME, HORA B, ID duplicada, Contexto analizado,
  Resumen - Aclaracion, Audio. Sin TIPO ni GÉNERO (Defensoría no los
  clasifica) y sin Web Ext. FECHA INFORME es la Fecha de la nota;
  HORA B es "1:00 p.m." antes de la 1 p.m. de Bogotá y "6:00 p.m."
  desde la 1 p.m. En la pestaña personalizada van estas columnas
  primero y después las personalizadas extra.
- Mismo Título => mismo Subtema_IA (igual que Secretaría v1.10): pase
  final determinista después de la puerta anti-copia y antes de
  volcar, sin LLM y sin guarda de fidelidad; solo toca el subtema.
- La regla de Alertas Temprana (subtema exacto "Alertas Defensoría del
  Pueblo") queda intacta. Secretaría no se toca.

## Novedades v1.8 (2026-10-31, nunca pusheada; incluida en v1.9; solo Defensoría)

- Sin cambios de foco: el perfil ya era exactamente el indicado por el
  usuario (Defensoría, la Defensoría, Defensoría del Pueblo,
  Defensoría del Pueblo de Colombia, defensoría delegada, defensor
  regional, DP; Iris Marín Ortiz, Iris Marín). Se mantienen el filtro
  Sheets, el boletín de 23 columnas y la regla de Alertas Temprana.
- Tono: misma regla general determinista que Secretaría v1.12
  (decreto/resolución/acuerdo/ordenanza sin crítica = Neutro).
- Velocidad: misma paralelización de las auditorías Jev que
  Secretaría v1.12 (mismas llamadas y resultados, solo menos tiempo).
- Secretaría no se toca.

## Novedades v1.9 (2026-10-31, nunca pusheada; incluida en v1.10; solo Defensoría)

- Incluye todo lo de v1.8 (regla decreto, Jev paralelo), que nunca se
  pusheó.
- Web Ext como ÚLTIMA columna del boletín (tras Audio): 24 columnas
  (sin TIPO/GÉNERO). La guardia de género por URL no tiene efecto aquí
  (Defensoría no clasifica género), pero el motor es idéntico.
- Fidelidad FINAL por fila: igual que Secretaría v1.13 (mismo motor):
  ningún Subtema_IA llega al Excel si no corresponde a su fila
  (título/cuerpo); si no corresponde, la fila recupera su rótulo
  propio. Misma nota: Grill comparte este motor y le corresponde el
  mismo arreglo en su próxima versión (no se toca aquí).
- Secretaría no se toca (salvo el motor compartido, que es idéntico).

## Novedades v1.10 (2026-10-31, nunca pusheada; incluida en v1.11; solo Defensoría)

- Incluye todo lo de v1.9 (nunca pusheada).
- HORA B del boletín: en la tarde dice "4:00 p.m." (antes "6:00 p.m."),
  por pedido del usuario 2026-10-31. La mañana no cambia: antes de la
  1 p.m. de Bogotá sigue "1:00 p.m.". Implementado como campo genérico
  de perfil `hora_boletin_tarde` (por defecto "6:00 p.m."; Defensoría
  lo trae en "4:00 p.m."), plomado perfil -> app -> pipeline, sin
  hardcodear el cliente en el motor. Secretaría sigue en "6:00 p.m.".
- Secretaría no se toca (salvo el motor compartido, que es idéntico).

## Novedades v1.11 (2026-10-31, PUSH HECHO, solo Defensoría)

- Incluye todo lo de v1.10 (nunca pusheada).
- HORA B del boletín por horario de perfil (campo genérico, sin
  hardcodear el cliente): corte 16, antes "4:00 p.m.", después
  "8:00 a.m.". O sea: si se corre antes de las 4 p.m. dice
  "4:00 p.m." (el boletín que se arma en el día); si se corre desde
  las 4 p.m. dice "8:00 a.m." (el boletín que se arma tras la
  descarga de las 4 p.m.). La mañana de Secretaría no cambia
  (corte 13, 1:00 p.m. / 6:00 p.m.).
- Secretaría no se toca (salvo el motor compartido, que es idéntico).

## Novedades v1.12 (2026-10-31, PUSH HECHO, solo Defensoría)

- FECHA INFORME es la fecha de procesamiento (Bogotá, mismo instante
  que HORA B), NO la Fecha de la nota: todas las filas llevan la
  misma fecha, la del día en que se corrió. Antes llevaba la Fecha
  de cada nota (v1.7). HORA B no cambia (corte 16, 4:00 p.m. /
  8:00 a.m.), confirmado por el usuario 2026-10-31.
- Secretaría no se toca (salvo el motor compartido, que es idéntico).

## Novedades v1.13 (2026-10-31, pendiente de push; solo Defensoría)

- Igual que Secretaría v1.17 (mismo motor): columna "ENLACE" como
  texto plano, sin hipervínculo (cualquier capitalización). Link
  Nota, Link Ext, Web Ext y Audio no cambian.
- Secretaría no se toca (salvo el motor compartido, que es idéntico).
