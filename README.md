# Defensoría del Pueblo — Limpieza y Análisis de Noticias

App Streamlit basada en **API_2_Grill v4.67**, adaptada a un solo cliente,
con una función nueva en la **v1.0**: **Resumen para informe** a partir de
un xlsx corregido.


## Agilidad, medición por etapa y pantalla de resultados (portado de API_2_Grill)

- **Clasificación en paralelo.** Con 100 o más noticias, hasta 4 agentes
  Haiku clasifican tramos a la vez; un agente de cierre recoge lo pendiente
  y revisa la consistencia entre tramos. `paralelo: 1` vuelve a un agente.
- **Auditor de tono y evaluador de agrupación a la vez.**
- **Memoria del cliente** (`memoria_cliente.py`): una noticia ya clasificada
  con la misma configuración no vuelve al modelo. Caduca a los 45 días y se
  invalida si cambia la configuración o las instrucciones del motor. Se
  apaga con la casilla «Reutilizar clasificaciones previas» o
  `memoria: false`.
- **Candidatos por matriz** de rapidfuzz en el revisor y el evaluador
  (mismo resultado que antes).
- **Medición por etapa**: `process_dossier` devuelve `tiempos`.
- **Pantalla de resultados**: distribución de tono, tabla de subtemas,
  noticias clasificadas con filtro, pestaña «Para revisar», tiempo por etapa
  e historial como tabla.

## Tono por rol, auditor de tono y una noticia = un subtema (portado de API_2_Grill)

Se conserva todo lo que esta app ya hacía; se suma:

- **Tono por rol del cliente.** El agente Haiku decide primero el papel de la
  marca, alias o vocero en la nota (`gestion`, `logro` = Positivo; `critica`,
  `afectacion` = Negativo; `equilibrada`, `referencial` = Neutro) y el tono
  sale de ahí. `guardar_clasificacion` rechaza la fila si no coinciden. El
  criterio de tono del perfil sigue mandando en los casos que nombre.
- **Auditor de tono** (`motor_haiku.auditar_tono`): verifica los Negativos,
  los tonos sin mención literal del cliente, los Positivos sin el cliente en
  el título y los subtemas con tonos distintos. Se apaga con
  `auditor_tono: false` en `ai_config`.
- **Subagentes con contexto.** `revisor-subtemas` y `evaluador-agrupacion`
  reciben cliente, alias, voceros y criterio en su propio pedido.
- **Subtema preciso.** Hecho + objeto + dato distintivo, con prueba de
  precisión; "mismo hecho" exige el mismo evento, actores, lugar y momento.
- **Una noticia = un subtema, un tono y un tema** (`unificar_por_noticia`,
  pase final de Grill v4.72): las noticias iguales o realmente similares
  (mismo titular comparable, mismo CuerpoEs, pasaje literal compartido o
  texto muy parecido) terminan con un solo subtema. Nunca une dos notas del
  mismo molde con lugar o persona distintos.

Banco de pruebas sin API (`python3 tools/banco_agrupacion.py --semillas 5`),
86 noticias con varias notas: subtema partido 11 -> 0, fusiones de noticias
distintas 7 -> 6, filas con un subtema correcto 86,5 % -> 91,8 %.

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

## Motor Claude Haiku

En la pestaña estándar, «Motor de clasificación» ofrece dos opciones:

- **OpenAI Luna**: el motor anterior (gpt-6-luna + Jev + PKL). Opcional; **Claude Haiku es el valor por defecto**.
- **Claude Haiku (agente + revisor)**: un agente Claude Haiku (`motor_haiku.py`, Claude Agent SDK) clasifica Tono_IA, Subtema_IA y, si se pide, Tema_IA (de la lista de Temas cuando se elige una). Al final un subagente `revisor-subtemas` revisa la consistencia. La limpieza, el Contexto analizado, el agrupamiento, las guardas deterministas de tono y subtema y el layout del Excel son los mismos. No usa PKL ni Jev.

El motor Haiku se factura a la clave de Claude Platform. Agrega en los Secrets de Streamlit:

```toml
ANTHROPIC_API_KEY = "sk-ant-..."
```

Sin esa clave, elegir Claude Haiku muestra un error y el motor OpenAI sigue funcionando.

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

## Novedades v1.26 (2026-11-02; solo Defensoría)

Se replican las mejoras de tono y subtema de Secretaría (v1.29 a v1.31),
sin TIPO/GÉNERO (este perfil no los usa) y sin tocar HORA B (8:00 a.m. /
4:00 p.m., cortes 8 y 16).

- **Agrupación estricta** (`agrupacion_estricta: true` en el perfil): dos
  noticias comparten subtema SOLO con evidencia: título igual o muy
  parecido, Contexto analizado con pasajes literales compartidos o
  CuerpoEs igual o muy parecido. Se omiten las uniones por parecido del
  rótulo y por "ancla" temática; los pases finales por título usan el
  mismo umbral estricto. Las notas que no se parecen a otras conservan
  su subtema. La regla fija de Alertas Tempranas ("Alertas Defensoría
  del Pueblo") se mantiene.
- **Coherencia por noticia**: misma noticia => mismo subtema (si hay un
  rótulo fiel a todas) y mismo tono; noticias distintas con el mismo
  subtema conservan cada una su tono.
- **Tono enfocado en marca, alias y voceros**:
  - Las reglas de "crítica dirigida a la marca" ahora cuentan a la
    vocera (Iris Marín): antes una crítica a ella podía bajar a Neutro;
    y "cuestionan a la Defensoría" no coincidía por el artículo.
  - El patrón de "crítica" no exigía inicio de palabra ("atac" dentro
    de "contratación").
  - Si la marca o su vocera es sujeto de una gestión ("la Defensoría
    presentó…"), el Positivo no baja a Neutro por una sola mención.
  - Empates de tono dentro de la misma noticia: se deciden con la
    evidencia del texto en vez de ir siempre a Neutro.
- **Más ágil con el mismo modelo**: la consolidación solo revisa los
  grupos con evidencia (sin llamada si un subtema ya es fiel a todos), y
  la auditoría Jev corre en paralelo con el etiquetado.
- Validador: acepta nombres propios de proyecto/programa como subtema
  aunque estén en el titular. Ejemplos del prompt corregidos (enseñaban
  dos subtemas distintos para la misma noticia). Corrección del NameError
  de `km` en el volcado.
- Se quita la sección "📝 Resumen para informe" y su módulo
  `resumen_informe.py` (pedido del usuario).

## Novedades v1.27 (2026-11-02; solo Defensoría; incluye la v1.26)

- **Criterio de tono del perfil** (`criterio_custom`), pensado para un
  monitoreo de la Defensoría: Positivo si la nota destaca su labor
  (alertas, advertencias, denuncias de vulneraciones, acompañamiento,
  mediación, informes, defensa de derechos); Negativo si critica a la
  entidad, la defensora o sus funcionarios, o hay corrupción o
  investigaciones; Neutro si la mención es de paso o es un dato más. Los
  hechos graves que la Defensoría alerta no hacen Negativa la nota, y si
  otra entidad ignora su alerta la crítica es para esa entidad.
- **Alertas Tempranas: depende de la nota** (flag
  `tono_alertas_tempranas`): si la Defensoría o su vocera emite o
  advierte con una alerta, Positivo (regla determinista, salvo crítica
  dirigida a la Defensoría); si la alerta solo se cita como antecedente,
  lo decide el modelo (normalmente Neutro).
- **Subtema fijo de Alertas, más preciso** (con agrupación estricta): se
  aplica si "alerta temprana" va seguida en el titular o si el modelo ya
  identificó la alerta como hecho principal. Antes bastaba con que
  "alerta" y "temprana" aparecieran en cualquier parte del cuerpo, así
  que una nota que citaba una alerta de paso quedaba en "Alertas
  Defensoría del Pueblo".
- **Columna texto** con la misma regla que Secretaría: más de 15
  palabras, completando con oraciones literales del Resumen -
  Aclaracion (sin inventar ni repetir el titular).

## Novedades v1.28 (2026-11-02; solo Defensoría)

- **Alertas Tempranas (regla del usuario)**: si el titular, el Resumen -
  Aclaracion o el CuerpoEs dicen "alerta temprana" o "alertas tempranas"
  (frase seguida), el subtema es "Alertas Defensoría del Pueblo". Corrige
  la v1.27, que exigía la frase en el titular o en el subtema del modelo.
  Se garantiza al final, por nota, después de todos los pases que tocan el
  subtema. El tono sigue dependiendo de la nota (la Defensoría emite o
  advierte => Positivo).
- **Labor de la Defensoría => Positivo** (flag `tono_labor_positiva`): si
  la Defensoría o su vocera es sujeto de su labor (acompaña, verifica,
  advierte, denuncia vulneraciones, media, presenta un informe…) y no hay
  crítica dirigida a ella, Neutro pasa a Positivo.
- **Subtema del modelo protegido**: la guarda de fidelidad ya no cambia un
  subtema con relación con la nota por un rótulo derivado del titular que
  lo copia o empieza con verbo (caso: "Críticas por informe sobre líderes"
  -> "Cuestionan a Iris Marín por informe incompleto"). Los rótulos de otra
  noticia (sin palabras en común) se siguen rechazando.
- **Traídas de Secretaría v1.33**: un solo subtema por evento grande
  (frase distintiva repetida en al menos 3 titulares), unión de variantes
  del mismo rótulo, más verbos de gestión (designó, nombró, abrió…) y la
  columna texto con crédito al final del Resumen (toma las oraciones
  anteriores).

## Novedades v1.29 (2026-11-02; solo Defensoría)

Forma del subtema (pedido del usuario: casos reales "Días dejan cinco muertos
en el suroccidente" y "Ellos, una bebé de dos meses"): un subtema jamás lleva
comas ni puntos (salvo comas de un nombre propio de programa y cifras), jamás
empieza con pronombre y jamás es una oración "sujeto + verbo". El validador
los marca (la puerta anti-copia los reformula), el respaldo del titular/cuerpo
ya no los produce y una revisión final antes de exportar prefiere el subtema
del grupo. "Alertas Defensoría del Pueblo" no se ve afectado.
