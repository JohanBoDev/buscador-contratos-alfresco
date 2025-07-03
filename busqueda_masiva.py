import time
from pathlib import Path
from alfresco_service import buscar_archivos_generico

# Archivos
archivo_entrada = Path("combinaciones_cedula_contrato.txt")
archivo_resultado = Path("resultados_busqueda_alfresco.txt")

# Leer combinaciones originales
with archivo_entrada.open(encoding="utf-8") as f:
    combinaciones = [line.strip().split("→")[0].strip() for line in f if "→" in line]

# Leer ya procesadas (si existe)
combinaciones_ya_hechas = set()
if archivo_resultado.exists():
    with archivo_resultado.open(encoding="utf-8") as f:
        for line in f:
            if "→" in line:
                comb = line.split("→")[0].strip()
                combinaciones_ya_hechas.add(comb)

print(f"🔁 {len(combinaciones_ya_hechas)} combinaciones ya estaban procesadas.")
pendientes = [c for c in combinaciones if c not in combinaciones_ya_hechas]
print(f"🟡 Se procesarán {len(pendientes)} combinaciones nuevas.")

# Función con reintentos automáticos
def buscar_con_reintentos(terminos, reintentos=3, espera=10):
    for intento in range(reintentos):
        resultados = buscar_archivos_generico(terminos)
        if resultados is not None:
            return resultados
        print(f"⚠️ Reintento {intento + 1}/{reintentos} fallido. Esperando {espera}s...")
        time.sleep(espera)
    return None

# Procesamiento
with archivo_resultado.open("a", encoding="utf-8") as salida:
    for i, combinacion in enumerate(pendientes, 1):
        print(f"🔍 [{i}/{len(pendientes)}] Buscando: {combinacion}")
        resultados = buscar_con_reintentos([combinacion], reintentos=3, espera=10)

        if resultados:
            salida.write(f"{combinacion} → FOUND ✅\n")
        else:
            salida.write(f"{combinacion} → NOT FOUND ❌\n")

        salida.flush()  # fuerza guardado inmediato
        time.sleep(1)  # limitar velocidad

print("✅ Proceso finalizado.")
