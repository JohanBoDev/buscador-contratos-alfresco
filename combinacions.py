import pandas as pd

# Ruta al archivo
ruta_excel = r"C:\Users\Johan Bohorquez\Downloads\SIC_FACTURAS_UNE_VERSION_FINAL.xlsx"

# Leer el archivo Excel
df = pd.read_excel(ruta_excel)

# Verificar el nombre de la columna del nombre
columna_nombre = 'NAME'
if 'NAME_COMPLETO' in df.columns:
    columna_nombre = 'NAME_COMPLETO'

# Eliminar filas vacías en columnas clave
df = df.dropna(subset=['CEDULA', 'CONTRATO'])

# Crear columna de combinación
df['COMBINACION'] = df['CEDULA'].astype(str) + '-' + df['CONTRATO'].astype(str)

# Ruta del archivo de salida
ruta_salida = "combinaciones_cedula_contrato.txt"

# Abrir archivo y escribir resultados
with open(ruta_salida, "w", encoding="utf-8") as f:
    for _, fila in df.iterrows():
        linea = f"{fila['COMBINACION']} → {fila[columna_nombre]}"
        print(linea)
        f.write(linea + "\n")

print(f"\n✅ Archivo guardado como: {ruta_salida}")
