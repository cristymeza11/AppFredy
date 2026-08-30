import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import random
import string

st.set_page_config(page_title="Gestor Escolar SEP 2026-2027", layout="wide")

# --- CONFIGURACIÓN DE BLOQUES Y FECHAS (SEP 2026-2027) ---
BLOQUES = {
    "Bloque 1": (date(2026, 8, 31), date(2026, 11, 15)),
    "Bloque 2": (date(2026, 11, 16), date(2027, 3, 15)),
    "Bloque 3": (date(2027, 3, 16), date(2027, 6, 30))
}

DEPORTES = [
    "Fútbol", "Basquetbol", "Voleibol",
    "Atletismo - 75 mts", "Atletismo - 150 mts", "Atletismo - 300 mts", "Atletismo - 600 mts",
    "Atletismo - Relevos 4 x 4", "Atletismo - Lanzamiento de disco",
    "Atletismo - Impulso de bala", "Atletismo - Salto de longitud",
    "Escolta (7 integrantes)"
]

GRUPOS = [f"Grupo {i}" for i in range(1, 11)]

# Función auxiliar para generar un CURP ficticio
def generar_curp_ficticia():
    letras = "".join(random.choices(string.ascii_uppercase, k=4))
    numeros = "".join(random.choices(string.digits, k=6))
    genero = random.choice(['H', 'M'])
    estado = "".join(random.choices(string.ascii_uppercase, k=2))
    consonantes = "".join(random.choices(string.ascii_uppercase, k=3))
    homoclave = "".join(random.choices(string.ascii_uppercase + string.digits, k=2))
    return f"{letras}{numeros}{genero}{estado}{consonantes}{homoclave}"

# --- INICIALIZACIÓN DE DATOS ---
def inicializar_datos():
    if 'alumnos' not in st.session_state:
        # Generación automática de 10 grupos x 35 alumnos = 350 alumnos
        lista_alumnos = []
        alumno_id = 1
        for g in GRUPOS:
            for i in range(1, 36):
                genero = "Masculino" if i % 2 != 0 else "Femenino"
                lista_alumnos.append({
                    "id": alumno_id,
                    "grupo": g,
                    "nombre": f"Alumno {i:02d} ({g})",
                    "genero": genero,
                    "curp": generar_curp_ficticia() # Se agrega la CURP ficticia
                })
                alumno_id += 1
        st.session_state.alumnos = pd.DataFrame(lista_alumnos)

    if 'asistencias' not in st.session_state:
        st.session_state.asistencias = pd.DataFrame(columns=["alumno_id", "fecha", "bloque", "estado"])

    if 'evaluaciones' not in st.session_state:
        records = []
        for a_id in st.session_state.alumnos["id"]:
            for b in BLOQUES.keys():
                records.append({
                    "alumno_id": a_id,
                    "bloque": b,
                    "participacion": 10.0,
                    "conducta": 10.0,
                    "eval_formativa": 10.0
                })
        st.session_state.evaluaciones = pd.DataFrame(records)

    if 'incidencias' not in st.session_state:
        st.session_state.incidencias = pd.DataFrame(columns=["fecha", "alumno_id", "tipo", "descripcion"])

    if 'aptitudes_deportivas' not in st.session_state:
        st.session_state.aptitudes_deportivas = pd.DataFrame(columns=["alumno_id", "disciplina"])

inicializar_datos()

def obtener_dias_habiles(inicio, fin):
    cur = inicio
    dias = []
    while cur <= fin:
        if cur.weekday() < 5:  # Lunes a Viernes
            dias.append(cur)
        cur += timedelta(days=1)
    return dias

# --- INTERFAZ DE USUARIO ---
st.title("📋 Sistema Integral de Gestión Escolar SEP 2026-2027")
st.sidebar.header("Navegación y Filtros")

grupo_sel = st.sidebar.selectbox("Seleccionar Grupo", GRUPOS)
bloque_sel = st.sidebar.selectbox("Seleccionar Corte / Bloque", list(BLOQUES.keys()))

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📅 Asistencias", 
    "⭐ Participación y Conducta", 
    "📊 Eval. Formativa y Cuantitativa", 
    "🚨 Registro de Incidencias", 
    "🏆 Cédulas Deportivas y Escolta"
])

alumnos_grupo = st.session_state.alumnos[st.session_state.alumnos["grupo"] == grupo_sel]

# -------------------------------------------------------------------
# 1. ASISTENCIAS
# -------------------------------------------------------------------
with tab1:
    st.subheader(f"Registro de Asistencia - {grupo_sel} ({bloque_sel})")
    inicio_b, fin_b = BLOQUES[bloque_sel]
    dias_bloque = obtener_dias_habiles(inicio_b, fin_b)
    
    fecha_sel = st.date_input("Seleccionar Fecha (Lunes a Viernes):", value=inicio_b, min_value=inicio_b, max_value=fin_b)
    
    if fecha_sel.weekday() >= 5:
        st.warning("⚠️ La fecha seleccionada es fin de semana. Seleccione un día hábil (L-V).")
    else:
        with st.form("form_asistencia"):
            st.write(f"Pasar lista para el día **{fecha_sel.strftime('%d/%m/%Y')}**")
            asist_df = st.session_state.asistencias
            sub_asist = asist_df[(asist_df["fecha"] == fecha_sel)]
            
            estados = {}
            for _, alum in alumnos_grupo.iterrows():
                val_previo = "Presente"
                match = sub_asist[sub_asist["alumno_id"] == alum["id"]]
                if not match.empty:
                    val_previo = match.iloc[0]["estado"]
                estados[alum["id"]] = st.radio(
                    f"{alum['nombre']}", ["Presente", "Falta", "Justificada"], 
                    index=["Presente", "Falta", "Justificada"].index(val_previo), 
                    key=f"ast_{alum['id']}_{fecha_sel}", horizontal=True
                )
            
            if st.form_submit_button("Guardar Asistencias del Día"):
                st.session_state.asistencias = st.session_state.asistencias[
                    ~(st.session_state.asistencias["fecha"] == fecha_sel)
                ]
                nuevos = [{"alumno_id": aid, "fecha": fecha_sel, "bloque": bloque_sel, "estado": est} 
                          for aid, est in estados.items()]
                st.session_state.asistencias = pd.concat([st.session_state.asistencias, pd.DataFrame(nuevos)], ignore_index=True)
                st.success("Asistencias guardadas exitosamente.")

    st.markdown("---")
    st.subheader("Resumen de Asistencia por Corte")
    
    df_ast = st.session_state.asistencias[st.session_state.asistencias["bloque"] == bloque_sel]
    resumen_ast = []
    total_dias = len(dias_bloque)
    
    for _, alum in alumnos_grupo.iterrows():
        a_sub = df_ast[df_ast["alumno_id"] == alum["id"]]
        presents = len(a_sub[a_sub["estado"] == "Presente"])
        faltas = len(a_sub[a_sub["estado"] == "Falta"])
        just = len(a_sub[a_sub["estado"] == "Justificada"])
        pct = (presents / total_dias * 100) if total_dias > 0 else 100.0
        
        resumen_ast.append({
            "ID": alum["id"],
            "Nombre": alum["nombre"],
            "Asistencias Totales": presents,
            "Faltas Totales": faltas,
            "Justificadas": just,
            "Días Hábiles del Bloque": total_dias,
            "% Asistencia": round(pct, 2)
        })
    st.dataframe(pd.DataFrame(resumen_ast), use_container_width=True)

# -------------------------------------------------------------------
# 2. PARTICIPACIÓN Y CONDUCTA
# -------------------------------------------------------------------
with tab2:
    st.subheader(f"Registro de Participación y Conducta - {grupo_sel} ({bloque_sel})")
    
    eval_df = st.session_state.evaluaciones
    alumnos_ids = alumnos_grupo["id"].tolist()
    sub_eval = eval_df[(eval_df["alumno_id"].isin(alumnos_ids)) & (eval_df["bloque"] == bloque_sel)].copy()
    sub_eval = sub_eval.merge(alumnos_grupo[["id", "nombre"]], left_on="alumno_id", right_on="id")
    
    edited_eval = st.data_editor(
        sub_eval[["alumno_id", "nombre", "participacion", "conducta"]],
        column_config={
            "participacion": st.column_config.NumberColumn("Participación (0-10)", min_value=0, max_value=10, step=0.5),
            "conducta": st.column_config.NumberColumn("Conducta (0-10)", min_value=0, max_value=10, step=0.5)
        },
        disabled=["alumno_id", "nombre"],
        use_container_width=True,
        key=f"editor_part_cond_{grupo_sel}_{bloque_sel}"
    )
    
    if st.button("Guardar Participación y Conducta"):
        for _, row in edited_eval.iterrows():
            idx = st.session_state.evaluaciones[
                (st.session_state.evaluaciones["alumno_id"] == row["alumno_id"]) & 
                (st.session_state.evaluaciones["bloque"] == bloque_sel)
            ].index
            st.session_state.evaluaciones.loc[idx, "participacion"] = row["participacion"]
            st.session_state.evaluaciones.loc[idx, "conducta"] = row["conducta"]
        st.success("Registros actualizados correctamente.")

# -------------------------------------------------------------------
# 3. EVALUACIÓN FORMATIVA Y CUANTITATIVA
# -------------------------------------------------------------------
with tab3:
    st.subheader(f"Evaluación Formativa y Cuantitativa - {grupo_sel} ({bloque_sel})")
    
    st.markdown("##### Ponderación de la Calificación Cuantitativa (Suma debe ser 100%)")
    col1, col2, col3, col4 = st.columns(4)
    w_ast = col1.number_input("% Asistencia", value=20, min_value=0, max_value=100)
    w_part = col2.number_input("% Participación", value=20, min_value=0, max_value=100)
    w_cond = col3.number_input("% Conducta", value=20, min_value=0, max_value=100)
    w_form = col4.number_input("% Eval. Formativa", value=40, min_value=0, max_value=100)
    
    if w_ast + w_part + w_cond + w_form != 100:
        st.error("⚠️ La suma de las ponderaciones debe ser exactamente 100%.")
    else:
        eval_df = st.session_state.evaluaciones
        alumnos_ids = alumnos_grupo["id"].tolist()
        sub_eval = eval_df[(eval_df["alumno_id"].isin(alumnos_ids)) & (eval_df["bloque"] == bloque_sel)].copy()
        
        ast_df = st.session_state.asistencias[st.session_state.asistencias["bloque"] == bloque_sel]
        total_dias = len(obtener_dias_habiles(*BLOQUES[bloque_sel]))
        
        def calc_ast_score(aid):
            a_sub = ast_df[ast_df["alumno_id"] == aid]
            pres = len(a_sub[a_sub["estado"] == "Presente"])
            return (pres / total_dias * 10) if total_dias > 0 else 10.0

        sub_eval["asistencia_nota"] = sub_eval["alumno_id"].apply(calc_ast_score)
        sub_eval = sub_eval.merge(alumnos_grupo[["id", "nombre"]], left_on="alumno_id", right_on="id")
        
        edited_form = st.data_editor(
            sub_eval[["alumno_id", "nombre", "eval_formativa"]],
            column_config={
                "eval_formativa": st.column_config.NumberColumn("Eval. Formativa (0-10)", min_value=0, max_value=10, step=0.1)
            },
            disabled=["alumno_id", "nombre"],
            use_container_width=True,
            key=f"editor_formativa_{grupo_sel}_{bloque_sel}"
        )
        
        if st.button("Guardar Evaluación Formativa"):
            for _, row in edited_form.iterrows():
                idx = st.session_state.evaluaciones[
                    (st.session_state.evaluaciones["alumno_id"] == row["alumno_id"]) & 
                    (st.session_state.evaluaciones["bloque"] == bloque_sel)
                ].index
                st.session_state.evaluaciones.loc[idx, "eval_formativa"] = row["eval_formativa"]
            st.success("Evaluación Formativa actualizada.")

        sub_eval["eval_formativa"] = edited_form["eval_formativa"]
        sub_eval["Calificación Final"] = (
            (sub_eval["asistencia_nota"] * (w_ast / 100)) +
            (sub_eval["participacion"] * (w_part / 100)) +
            (sub_eval["conducta"] * (w_cond / 100)) +
            (sub_eval["eval_formativa"] * (w_form / 100))
        ).round(2)
        
        st.markdown("#### Sabana de Calificaciones Finales")
        st.dataframe(
            sub_eval[["alumno_id", "nombre", "asistencia_nota", "participacion", "conducta", "eval_formativa", "Calificación Final"]].rename(
                columns={
                    "asistencia_nota": "Nota Asistencia",
                    "participacion": "Nota Participación",
                    "conducta": "Nota Conducta",
                    "eval_formativa": "Nota Formativa"
                }
            ),
            use_container_width=True
        )

# -------------------------------------------------------------------
# 4. REGISTRO DE INCIDENCIAS
# -------------------------------------------------------------------
with tab4:
    st.subheader(f"Registro y Reporte Individual de Incidencias - {grupo_sel}")
    
    with st.form("form_incidencia"):
        alumno_inc = st.selectbox("Seleccionar Alumno", alumnos_grupo["nombre"].tolist())
        fecha_inc = st.date_input("Fecha de Incidencia", value=date.today())
        tipo_inc = st.selectbox("Tipo de Incidencia", ["Leve (Llamada de atención)", "Moderada (Reporte a Dirección)", "Grave (Citatorio a Padres)"])
        desc_inc = st.text_area("Descripción detallada del suceso")
        
        if st.form_submit_button("Registrar Incidencia"):
            aid = alumnos_grupo[alumnos_grupo["nombre"] == alumno_inc]["id"].values[0]
            nueva_inc = {"fecha": fecha_inc, "alumno_id": aid, "tipo": tipo_inc, "descripcion": desc_inc}
            st.session_state.incidencias = pd.concat([st.session_state.incidencias, pd.DataFrame([nueva_inc])], ignore_index=True)
            st.success("Incidencia registrada.")

    st.markdown("---")
    st.subheader("Generador de Reporte Individual")
    
    alumno_rep = st.selectbox("Seleccionar Alumno para Expediente", alumnos_grupo["nombre"].tolist(), key="rep_sel")
    aid_rep = alumnos_grupo[alumnos_grupo["nombre"] == alumno_rep]["id"].values[0]
    
    rep_df = st.session_state.incidencias[st.session_state.incidencias["alumno_id"] == aid_rep]
    
    st.write(f"**Expediente Disciplinario de:** {alumno_rep}")
    if rep_df.empty:
        st.info("El alumno no cuenta con incidencias registradas.")
    else:
        st.dataframe(rep_df[["fecha", "tipo", "descripcion"]], use_container_width=True)
        
        reporte_texto = f"REPORTE DE INCIDENCIAS INDIVIDUAL\nSEP 2026-2027\n"
        reporte_texto += f"Alumno: {alumno_rep} | Grupo: {grupo_sel}\n"
        reporte_texto += f"Total Incidencias: {len(rep_df)}\n"
        reporte_texto += "="*40 + "\n"
        for _, r in rep_df.iterrows():
            reporte_texto += f"Fecha: {r['fecha']} | Tipo: {r['tipo']}\nDescripción: {r['descripcion']}\n" + "-"*40 + "\n"
        
        st.download_button("Descargar Reporte Individual (.txt)", data=reporte_texto, file_name=f"Reporte_{alumno_rep}.txt", mime="text/plain")

# -------------------------------------------------------------------
# 5. CÉDULAS DEPORTIVAS Y ESCOLTA
# -------------------------------------------------------------------
with tab5:
    st.subheader("Asignación de Aptitudes Deportivas y Escolta")
    
    col_dep1, col_dep2 = st.columns(2)
    alumno_dep = col_dep1.selectbox("Seleccionar Alumno", alumnos_grupo["nombre"].tolist(), key="dep_alum")
    aid_dep = alumnos_grupo[alumnos_grupo["nombre"] == alumno_dep]["id"].values[0]
    
    deportes_seleccionados = col_dep2.multiselect("Marcar Disciplinas / Aptitudes", DEPORTES)
    
    if st.button("Guardar Aptitudes Deportivas"):
        st.session_state.aptitudes_deportivas = st.session_state.aptitudes_deportivas[
            ~(st.session_state.aptitudes_deportivas["alumno_id"] == aid_dep)
        ]
        nuevas_apt = [{"alumno_id": aid_dep, "disciplina": d} for d in deportes_seleccionados]
        st.session_state.aptitudes_deportivas = pd.concat([st.session_state.aptitudes_deportivas, pd.DataFrame(nuevas_apt)], ignore_index=True)
        st.success("Aptitudes actualizadas.")

    st.markdown("---")
    st.subheader("Generación de Cédulas Oficiales")
    
    col_c1, col_c2 = st.columns(2)
    dep_sel = col_c1.selectbox("Seleccionar Disciplina", DEPORTES)
    rama_sel = col_c2.selectbox("Seleccionar Rama", ["Masculino", "Femenino"])
    
    # Filtrar por aptitud y género global (todos los grupos)
    apt_df = st.session_state.aptitudes_deportivas[st.session_state.aptitudes_deportivas["disciplina"] == dep_sel]
    ids_con_apt = apt_df["alumno_id"].tolist()
    
    # ¡AQUÍ SE INCLUYE LA CURP EN LA SELECCIÓN DE COLUMNAS DE LA CÉDULA!
    cedula_df = st.session_state.alumnos[
        (st.session_state.alumnos["id"].isin(ids_con_apt)) & 
        (st.session_state.alumnos["genero"] == rama_sel)
    ][["id", "grupo", "nombre", "curp", "genero"]] 
    
    st.markdown(f"### CÉDULA DE INSCRIPCIÓN: {dep_sel.upper()} ({rama_sel.upper()})")
    
    if "Escolta" in dep_sel and len(cedula_df) > 7:
        st.warning(f"⚠️ La escolta contempla 7 elementos. Actualmente hay {len(cedula_df)} registrados.")
    
    st.dataframe(cedula_df, use_container_width=True)
    
    csv_cedula = cedula_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        f"📥 Descargar Cédula con CURP ({dep_sel} - {rama_sel})",
        data=csv_cedula,
        file_name=f"Cedula_{dep_sel}_{rama_sel}.csv",
        mime="text/csv"
    )