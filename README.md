# SERVIALAFT SAS — Prototipo de Consulta Listas Vinculantes

## Instalación rápida

```bash
# 1. Crear entorno virtual (recomendado)
python -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Ejecutar la app
streamlit run app.py
```

La app abre automáticamente en http://localhost:8501

---

## Usuarios de demo

| Usuario    | Contraseña   | Rol           |
|------------|-------------|---------------|
| admin      | admin123    | Administrador |
| analista1  | sarlaft2024 | Analista      |
| consultor  | consulta01  | Consultor     |

---

## Módulos incluidos

- **OFAC / ONU** — Búsqueda individual y masiva con SimiliScore™ (fuzzy matching)
- **Policía Nacional** — Link directo + registro manual de resultado
- **Procuraduría** — Link directo + registro manual de resultado  
- **Registros consultados** — Log de todas las consultas con filtros y exportación Excel
- **Estadísticas** — Gráficas de uso, alertas y actividad por usuario

---

## Cómo probar la búsqueda fuzzy

Prueba con estos datos que están en las listas de demo:

| Tipo ID | Número     | Nombre (exacto o aproximado)         | Esperado       |
|---------|-----------|--------------------------------------|----------------|
| CC      | 12345678  | JUAN CARLOS RODRIGUEZ GOMEZ          | OFAC SDN       |
| CC      | 87654321  | MARIA FERNANDA LOPEZ HERRERA         | OFAC SDN       |
| NIT     | 900123456 | INVERSIONES DELTA SAS                | OFAC SDN       |
| CC      | 99887766  | PEDRO ANTONIO SUAREZ MORA            | PEP            |
| CC      | 12345678  | JUAN RODRIGUEZ GOMEZ *(aproximado)*  | OFAC (aprox.)  |
| CC      | 99999999  | NOMBRE INVENTADO                     | Sin resultado  |
